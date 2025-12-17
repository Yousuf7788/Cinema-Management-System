-- 1. Customer Table
CREATE TABLE Customer (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20)
);

-- 2. Employee Table
CREATE TABLE Employee (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    position VARCHAR(50),
    hire_date DATE
);

-- 3. Movie Table
CREATE TABLE Movie (
    movie_id INT IDENTITY(1,1) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    genre VARCHAR(100),
    duration_minutes INT,
    rating VARCHAR(10)
);

-- 4. Movie_Details Table (1-to-1 with Movie)
CREATE TABLE Movie_Details (
    movie_id INT PRIMARY KEY,
    director VARCHAR(255),
    cast TEXT,
    synopsis TEXT,
    release_date DATE,
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id) ON DELETE CASCADE
);

-- 5. Movie_Hall Table
CREATE TABLE Movie_Hall (
    hall_id INT IDENTITY(1,1) PRIMARY KEY,
    hall_name VARCHAR(50) NOT NULL,
    capacity INT
);

-- 6. Screening Table (Connects Movie and Movie_Hall, represents a showtime)
CREATE TABLE Screening (
    screening_id INT IDENTITY(1,1) PRIMARY KEY,
    movie_id INT NOT NULL,
    hall_id INT NOT NULL,
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id),
    FOREIGN KEY (hall_id) REFERENCES Movie_Hall(hall_id)
);

-- 7. Seat Table
CREATE TABLE Seat (
    seat_id INT IDENTITY(1,1) PRIMARY KEY,
    hall_id INT NOT NULL,
    row_letter CHAR(1) NOT NULL,
    seat_number INT NOT NULL,
    seat_type VARCHAR(20) DEFAULT 'Standard',
    FOREIGN KEY (hall_id) REFERENCES Movie_Hall(hall_id),
    CONSTRAINT unique_seat UNIQUE (hall_id, row_letter, seat_number)
);

-- 8. Booking Table (Core transaction table)
CREATE TABLE Booking (
    booking_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT NOT NULL,
    screening_id INT NOT NULL,
    booking_date DATETIME2 DEFAULT GETDATE(),
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (screening_id) REFERENCES Screening(screening_id)
);

-- 9. Booking_Seat Table (Junction table for Many-to-Many between Booking and Seat)
CREATE TABLE Booking_Seat (
    booking_id INT,
    seat_id INT,
    PRIMARY KEY (booking_id, seat_id),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES Seat(seat_id)
);

-- 10. Payment Table
CREATE TABLE Payment (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL,
    payment_date DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id)
);

-- 11. Refund Table
CREATE TABLE Refund (
    refund_id INT IDENTITY(1,1) PRIMARY KEY,
    payment_id INT NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    refund_reason TEXT,
    refund_date DATETIME2 DEFAULT GETDATE(),
    processed_by_employee_id INT,
    FOREIGN KEY (payment_id) REFERENCES Payment(payment_id),
    FOREIGN KEY (processed_by_employee_id) REFERENCES Employee(employee_id)
);

-- 12. Users Table
CREATE TABLE Users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    user_type VARCHAR(20) CHECK (user_type IN ('customer', 'employee', 'manager')) NOT NULL,
    customer_id INT NULL,
    employee_id INT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
);

-- Add price to screening table
ALTER TABLE Screening ADD ticket_price DECIMAL(10,2) NOT NULL DEFAULT 0;

-- Add status to booking table
-- Find the default constraint name
SELECT 
    dc.name AS constraint_name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID('Booking') 
AND c.name = 'status';

-- 2. Drop the existing constraint (replace with actual name)
ALTER TABLE Booking DROP CONSTRAINT DF__Booking__status__4959E263;

-- 3. Add the new default value
ALTER TABLE Booking ADD DEFAULT 'pending' FOR status;

-- Update existing bookings to 'confirmed' if they have payments
UPDATE Booking SET status = 'confirmed' WHERE booking_id IN (SELECT booking_id FROM Payment);

