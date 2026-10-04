from db import get_connection


def popular_books():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT b.book_id, b.title, COUNT(*) AS times_borrowed
        FROM borrowed_by bb
        JOIN copy c ON c.copy_id = bb.copy_id
        JOIN volume v ON v.volume_id = c.volume_id
        JOIN book b ON b.book_id = v.book_id
        GROUP BY b.book_id, b.title
        ORDER BY times_borrowed DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fine_collection():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT m.member_id, m.full_name,
               SUM(f.amount) AS total_fined,
               SUM(CASE WHEN f.paid_status THEN f.amount ELSE 0 END) AS paid,
               SUM(CASE WHEN NOT f.paid_status THEN f.amount ELSE 0 END) AS unpaid
        FROM fines f
        JOIN borrowed_by bb ON bb.borrow_id = f.borrow_id
        JOIN member m ON m.member_id = bb.member_id
        GROUP BY m.member_id, m.full_name
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def mark_fine_paid(fine_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE fines SET paid_status = TRUE WHERE fine_id = %s", (fine_id,))
    conn.commit()
    cur.close()
    conn.close()
