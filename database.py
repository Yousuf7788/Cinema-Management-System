import pyodbc
import logging
from typing import Optional, List, Tuple, Dict, Any
import bcrypt

class Database:
    def __init__(self):
        self.connection = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self, server: str, database: str, username: str = None, password: str = None) -> bool:
        try:
            if username and password:
                # SQL Authentication (recommended for macOS/Docker)
                connection_string = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"UID={username};"
                    f"PWD={password};"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=yes;"
                )
            else:
                # Windows Authentication DOES NOT WORK on macOS,
                # but kept here for compatibility — it will fail silently.
                connection_string = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={database};"
                    f"Trusted_Connection=yes;"
                    f"Encrypt=yes;"
                    f"TrustServerCertificate=yes;"
                )

            self.connection = pyodbc.connect(connection_string, timeout=5)
            print("Database connected successfully")
            return True

        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    
    def hash_password(self, password: str) -> str:
        """
        NOTE: This no longer hashes. It simply returns the raw password string.
        Storing plaintext passwords is insecure.
        """
        return password

    def verify_password(self, password: str, stored: str) -> bool:
        """
        Compare password directly to stored plaintext value.
        """
        try:
            # Defensive: ensure types are str
            return str(password) == str(stored)
        except Exception as e:
            self.logger.error(f"verify_password error: {e}")
            return False

    
    def create_user(self, username: str, password: str, email: str, user_type: str, 
                   first_name: str, last_name: str, phone: str = None) -> bool:
        try:
            cursor = self.connection.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT user_id FROM Users WHERE username = ? OR email = ?", username, email)
            if cursor.fetchone():
                return False
            
            # Insert into Customer table
            cursor.execute(
                "INSERT INTO Customer (first_name, last_name, email, phone_number) OUTPUT INSERTED.customer_id VALUES (?, ?, ?, ?)",
                first_name, last_name, email, phone
            )
            customer_id = cursor.fetchone()[0]
            
            # Insert into Users table