-- Add refund status
ALTER TABLE Refund ADD status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'));

-- Step 3: Add the new default value
ALTER TABLE Payment ADD DEFAULT 'pending' FOR payment_status;

-- 1. Populate Customer Table
INSERT INTO Customer (first_name, last_name, email, phone_number) VALUES
('John', 'Smith', 'john.smith@email.com', '555-0101'),
('Sarah', 'Johnson', 'sarah.j@email.com', '555-0102'),
('Michael', 'Brown', 'mike.brown@email.com', '555-0103'),
('Emily', 'Davis', 'emily.davis@email.com', '555-0104'),
('David', 'Wilson', 'david.wilson@email.com', '555-0105'),
('Jennifer', 'Miller', 'jennifer.m@email.com', '555-0106'),
('Robert', 'Taylor', 'robert.t@email.com', '555-0107'),
('Lisa', 'Anderson', 'lisa.a@email.com', '555-0108');

-- 2. Populate Employee Table
INSERT INTO Employee (first_name, last_name, position, hire_date) VALUES
('James', 'Clark', 'Manager', '2020-01-15'),
('Maria', 'Garcia', 'Cashier', '2021-03-20'),
('Thomas', 'Lee', 'Projectionist', '2020-11-10'),
('Karen', 'White', 'Usher', '2022-05-01'),
('Steven', 'Harris', 'Cashier', '2023-01-10');

-- 3. Populate Movie Table
INSERT INTO Movie (title, genre, duration_minutes, rating) VALUES
('The Last Adventure', 'Action', 138, 'PG-13'),
('Moonlight Dreams', 'Drama', 125, 'PG'),
('Galaxy Warriors', 'Sci-Fi', 152, 'PG-13'),
('Lost in Time', 'Thriller', 115, 'R'),
('Summer Romance', 'Romance', 108, 'PG-13'),
('The Hidden Truth', 'Mystery', 132, 'R');

-- 4. Populate Movie_Details Table
INSERT INTO Movie_Details (movie_id, director, cast, synopsis, release_date) VALUES
(1, 'Christopher Nolan', 'Tom Cruise, Emma Stone, Robert Downey Jr.', 'A group of explorers travel through a wormhole in search of a new home for humanity.', '2023-05-15'),
(2, 'Sofia Coppola', 'Meryl Streep, Timoth�e Chalamet', 'A coming-of-age story about a young artist finding her voice in New York City.', '2023-03-22'),
(3, 'James Cameron', 'Chris Hemsworth, Zendaya, Idris Elba', 'Space marines battle alien forces to save humanity from extinction.', '2023-07-10'),
(4, 'David Fincher', 'Jake Gyllenhaal, Viola Davis', 'A detective uncovers a conspiracy that threatens to destroy the city.', '2023-09-05'),
(5, 'Nancy Meyers', 'Ryan Gosling, Rachel McAdams', 'Two strangers meet on a summer vacation and discover true love.', '2023-06-18'),
(6, 'Denis Villeneuve', 'Amy Adams, Jeremy Renner', 'A journalist investigates a series of mysterious disappearances in a small town.', '2023-08-12');

-- 5. Populate Movie_Hall Table
INSERT INTO Movie_Hall (hall_name, capacity) VALUES
('Hall A - IMAX', 250),
('Hall B - Standard', 180),
('Hall C - Premium', 120),
('Hall D - 3D', 200),
('Hall E - VIP', 80);

-- 6. Populate Seat Table (adding seats for Hall 1 as example)
INSERT INTO Seat (hall_id, row_letter, seat_number, seat_type) VALUES
-- Hall 1 (IMAX) - 10 rows, 25 seats per row
(1, 'A', 1, 'Standard'), (1, 'A', 2, 'Standard'), (1, 'A', 3, 'Standard'), (1, 'A', 4, 'Standard'), (1, 'A', 5, 'Standard'),
(1, 'B', 1, 'Standard'), (1, 'B', 2, 'Standard'), (1, 'B', 3, 'Standard'), (1, 'B', 4, 'Standard'), (1, 'B', 5, 'Standard'),
(1, 'C', 1, 'Premium'), (1, 'C', 2, 'Premium'), (1, 'C', 3, 'Premium'), (1, 'C', 4, 'Premium'), (1, 'C', 5, 'Premium'),
(1, 'D', 1, 'Premium'), (1, 'D', 2, 'Premium'), (1, 'D', 3, 'Premium'), (1, 'D', 4, 'Premium'), (1, 'D', 5, 'Premium');

