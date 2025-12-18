from database import Database
import sys

db = Database()
if not db.connect("localhost,1433", "CinemaDB", "sa", "reallyStrongPwd123"):
    print("Connection failed")
    sys.exit(1)

# Pick a screening ID that we know exists (e.g., 1)
screening_id = 1
seats = db.get_screening_seat_status(screening_id)

print(f"Fetched {len(seats)} seats for Screening {screening_id}")
row_counts = {}
for s in seats:
    r = s['row_letter']
    row_counts[r] = row_counts.get(r, 0) + 1

print("Row counts:", row_counts)