# Insert into Users table (store plaintext password)
            plain_password = self.hash_password(password)  # now returns plaintext
            cursor.execute(
                "INSERT INTO Users (username, password_hash, email, user_type, customer_id) VALUES (?, ?, ?, ?, ?)",
                username, plain_password, email, user_type, customer_id
            )

            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            self.connection.rollback()
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user by username and plaintext password.
        Returns a dict on success, or None on failure.
        """
        try:
            print(f"DEBUG: authenticate_user called with username={username!r}")
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT u.user_id, u.username, u.password_hash, u.user_type, u.customer_id, u.employee_id,
                        c.first_name, c.last_name, c.email, c.phone_number,
                        e.first_name as emp_first_name, e.last_name as emp_last_name, e.position
                FROM Users u 
                LEFT JOIN Customer c ON u.customer_id = c.customer_id
                LEFT JOIN Employee e ON u.employee_id = e.employee_id
                WHERE LOWER(u.username) = LOWER(?)""",
                username
            )
            user = cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Authentication SQL error: {e}")
            print("DEBUG: Authentication SQL error:", e)
            return None

        print("DEBUG: authenticate_user - fetched row:", repr(user), "type:", type(user))
        if not user:
            print("DEBUG: authenticate_user - no user found for:", username)
            return None

        # get stored value (works for pyodbc row or tuple)
        try:
            stored = getattr(user, 'password_hash', None)
            if stored is None:
                stored = user[2]  # fallback index
        except Exception as e:
            print("DEBUG: could not extract stored password:", e)
            return None

        # normalize stored to string and compare plaintext
        try:
            stored_str = str(stored).strip()
        except Exception as e:
            print("DEBUG: error normalizing stored password:", e)
            return None

        pw_ok = False
        try:
            pw_ok = self.verify_password(password, stored_str)
        except Exception as e:
            print("DEBUG: verify_password raised:", e)
            pw_ok = False

        print("DEBUG: password verification result for", username, ":", pw_ok)
        if not pw_ok:
            return None

        # Build user_data dict (defensive)
        def get(attr, idx):
            try:
                return getattr(user, attr, None) or (user[idx] if len(user) > idx else None)
            except Exception:
                return (user[idx] if len(user) > idx else None)

        user_id = get('user_id', 0)
        uname = get('username', 1)
        utype_raw = get('user_type', 3)
        user_type = utype_raw.strip().lower() if isinstance(utype_raw, str) else None
        customer_id = get('customer_id', 4)
        employee_id = get('employee_id', 5)
        first_name = get('first_name', 6) or get('emp_first_name', 10)
        last_name = get('last_name', 7) or get('emp_last_name', 11)
        email = get('email', 8)
        phone = get('phone_number', 9)
        position = get('position', 12) if len(user) > 12 else None

        user_data = {
            'user_id': user_id,
            'username': uname,
            'user_type': user_type,
            'customer_id': customer_id,
            'employee_id': employee_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'position': position
        }

        print("DEBUG: authenticate_user returning user_data:", user_data)
        return user_data

    
    def get_movies(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT m.movie_id, m.title, m.genre, m.duration_minutes, m.rating,
                          md.director, md.cast, md.synopsis, md.release_date
                   FROM Movie m
                   JOIN Movie_Details md ON m.movie_id = md.movie_id"""
            )
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching movies: {e}")
            return []
    
    def get_screenings(self, movie_id: int = None) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT s.screening_id, s.movie_id, s.hall_id, s.start_time, s.end_time, s.ticket_price,
                       m.title, mh.hall_name, mh.capacity,
                       (SELECT COUNT(*) FROM Seat WHERE hall_id = s.hall_id) - 
                       (SELECT COUNT(*) FROM Booking_Seat bs 
                        JOIN Booking b ON bs.booking_id = b.booking_id 
                        WHERE b.screening_id = s.screening_id AND b.status = 'confirmed') as available_seats
                FROM Screening s
                JOIN Movie m ON s.movie_id = m.movie_id
                JOIN Movie_Hall mh ON s.hall_id = mh.hall_id
            """
            if movie_id:
                query += " WHERE s.movie_id = ?"
                cursor.execute(query, movie_id)
            else:
                cursor.execute(query)
            
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching screenings: {e}")
            return []
    
    def get_available_seats(self, screening_id: int) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT s.seat_id, s.row_letter, s.seat_number, s.seat_type
                FROM Seat s
                JOIN Screening sc ON s.hall_id = sc.hall_id
                WHERE sc.screening_id = ?
                AND s.seat_id NOT IN (
                    SELECT bs.seat_id 
                    FROM Booking_Seat bs
                    JOIN Booking b ON bs.booking_id = b.booking_id
                    WHERE b.screening_id = ? AND b.status = 'confirmed'
                )
            """, screening_id, screening_id)
            
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching available seats: {e}")
            return []
    
    def create_booking(self, customer_id: int, screening_id: int, seat_ids: List[int], total_amount: float) -> Optional[int]:
        try:
            cursor = self.connection.cursor()
            
            # Create booking
            cursor.execute(
                "INSERT INTO Booking (customer_id, screening_id, total_amount, status) OUTPUT INSERTED.booking_id VALUES (?, ?, ?, 'confirmed')",
                customer_id, screening_id, total_amount
            )
            booking_id = cursor.fetchone()[0]
            
            # Link seats to booking
            for seat_id in seat_ids:
                cursor.execute(
                    "INSERT INTO Booking_Seat (booking_id, seat_id) VALUES (?, ?)",
                    booking_id, seat_id
                )
            
            # Create payment
            cursor.execute(
                "INSERT INTO Payment (booking_id, amount, payment_method, payment_status) VALUES (?, ?, 'Credit Card', 'completed')",
                booking_id, total_amount
            )
            
            self.connection.commit()
            return booking_id
            
        except Exception as e:
            self.logger.error(f"Error creating booking: {e}")
            self.connection.rollback()
            return None
        
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Retrieve ALL bookings across all customers (for managers/employees)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    b.booking_id,
                    b.booking_date,
                    b.total_amount,
                    b.status,
                    c.first_name AS customer_first_name,
                    c.last_name AS customer_last_name,
                    c.email AS customer_email,
                    m.title AS movie_title,
                    s.start_time,
                    mh.hall_name,
                    STRING_AGG(CONCAT(seat.row_letter, seat.seat_number), ', ') AS seats
                FROM Booking b
                JOIN Customer c ON b.customer_id = c.customer_id
                JOIN Screening s ON b.screening_id = s.screening_id
                JOIN Movie m ON s.movie_id = m.movie_id
                JOIN Movie_Hall mh ON s.hall_id = mh.hall_id
                JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
                JOIN Seat seat ON bs.seat_id = seat.seat_id
                GROUP BY 
                    b.booking_id, 
                    b.booking_date, 
                    b.total_amount, 
                    b.status,
                    c.first_name,
                    c.last_name,
                    c.email,
                    m.title,
                    s.start_time,
                    mh.hall_name
                ORDER BY b.booking_date DESC;
            """)

            # Convert each row into a dict using column names
            return [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]

        except Exception as e:
            self.logger.error(f"Error fetching all bookings: {e}")
            return []

    
    def get_user_bookings(self, customer_id: int) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT b.booking_id, b.booking_date, b.total_amount, b.status,
                       m.title, s.start_time, mh.hall_name,
                       STRING_AGG(CONCAT(seat.row_letter, seat.seat_number), ', ') as seats
                FROM Booking b
                JOIN Screening s ON b.screening_id = s.screening_id
                JOIN Movie m ON s.movie_id = m.movie_id
                JOIN Movie_Hall mh ON s.hall_id = mh.hall_id
                JOIN Booking_Seat bs ON b.booking_id = bs.booking_id
                JOIN Seat seat ON bs.seat_id = seat.seat_id
                WHERE b.customer_id = ?
                GROUP BY b.booking_id, b.booking_date, b.total_amount, b.status, m.title, s.start_time, mh.hall_name
                ORDER BY b.booking_date DESC
            """, customer_id)
            
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching user bookings: {e}")
            return []
    
    def request_refund(self, booking_id: int, reason: str) -> bool:
        try:
            cursor = self.connection.cursor()
            
            # Get payment ID for the booking
            cursor.execute("SELECT payment_id FROM Payment WHERE booking_id = ?", booking_id)
            payment = cursor.fetchone()
            if not payment:
                return False
            
            # Create refund request
            cursor.execute(
                "INSERT INTO Refund (payment_id, refund_amount, refund_reason, status) VALUES (?, ?, ?, 'pending')",
                payment[0], 0, reason  # Amount will be updated by employee
            )
            
            # Update booking status
            cursor.execute("UPDATE Booking SET status = 'refunded' WHERE booking_id = ?", booking_id)
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating refund request: {e}")
            self.connection.rollback()
            return False
    
    def get_pending_refunds(self) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT r.refund_id, r.refund_amount, r.refund_reason, r.refund_date, r.status,
                       b.booking_id, b.total_amount, c.first_name, c.last_name, m.title
                FROM Refund r
                JOIN Payment p ON r.payment_id = p.payment_id
                JOIN Booking b ON p.booking_id = b.booking_id
                JOIN Customer c ON b.customer_id = c.customer_id
                JOIN Screening s ON b.screening_id = s.screening_id
                JOIN Movie m ON s.movie_id = m.movie_id
                WHERE r.status = 'pending'
            """)
            
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error fetching pending refunds: {e}")
            return []
    
    def get_halls(self) -> List[Dict[str, Any]]:
        """Return a list of all movie halls with hall_id, hall_name, and capacity."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    hall_id,
                    hall_name,
                    capacity
                FROM Movie_Hall
                ORDER BY hall_id
            """)
            
            rows = cursor.fetchall()
            return [
                dict(zip([column[0] for column in cursor.description], row))
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f"Error fetching halls: {e}")
            return []

    def process_refund(self, refund_id: int, employee_id: int, status: str, refund_amount: float = None) -> bool:
        try:
            cursor = self.connection.cursor()
            
            if status == 'approved' and refund_amount:
                cursor.execute(
                    "UPDATE Refund SET status = ?, processed_by_employee_id = ?, refund_amount = ? WHERE refund_id = ?",
                    status, employee_id, refund_amount, refund_id
                )
            else:
                cursor.execute(
                    "UPDATE Refund SET status = ?, processed_by_employee_id = ? WHERE refund_id = ?",
                    status, employee_id, refund_id
                )
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing refund: {e}")
            self.connection.rollback()
            return False
    
    def add_movie(self, title: str, genre: str, duration: int, rating: str, 
                  director: str, cast: str, synopsis: str, release_date: str) -> bool:
        try:
            cursor = self.connection.cursor()
            
            # Insert into Movie table
            cursor.execute(
                "INSERT INTO Movie (title, genre, duration_minutes, rating) OUTPUT INSERTED.movie_id VALUES (?, ?, ?, ?)",
                title, genre, duration, rating
            )
            movie_id = cursor.fetchone()[0]
            
            # Insert into Movie_Details table
            cursor.execute(
                "INSERT INTO Movie_Details (movie_id, director, cast, synopsis, release_date) VALUES (?, ?, ?, ?, ?)",
                movie_id, director, cast, synopsis, release_date
            )
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding movie: {e}")
            self.connection.rollback()
            return False
    
    def add_screening(self, movie_id: int, hall_id: int, start_time: str, end_time: str, ticket_price: float) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO Screening (movie_id, hall_id, start_time, end_time, ticket_price) VALUES (?, ?, ?, ?, ?)",
                movie_id, hall_id, start_time, end_time, ticket_price
            )
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding screening: {e}")
            self.connection.rollback()
            return False
    
    def get_customer_name(self, customer_id: int) -> str:
        """Get customer name by ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT first_name + ' ' + last_name FROM Customer WHERE customer_id = ?",
                customer_id
            )
            result = cursor.fetchone()
            return result[0] if result else "Unknown Customer"
        except Exception as e:
            self.logger.error(f"Error getting customer name: {e}")
            return "Unknown Customer"
        
    def init_database(self):
        server = "localhost"  # Change to your SQL Server instance
        database = "CinemaDB"  # Your database name
        
        # Option 1: Windows Authentication (recommended)
        if self.db.connect(server, database):
            return True
        
        # Option 2: SQL Server Authentication
        username = "sa"  # Your SQL Server username
        password = "YourPassword123"  # Your SQL Server password
        if self.db.connect(server, database, username, password):
            return True
        
        self.show_db_error()
        return False