-- 7. Populate Screening Table
INSERT INTO Screening (movie_id, hall_id, start_time, end_time) VALUES
(1, 1, '2024-01-15 14:00:00', '2024-01-15 16:18:00'),
(1, 1, '2024-01-15 18:30:00', '2024-01-15 20:48:00'),
(2, 2, '2024-01-15 15:00:00', '2024-01-15 17:05:00'),
(3, 3, '2024-01-15 16:00:00', '2024-01-15 18:32:00'),
(4, 4, '2024-01-15 19:00:00', '2024-01-15 20:55:00'),
(5, 2, '2024-01-15 20:00:00', '2024-01-15 21:48:00'),
(6, 3, '2024-01-15 21:00:00', '2024-01-15 23:12:00');

-- 8. Populate Booking Table
INSERT INTO Booking (customer_id, screening_id, booking_date, total_amount) VALUES
(1, 1, '2024-01-14 10:30:00', 45.00),
(2, 1, '2024-01-14 11:15:00', 30.00),
(3, 2, '2024-01-14 12:00:00', 60.00),
(4, 3, '2024-01-14 14:20:00', 25.00),
(5, 4, '2024-01-14 15:45:00', 40.00),
(6, 5, '2024-01-14 16:30:00', 35.00),
(7, 6, '2024-01-14 17:10:00', 50.00);

-- 9. Populate Booking_Seat Table
INSERT INTO Booking_Seat (booking_id, seat_id) VALUES
(1, 1), (1, 2), (1, 3),  -- Customer 1 booked 3 seats
(2, 4), (2, 5),          -- Customer 2 booked 2 seats
(3, 6), (3, 7), (3, 8), (3, 9),  -- Customer 3 booked 4 seats
(4, 10),                 -- Customer 4 booked 1 seat
(5, 11), (5, 12),        -- Customer 5 booked 2 seats
(6, 13), (6, 14),        -- Customer 6 booked 2 seats
(7, 15), (7, 16), (7, 17); -- Customer 7 booked 3 seats

-- 10. Populate Payment Table
INSERT INTO Payment (booking_id, amount, payment_method, payment_status, payment_date) VALUES
(1, 45.00, 'Credit Card', 'Completed', '2024-01-14 10:32:00'),
(2, 30.00, 'Debit Card', 'Completed', '2024-01-14 11:17:00'),
(3, 60.00, 'Credit Card', 'Completed', '2024-01-14 12:02:00'),
(4, 25.00, 'Cash', 'Completed', '2024-01-14 14:22:00'),
(5, 40.00, 'Credit Card', 'Completed', '2024-01-14 15:47:00'),
(6, 35.00, 'Mobile Payment', 'Completed', '2024-01-14 16:32:00'),
(7, 50.00, 'Credit Card', 'Completed', '2024-01-14 17:12:00');

-- 11. Populate Refund Table
INSERT INTO Refund (payment_id, refund_amount, refund_reason, refund_date, processed_by_employee_id) VALUES
(4, 25.00, 'Customer emergency', '2024-01-14 16:00:00', 1);

