import pyodbc
from datetime import datetime, timedelta

def get_conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=localhost,1433;'
        'DATABASE=CinemaDB;'
        'UID=sa;'
        'PWD=reallyStrongPwd123;'
        'Encrypt=no;'
        'TrustServerCertificate=yes;'
    )

def reset_and_populate():
    conn = get_conn()
    cursor = conn.cursor()
    print("Connected to DB.")

    # --- 1. CLEANUP ---
    print("\n--- Cleaning up tables ---")
    tables = [
        'Refund', 'Payment', 'Booking_Seat', 'Booking', 'Users',
        'Screening', 'Seat', 'Movie_Details', 'Movie', 'Movie_Hall', 
        'Employee', 'Customer'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Deleted data from {table}")
            try:
                cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
            except:
                pass 
        except Exception as e:
            print(f"Error deleting {table}: {e}")

    # --- 2. POPULATE ---
    print("\n--- Populating tables ---")

    # A. EMPLOYEES (Identity column exists)
    print("Inserting Employees...")
    employees = [
        ('Manager', 'User', 'Manager', '2023-01-01'),
        ('Staff', 'User', 'Cashier', '2023-02-01')
    ]
    emp_ids = []
    for emp in employees:
        cursor.execute(
            "INSERT INTO Employee (first_name, last_name, position, hire_date) VALUES (?, ?, ?, ?)", 
            emp
        )
        # Assuming DB supports SCOPE_IDENTITY, otherwise query max
        cursor.execute("SELECT @@IDENTITY")
        emp_ids.append(cursor.fetchone()[0])
    
    # Employee Users
    print("Creating Employee Users...")
    emp_users = [
        ('manager', 'admin123', 'manager@cinema.com', 'manager', emp_ids[0]),
        ('staff', 'staff123', 'staff@cinema.com', 'employee', emp_ids[1])
    ]
    for u in emp_users:
        cursor.execute(
            "INSERT INTO Users (username, password_hash, email, user_type, employee_id) VALUES (?, ?, ?, ?, ?)",
            u
        )

    # B. CUSTOMERS (No Identity - Uses User ID)
    print("Inserting Customers & Users...")
    cust_data = [
        # (username, pass, email, first, last, phone)
        ('john_doe', 'pass123', 'john@test.com', 'John', 'Doe', '12345678901'),
        ('jane_smith', 'pass123', 'jane@test.com', 'Jane', 'Smith', '12345678902'),
        ('bob_wilson', 'pass123', 'bob@test.com', 'Bob', 'Wilson', None),
        ('alice_brown', 'pass123', 'alice@test.com', 'Alice', 'Brown', '12345678903')
    ]
    
    cust_ids = []
    for c in cust_data:
        # 1. Insert User first to get ID
        username, pwd, email, fname, lname, phone = c
        cursor.execute(
            "INSERT INTO Users (username, password_hash, email, user_type) VALUES (?, ?, ?, ?)",
            (username, pwd, email, 'customer')
        )
        cursor.execute("SELECT @@IDENTITY")
        user_id = cursor.fetchone()[0]
        cust_ids.append(user_id)
        
        # 2. Insert Customer (using user_id as customer_id)
        # Phone is passed as string, driver/DB handles cast to bigint if needed, or NULL
        cursor.execute(
            "INSERT INTO Customer (customer_id, first_name, last_name, phone_number) VALUES (?, ?, ?, ?)",
            (user_id, fname, lname, phone)
        )
        
        # 3. Update User to link customer_id
        cursor.execute("UPDATE Users SET customer_id = ? WHERE user_id = ?", (user_id, user_id))

    # C. MOVIE HALLS
    print("Inserting Halls...")
    halls = [
        ('Hall 1 - IMAX', 50),
        ('Hall 2 - Standard', 40),
        ('Hall 3 - VIP', 20)
    ]
    hids = []
    for h in halls:
        cursor.execute("INSERT INTO Movie_Hall (hall_name, capacity) VALUES (?, ?)", h)
        cursor.execute("SELECT @@IDENTITY")
        hids.append(cursor.fetchone()[0])

    # D. MOVIES & DETAILS
    print("Inserting Movies...")
    movies = [
        ('Inception', 'Sci-Fi', 148, 'PG-13'),
        ('The Dark Knight', 'Action', 152, 'PG-13'),
        ('Toy Story', 'Animation', 81, 'G')
    ]
    mids = []
    for m in movies:
        cursor.execute("INSERT INTO Movie (title, genre, duration_minutes, rating) VALUES (?, ?, ?, ?)", m)
        cursor.execute("SELECT @@IDENTITY")
        mid = cursor.fetchone()[0]
        mids.append(mid)
        # Details
        cursor.execute(
            "INSERT INTO Movie_Details (movie_id, director, cast, synopsis, release_date) VALUES (?, ?, ?, ?, ?)",
            mid, "Director Name", "Actor 1, Actor 2", f"Synopsis for {m[0]}", '2010-01-01'
        )

    # E. SEATS
    print("Inserting Seats...")
    cursor.execute("SELECT hall_id, capacity FROM Movie_Hall")
    hall_rows = cursor.fetchall()  # (hall_id, capacity)
    
    for hid, cap in hall_rows:
        rows = ['A', 'B', 'C', 'D', 'E']
        count = 0
        for r in rows:
            for n in range(1, 11): # 10 seats per row
                if count >= cap: break
                seat_type = 'Premium' if r == 'A' else 'Standard'
                cursor.execute(
                    "INSERT INTO Seat (hall_id, row_letter, seat_number, seat_type) VALUES (?, ?, ?, ?)",
                    (hid, r, n, seat_type)
                )
                count += 1

    # F. SCREENINGS
    print("Inserting Screenings...")
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    screenings_data = [
        (mids[0], hids[0], tomorrow, tomorrow + timedelta(hours=2), 15.00), # IMAX
        (mids[1], hids[1], tomorrow, tomorrow + timedelta(hours=2), 10.00), # Standard
        (mids[2], hids[2], tomorrow, tomorrow + timedelta(hours=2), 25.00)  # VIP
    ]
    sids = []
    for s in screenings_data:
        cursor.execute(
            "INSERT INTO Screening (movie_id, hall_id, start_time, end_time, ticket_price) VALUES (?, ?, ?, ?, ?)",
            s
        )
        cursor.execute("SELECT @@IDENTITY")
        sids.append(cursor.fetchone()[0])

    # G. BOOKINGS & PAYMENTS
    print("Inserting Bookings...")
    # 1. Confirmed Booking (Paid) - Customer 0
    cursor.execute("INSERT INTO Booking (customer_id, screening_id, total_amount, status) VALUES (?, ?, ?, ?)", 
                   cust_ids[0], sids[0], 30.00, 'confirmed')
    cursor.execute("SELECT @@IDENTITY")
    bid1 = cursor.fetchone()[0]
    cursor.execute("INSERT INTO Payment (booking_id, amount, payment_method, payment_status) VALUES (?, ?, ?, ?)",
                   bid1, 30.00, 'Credit Card', 'Completed')

    # 2. Pending Booking (No Payment) - Customer 1
    cursor.execute("INSERT INTO Booking (customer_id, screening_id, total_amount, status) VALUES (?, ?, ?, ?)",
                   cust_ids[1], sids[1], 20.00, 'pending')
    
    # 3. Refunded Booking - Customer 0
    cursor.execute("INSERT INTO Booking (customer_id, screening_id, total_amount, status) VALUES (?, ?, ?, ?)",
                   cust_ids[0], sids[2], 50.00, 'confirmed')
    cursor.execute("SELECT @@IDENTITY")
    bid3 = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Payment (booking_id, amount, payment_method, payment_status) VALUES (?, ?, ?, ?)",
                   bid3, 50.00, 'Cash', 'Completed')
    cursor.execute("SELECT @@IDENTITY")
    pid3 = cursor.fetchone()[0]
    
    # Refund Request
    cursor.execute("INSERT INTO Refund (payment_id, refund_amount, refund_reason, status) VALUES (?, ?, ?, ?)",
                   pid3, 50.00, 'Sick', 'pending')

    conn.commit()
    print("\n--- Database Reset Complete ---")
    
    # Validation
    print("Final Counts:")
    for t in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f" {t}: {count}")

if __name__ == "__main__":
    try:
        reset_and_populate()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
