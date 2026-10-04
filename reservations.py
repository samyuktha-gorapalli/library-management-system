from datetime import date
from mysql.connector import Error
from db import get_connection


def create_reservation(volume_id, member_id):
    """Add a member to the back of the reservation queue for a volume."""
    conn = get_connection()
    cur = conn.cursor()
    try:
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
        SELECT r.reservation_id, b.title, v.volume_id, m.full_name,
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
