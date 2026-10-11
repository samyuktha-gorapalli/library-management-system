from flask import Flask, render_template, request, redirect, url_for, flash

import catalogue
import members
import circulation
import reservations
import reports

app = Flask(__name__)
app.secret_key = "replace-with-a-real-secret-key"


@app.route("/")
def index():
    return render_template(
        "index.html",
        available=catalogue.available_titles(),
        overdue=circulation.overdue_copies(),
    )


# ---------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------
@app.route("/catalogue", methods=["GET", "POST"])
def catalogue_page():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "book":
            catalogue.add_book(request.form["title"], request.form["category"])
            flash("Book added.")
        elif form_type == "volume":
            catalogue.add_volume(
                request.form["book_id"],
                request.form["isbn"],
                request.form["edition_no"],
                request.form["publication_year"],
            )
            flash("Volume added.")
        elif form_type == "copy":
            ok, msg = catalogue.add_copy(request.form["isbn"], request.form["accession_no"])
            flash(msg, "message" if ok else "error")
        elif form_type == "update_book":
            ok, msg = catalogue.update_book(
                request.form["book_id"], request.form["title"], request.form["category"]
            )
            flash(msg, "message" if ok else "error")
        elif form_type == "delete_book":
            ok, msg = catalogue.delete_book(request.form["book_id"])
            flash(msg, "message" if ok else "error")
        elif form_type == "update_volume":
            ok, msg = catalogue.update_volume(
                request.form["isbn"],
                request.form["new_isbn"],
                request.form["edition_no"],
                request.form["publication_year"],
            )
            flash(msg, "message" if ok else "error")
        elif form_type == "delete_volume":
            ok, msg = catalogue.delete_volume(request.form["isbn"])
            flash(msg, "message" if ok else "error")
        elif form_type == "update_copy":
            ok, msg = catalogue.update_copy(
                request.form["accession_no"], request.form["new_accession_no"], request.form["status"]
            )
            flash(msg, "message" if ok else "error")
        elif form_type == "delete_copy":
            ok, msg = catalogue.delete_copy(request.form["accession_no"])
            flash(msg, "message" if ok else "error")
        return redirect(url_for("catalogue_page"))

    keyword = request.args.get("q", "")
    results = catalogue.search_catalogue(keyword) if keyword else []
    return render_template("catalogue.html", results=results, keyword=keyword)


# ---------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------
@app.route("/members", methods=["GET", "POST"])
def members_page():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "update":
            ok, msg = members.update_member(
                request.form["member_id"], request.form["full_name"], request.form["email"]
            )
            flash(msg, "message" if ok else "error")
        elif form_type == "delete":
            ok, msg = members.delete_member(request.form["member_id"])
            flash(msg, "message" if ok else "error")
        else:
            members.register_member(request.form["full_name"], request.form["email"])
            flash("Member registered.")
        return redirect(url_for("members_page"))
    return render_template("members.html", members=members.list_members())


@app.route("/members/<int:member_id>/history")
def member_history_page(member_id):
    history = members.get_member_history(member_id)
    return render_template("member_history.html", history=history, member_id=member_id)


# ---------------------------------------------------------------------
# Circulation
# ---------------------------------------------------------------------
@app.route("/circulation", methods=["GET", "POST"])
def circulation_page():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "issue":
            ok, msg = circulation.issue_copy(request.form["copy_id"], request.form["member_id"])
        else:
            ok, msg = circulation.return_copy(request.form["borrow_id"])
        flash(msg, "message" if ok else "error")
        return redirect(url_for("circulation_page"))

    return render_template(
        "circulation.html",
        active_loans=circulation.active_loans(),
        overdue=circulation.overdue_copies(),
    )


# ---------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------
@app.route("/reservations", methods=["GET", "POST"])
def reservations_page():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "update":
            ok, msg = reservations.update_reservation(
                request.form["isbn"],
                request.form["queue_position"],
                request.form["new_queue_position"],
                request.form["status"],
            )
        elif form_type == "delete":
            ok, msg = reservations.delete_reservation(
                request.form["isbn"], request.form["queue_position"]
            )
        else:
            ok, msg = reservations.create_reservation(
                request.form["accession_no"], request.form["member_id"]
            )
        flash(msg, "message" if ok else "error")
        return redirect(url_for("reservations_page"))
    return render_template("reservations.html", reservations=reservations.all_reservations())


@app.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
def cancel_reservation_route(reservation_id):
    reservations.cancel_reservation(reservation_id)
    flash("Reservation cancelled.")
    return redirect(url_for("reservations_page"))


# ---------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------
@app.route("/reports")
def reports_page():
    return render_template(
        "reports.html",
        popular=reports.popular_books(),
        fines=reports.fine_collection(),
    )


@app.route("/fines/<int:fine_id>/pay", methods=["POST"])
def pay_fine(fine_id):
    reports.mark_fine_paid(fine_id)
    flash("Fine marked as paid.")
    return redirect(url_for("reports_page"))


if __name__ == "__main__":
    app.run(debug=True)
