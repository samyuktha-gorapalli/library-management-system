from datetime import date, timedelta
from mysql.connector import Error
from db import get_connection

FINE_RATE_PER_DAY = 0.50   # currency units per day late
DEFAULT_LOAN_DAYS = 14


def issue_copy(copy_id, member_id):
    """Issue a copy to a member. Returns (success, message)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        issue_date = date.today()
        due_date = issue_date + timedelta(days=DEFAULT_LOAN_DAYS)
        cur.execute(
            "INSERT INTO borrowed_by (copy_id, member_id, issue_date, due_date) "
            "VALUES (%s, %s, %s, %s)",
            (copy_id, member_id, issue_date, due_date),
        )
        cur.execute("UPDATE copy SET status = 'issued' WHERE copy_id = %s", (copy_id,))
        conn.commit()
        return True, f"Copy issued. Due back {due_date}."
    except Error as e:
        conn.rollback()
        # The trg_one_active_issue trigger raises SQLSTATE 45000 for a double issue
        if "already has an active issue" in str(e):
            return False, "This copy is already checked out."
        return False, f"Could not issue copy: {e}"
    finally:
        cur.close()
        conn.close()


def return_copy(borrow_id):
    """Return a copy, calculate any fine, and free the copy up."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM borrowed_by WHERE borrow_id = %s", (borrow_id,))
        loan = cur.fetchone()
        if loan is None:
            return False, "No such loan record."
        if loan["return_date"] is not None:
            return False, "This copy was already returned."

        return_date = date.today()
        cur.execute(
            "UPDATE borrowed_by SET return_date = %s WHERE borrow_id = %s",
            (return_date, borrow_id),
        )
        cur.execute(
            "UPDATE copy SET status = 'available' WHERE copy_id = %s",
            (loan["copy_id"],),
        )

        days_late = (return_date - loan["due_date"]).days
        message = "Returned on time."
        if days_late > 0:
            amount = days_late * FINE_RATE_PER_DAY
            cur.execute(
                "INSERT INTO fines (borrow_id, amount, assessed_date, paid_status) "
                "VALUES (%s, %s, %s, FALSE)",
                (borrow_id, amount, return_date),
            )
            message = f"Returned {days_late} day(s) late. Fine of {amount:.2f} recorded."

        conn.commit()
        return True, message
    except Error as e:
        conn.rollback()
        return False, f"Could not process return: {e}"
    finally:
        cur.close()
        conn.close()


def active_loans():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT bb.borrow_id, b.title, c.accession_no, m.full_name, bb.issue_date, bb.due_date
        FROM borrowed_by bb
        JOIN copy c ON c.copy_id = bb.copy_id
        JOIN volume v ON v.volume_id = c.volume_id
        JOIN book b ON b.book_id = v.book_id
        JOIN member m ON m.member_id = bb.member_id
        WHERE bb.return_date IS NULL
        ORDER BY bb.due_date
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def overdue_copies():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM v_overdue_copies ORDER BY days_overdue DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