-- Create user accounts
INSERT INTO Users (username, password_hash, email, user_type, customer_id, employee_id) VALUES
-- Customers (password: password123)
('johndoe', '$2b$12$LQv3c1yqBWVHxkd0L8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6a', 'john.doe@email.com', 'customer', 1, NULL),
('janesmith', '$2b$12$LQv3c1yqBWVHxkd0L8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6a', 'jane.smith@email.com', 'customer', 2, NULL),
('mikejohnson', '$2b$12$LQv3c1yqBWVHxkd0L8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6a', 'mike.johnson@email.com', 'customer', 3, NULL),
-- Employees (password: employee123)
('alicebrown', '$2b$12$8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6aLQv3c1yqBWVHxkd0L8', 'alice@cinema.com', 'manager', NULL, 1),
('bobwilson', '$2b$12$8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6aLQv3c1yqBWVHxkd0L8', 'bob@cinema.com', 'employee', NULL, 2),
('caroldavis', '$2b$12$8k7OeY2JzW7cQ6VZ5bXfV8nMk9JtR3dS6aLQv3c1yqBWVHxkd0L8', 'carol@cinema.com', 'employee', NULL, 3);

-- 1. Check all customers and their bookings
SELECT 
    c.first_name + ' ' + c.last_name AS customer_name,
    m.title AS movie_title,
    b.booking_date,
    b.total_amount
FROM Customer c
JOIN Booking b ON c.customer_id = b.customer_id
JOIN Screening s ON b.screening_id = s.screening_id
JOIN Movie m ON s.movie_id = m.movie_id;

-- 2. Check movie screenings with hall information
SELECT 
    m.title,
    mh.hall_name,
    s.start_time,
    s.end_time
FROM Screening s
JOIN Movie m ON s.movie_id = m.movie_id
JOIN Movie_Hall mh ON s.hall_id = mh.hall_id;

-- 3. Check payments and refunds
SELECT 
    c.first_name + ' ' + c.last_name AS customer_name,
    p.amount,
    p.payment_method,
    p.payment_status,
    COALESCE(r.refund_amount, 0) AS refund_amount
FROM Payment p
JOIN Booking b ON p.booking_id = b.booking_id
JOIN Customer c ON b.customer_id = c.customer_id
LEFT JOIN Refund r ON p.payment_id = r.payment_id;

-- 4. Check seat bookings for a specific screening
SELECT 
    s.row_letter + CAST(s.seat_number AS VARCHAR) AS seat_number,
    s.seat_type,
    c.first_name + ' ' + c.last_name AS booked_by
FROM Booking_Seat bs
JOIN Seat s ON bs.seat_id = s.seat_id
JOIN Booking b ON bs.booking_id = b.booking_id
JOIN Customer c ON b.customer_id = c.customer_id
WHERE b.screening_id = 1;

-- 5. Check employee who processed refunds
SELECT 
    c.customer_id,
    c.first_name + ' ' + c.last_name AS customer_name,
    r.refund_amount,
    r.refund_reason,
    e.first_name + ' ' + e.last_name AS processed_by
FROM Customer c
JOIN Booking b ON c.customer_id = b.customer_id
JOIN Payment p ON b.booking_id = p.booking_id
JOIN Refund r ON p.payment_id = r.payment_id
JOIN Employee e ON r.processed_by_employee_id = e.employee_id;


-- Update all password_hash values to hash of (username + '123')
UPDATE Users 
SET password_hash = username + '123';

SELECT 
    'Customer' AS table_name, COUNT(*) AS record_count FROM Customer
UNION ALL SELECT 'Employee', COUNT(*) FROM Employee
UNION ALL SELECT 'Movie', COUNT(*) FROM Movie
UNION ALL SELECT 'Movie_Details', COUNT(*) FROM Movie_Details
UNION ALL SELECT 'Movie_Hall', COUNT(*) FROM Movie_Hall
UNION ALL SELECT 'Seat', COUNT(*) FROM Seat
UNION ALL SELECT 'Screening', COUNT(*) FROM Screening
UNION ALL SELECT 'Booking', COUNT(*) FROM Booking
UNION ALL SELECT 'Booking_Seat', COUNT(*) FROM Booking_Seat
UNION ALL SELECT 'Payment', COUNT(*) FROM Payment
UNION ALL SELECT 'Refund', COUNT(*) FROM Refund


DELETE FROM Users WHERE user_id = 8;

SELECT * FROM Screening;    