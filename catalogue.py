from mysql.connector import Error, errorcode
from db import get_connection
from crud import update_row, delete_with_loan_history


def add_book(title, category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO book (title, category) VALUES (%s, %s)", (title, category))
    conn.commit()
    book_id = cur.lastrowid
    cur.close()
    conn.close()
    return book_id


def add_volume(book_id, isbn, edition_no, publication_year):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO volume (book_id, isbn, edition_no, publication_year) VALUES (%s, %s, %s, %s)",
        (book_id, isbn, edition_no, publication_year),
    )
    conn.commit()
    volume_id = cur.lastrowid
    cur.close()
    conn.close()
    return volume_id


def add_copy(isbn, accession_no):
    """Add a copy of the volume (edition) with the given ISBN. Returns (success, message)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT volume_id FROM volume WHERE isbn = %s", (isbn,))
        row = cur.fetchone()
        if row is None:
            return False, f"No volume with ISBN {isbn} found."
        cur.execute(
            "INSERT INTO copy (volume_id, accession_no) VALUES (%s, %s)",
            (row[0], accession_no),
        )
        conn.commit()
        return True, f"Copy {accession_no} added."
    except Error as e:
        conn.rollback()
        if e.errno == errorcode.ER_DUP_ENTRY:
            return False, f"Could not add copy: Accession No. {accession_no} is already in use."
        return False, f"Could not add copy: {e.msg}"
    finally:
        cur.close()
        conn.close()


def update_book(book_id, title, category):
    return update_row(
        "book",
        {"book_id": book_id},
        {"title": title, "category": category},
        f"book #{book_id}",
    )


def delete_book(book_id):
    return delete_with_loan_history(
        "book",
        "book_id",
        book_id,
        "SELECT c.copy_id FROM copy c JOIN volume v ON v.volume_id = c.volume_id WHERE v.book_id = %s",
        f"book #{book_id}",
    )


def update_volume(isbn, new_isbn, edition_no, publication_year):
    return update_row(
        "volume",
        {"isbn": isbn},
        {"isbn": new_isbn, "edition_no": edition_no, "publication_year": publication_year},
        f"volume with ISBN {isbn}",
    )


def delete_volume(isbn):
    return delete_with_loan_history(
        "volume",
        "isbn",
        isbn,
        "SELECT c.copy_id FROM copy c JOIN volume v ON v.volume_id = c.volume_id WHERE v.isbn = %s",
        f"volume with ISBN {isbn}",
    )


def update_copy(accession_no, new_accession_no, status):
    return update_row(
        "copy",
        {"accession_no": accession_no},
        {"accession_no": new_accession_no, "status": status},
        f"copy {accession_no}",
    )


def delete_copy(accession_no):
    return delete_with_loan_history(
        "copy",
        "accession_no",
        accession_no,
        "SELECT copy_id FROM copy WHERE accession_no = %s",
        f"copy {accession_no}",
    )


def search_catalogue(keyword):
    """Search books by title (partial match) and show their volumes/copies."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT b.book_id, b.title, b.category, v.volume_id, v.isbn,
               v.edition_no, v.publication_year, c.copy_id, c.accession_no, c.status
        FROM book b
        LEFT JOIN volume v ON v.book_id = b.book_id
        LEFT JOIN copy c ON c.volume_id = v.volume_id
        WHERE b.title LIKE %s
        ORDER BY b.title, v.edition_no
        """,
        (f"%{keyword}%",),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def available_titles():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM v_available_titles")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
