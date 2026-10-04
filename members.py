from db import get_connection


def register_member(full_name, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO member (full_name, email) VALUES (%s, %s)",
        (full_name, email),
    )
    conn.commit()
    member_id = cur.lastrowid
    cur.close()
    conn.close()
    return member_id


def list_members():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM member ORDER BY full_name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_member_history(member_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM v_member_history WHERE member_id = %s ORDER BY issue_date DESC",
        (member_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
