from datetime import date
from mysql.connector import Error
from db import get_connection
from crud import update_row, delete_row


def create_reservation(accession_no, member_id):
    """Add a member to the back of the reservation queue for the volume
    (edition) that the given copy belongs to."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT volume_id FROM copy WHERE accession_no = %s", (accession_no,))
        row = cur.fetchone()
        if row is None:
            return False, f"No copy {accession_no} found."
        volume_id = row[0]
        cur.execute("SELECT 1 FROM member WHERE member_id = %s", (member_id,))
        if cur.fetchone() is None:
            return False, f"No member #{member_id} found."
        cur.execute(
            "SELECT COALESCE(MAX(queue_position), 0) FROM reservation WHERE volume_id = %s",
            (volume_id,),
        )
        next_position = cur.fetchone()[0] + 1
        cur.execute(
            "INSERT INTO reservation (volume_id, member_id, reserved_date, queue_position) "
            "VALUES (%s, %s, %s, %s)",
            (volume_id, member_id, date.today(), next_position),
        )
        conn.commit()
        return True, f"Reserved — position {next_position} in queue."
    except Error as e:
        conn.rollback()
        return False, f"Could not create reservation: {e}"
    finally:
        cur.close()
        conn.close()


def queue_for_volume(volume_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT r.reservation_id, r.queue_position, r.status, r.reserved_date,
               m.full_name, m.member_id
        FROM reservation r
        JOIN member m ON m.member_id = r.member_id
        WHERE r.volume_id = %s
        ORDER BY r.queue_position
        """,
        (volume_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def all_reservations():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT r.reservation_id, b.title, v.isbn, m.full_name,
               r.queue_position, r.status, r.reserved_date
        FROM reservation r
        JOIN volume v ON v.volume_id = r.volume_id
        JOIN book b ON b.book_id = v.book_id
        JOIN member m ON m.member_id = r.member_id
        ORDER BY b.title, r.queue_position
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def cancel_reservation(reservation_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reservation SET status = 'cancelled' WHERE reservation_id = %s",
        (reservation_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def _volume_id_for_isbn(isbn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT volume_id FROM volume WHERE isbn = %s", (isbn,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def update_reservation(isbn, queue_position, new_queue_position, status):
    volume_id = _volume_id_for_isbn(isbn)
    if volume_id is None:
        return False, f"No volume with ISBN {isbn} found."
    return update_row(
        "reservation",
        {"volume_id": volume_id, "queue_position": queue_position},
        {"queue_position": new_queue_position, "status": status},
        f"reservation at queue position {queue_position} for ISBN {isbn}",
    )


def delete_reservation(isbn, queue_position):
    volume_id = _volume_id_for_isbn(isbn)
    if volume_id is None:
        return False, f"No volume with ISBN {isbn} found."
    return delete_row(
        "reservation",
        {"volume_id": volume_id, "queue_position": queue_position},
        f"reservation at queue position {queue_position} for ISBN {isbn}",
    )
