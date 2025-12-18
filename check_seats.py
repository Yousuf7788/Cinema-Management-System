from database import Database
import sys

db = Database()
if not db.connect("localhost,1433", "CinemaDB", "sa", "reallyStrongPwd123"):
    print("Connection failed")
    sys.exit(1)

cursor = db.connection.cursor()
cursor.execute("""
    SELECT h.hall_name, s.row_letter, COUNT(*) as seat_count
    FROM Seat s
    JOIN Movie_Hall h ON s.hall_id = h.hall_id
    GROUP BY h.hall_name, s.row_letter
    ORDER BY h.hall_name, s.row_letter
""")

rows = cursor.fetchall()
if not rows:
    print("No seats found!")
else:
    print("--- Seat Distribution ---")
    for r in rows:
        print(f"Hall: {r[0]}, Row: {r[1]}, Count: {r[2]}")
