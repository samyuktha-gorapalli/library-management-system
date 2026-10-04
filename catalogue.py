from db import get_connection


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


def add_copy(volume_id, accession_no):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO copy (volume_id, accession_no) VALUES (%s, %s)",
        (volume_id, accession_no),
    )
    conn.commit()
    copy_id = cur.lastrowid
    cur.close()
    conn.close()
    return copy_id


def search_catalogue(keyword):
    """Search books by title (partial match) and show their volumes/copies."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT b.book_id, b.title, b.category, v.volume_id, v.isbn,
               v.edition_no, v.publication_year, c.copy_id, c.accession_no, c.status
        FROM book b
        JOIN volume v ON v.book_id = b.book_id
        JOIN copy c ON c.volume_id = v.volume_id
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
