# Library System — Flask Front-End

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Edit db.py and set your MySQL password (and host/user if different).

3. Make sure the `librarydb` schema is already created (run the schema
   and sample-data SQL scripts first) and that the required views
   (v_available_titles, v_overdue_copies, v_member_history) exist.

4. Run the app:
   python app.py

5. Open http://127.0.0.1:5000 in your browser.

## Pages

- Dashboard  — available titles + overdue copies at a glance
- Catalogue  — search titles, add books/volumes/copies
- Members    — register members, view individual borrowing history
- Circulation — issue/return copies, see active loans and overdue items
- Reservations — join/view a title's reservation queue
- Reports    — popular books, fine collection by member
