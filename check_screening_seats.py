from database import Database
import sys

db = Database()
if not db.connect("localhost,1433", "CinemaDB", "sa", "reallyStrongPwd123"):
    print("Connection failed")
    sys.exit(1)

cursor = db.connection.cursor()
cursor.execute("""
    SELECT s.screening_id, s.movie_id, mh.hall_name, COUNT(seat.seat_id) as total_seats
    FROM Screening s
    JOIN Movie_Hall mh ON s.hall_id = mh.hall_id
    LEFT JOIN Seat seat ON mh.hall_id = seat.hall_id
    GROUP BY s.screening_id, s.movie_id, mh.hall_name
""")

rows = cursor.fetchall()
print("--- Screenings and Seat Counts ---")
for r in rows:
    print(f"Screening {r[0]} (Movie {r[1]}) in {r[2]}: {r[3]} seats")
