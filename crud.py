from mysql.connector import Error, errorcode
from db import get_connection

# Table and column names passed to these helpers always come from our own code,
# never from the form, so building them into the SQL string is safe. Every value
# the user typed is still sent as a %s parameter.


def _where_clause(where):
    return " AND ".join(f"{col} = %s" for col in where)


def _error_message(action, label, e):
    if e.errno == errorcode.ER_DUP_ENTRY:
        return f"Could not {action} {label}: that value is already in use (must be unique)."
    if e.errno == errorcode.WARN_DATA_TRUNCATED:
        return f"Could not {action} {label}: that is not an allowed value ({e.msg})."
    return f"Could not {action} {label}: {e.msg}"


def update_row(table, where, fields, label):
    """UPDATE only the fields that were filled in; blank fields keep their current value.
    Returns (success, message)."""
    changes = {col: val.strip() for col, val in fields.items() if val and val.strip()}
    if not changes:
        return False, "Nothing to update — fill in at least one field to change."

    where_sql = _where_clause(where)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT 1 FROM {table} WHERE {where_sql}", tuple(where.values()))
        if cur.fetchone() is None:
            return False, f"No {label} found."

        set_sql = ", ".join(f"{col} = %s" for col in changes)
        cur.execute(
            f"UPDATE {table} SET {set_sql} WHERE {where_sql}",
            tuple(changes.values()) + tuple(where.values()),
        )
        conn.commit()
        # The row exists (checked above), so 0 affected rows means MySQL found
        # nothing to change: the new values equal the current ones.
        if cur.rowcount == 0:
            return False, f"No changes made to {label}: the new values are the same as the current ones."
        return True, f"Updated {label}."
    except Error as e:
        conn.rollback()
        return False, _error_message("update", label, e)
    finally:
        cur.close()
        conn.close()


def delete_row(table, where, label, in_use_reason=None):
    """DELETE one row. If a RESTRICT foreign key still points at it, the delete is
    blocked and in_use_reason is shown. Returns (success, message)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM {table} WHERE {_where_clause(where)}", tuple(where.values()))
        if cur.rowcount == 0:
            conn.rollback()
            return False, f"No {label} found."
        conn.commit()
        return True, f"Deleted {label}."
    except Error as e:
        conn.rollback()
        if e.errno == errorcode.ER_ROW_IS_REFERENCED_2 and in_use_reason:
            return False, f"Cannot delete {label}: {in_use_reason}"
        return False, _error_message("delete", label, e)
    finally:
        cur.close()
        conn.close()


def delete_with_loan_history(table, key_col, key_val, copies_sql, label):
    """DELETE a book/volume/copy together with the returned-loan history of its copies.
    copies_sql is a SELECT of the affected copy_ids, taking key_val as its one parameter.
    Refused if any of those copies is currently issued. Returns (success, message)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT 1 FROM {table} WHERE {key_col} = %s", (key_val,))
        if cur.fetchone() is None:
            return False, f"No {label} found."

        cur.execute(
            "SELECT c.accession_no FROM borrowed_by bb JOIN copy c ON c.copy_id = bb.copy_id "
            f"WHERE bb.return_date IS NULL AND bb.copy_id IN ({copies_sql})",
            (key_val,),
        )
        issued = [row[0] for row in cur.fetchall()]
        if issued:
            return False, f"Cannot delete {label}: copy {', '.join(issued)} is currently issued."

        # Past loans go first because borrowed_by's RESTRICT key would block the
        # delete; their fines are removed by fines' ON DELETE CASCADE. Volumes,
        # copies and reservations below the row then go by their own CASCADE keys.
        cur.execute(f"DELETE FROM borrowed_by WHERE copy_id IN ({copies_sql})", (key_val,))
        loans_removed = cur.rowcount
        cur.execute(f"DELETE FROM {table} WHERE {key_col} = %s", (key_val,))
        conn.commit()
        if loans_removed:
            return True, f"Deleted {label} and {loans_removed} past loan record(s)."
        return True, f"Deleted {label}."
    except Error as e:
        conn.rollback()
        return False, _error_message("delete", label, e)
    finally:
        cur.close()
        conn.close()
