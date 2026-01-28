# Cinema Management System 🎬

A comprehensive desktop-based application for managing cinema operations, featuring role-based access for Customers, Employees, and Managers. Built with **Python** and **PyQt6**.

## 🚀 Features

### 👤 Customer
- **Account Management**: Sign up, login, and manage your personal profile.
- **Browse Movies**: View available movies, synopsis, cast, and ratings.
- **Seat Selection**: Interactive seating map to choose your preferred seats.
- **Booking**: Secure ticket booking and payment simulation.
- **History**: View booking history and request refunds.

### 👔 Employee
- **Operations**: Manage daily cinema operations.
- **Refund Processing**: Review and approve or reject refund requests.
- **Screening View**: Check status of halls and movie timings.

### 💼 Manager
- **Content Management**: Add new movies and update movie details.
- **Screening Management**: Schedule screenings for different halls.
- **Staff Oversight**: Manage employee access and roles.
- **System Overview**: Full access to all system features.

## 🛠️ Tech Stack

- **Language**: Python 3.x
- **GUI Framework**: PyQt6
- **Database**: Microsoft SQL Server
- **Driver**: ODBC Driver 18 for SQL Server (`pyodbc`)
- **Security**: `bcrypt` for password hashing and verification.

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

1.  **Python 3.8+**
2.  **Microsoft SQL Server** (Express, Developer, or Standard edition)
3.  **ODBC Driver 18 for SQL Server** (Usually comes with SSMS or can be downloaded separately)

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Yousuf7788/Cinema-Management-System.git
cd Cinema-Management-System
```

### 2. Install Dependencies
Install the required Python packages using pip:
```bash
pip install PyQt6 pyodbc bcrypt
```

### 3. Database Setup
1.  Open **SQL Server Management Studio (SSMS)** or Azure Data Studio.
2.  Connect to your local SQL Server instance.
3.  Open the `db.sql` file included in this project.
4.  Execute the script to create the `CinemaDB` database and all necessary tables.

### 4. Configure Connection
1.  Open `main.py` in your code editor.
2.  Locate the `init_database` method (approx. line 21).
3.  Update the connection variables to match your SQL Server credentials:

    ```python
    # In main.py
    host = "localhost"         # Use your server name/address
    port = 1433
    server = f"{host},{port}"
    database = "CinemaDB"
    username = "sa"            # Your SQL Server username
    password = "YourStrongPassword"  # Your SQL Server password
    ```

    > **Note**: If you are using Windows Authentication (Trusted Connection), you may need to modify the connection string construction in `database.py` or simply update the parameters to use a specific user if mixed auth is enabled.

## ▶️ Usage

Run the main application script to start the specific module:

```bash
python main.py
```

- **Login**: Use the `Login` screen to access your account.
- **Sign Up**: New customers can create an account via the `Sign Up` button.
- **Dashboard**: Upon login, you will be redirected to the appropriate dashboard based on your user role.

## 📂 Project Structure

- `main.py`: Application entry point and UI initialization.
- `database.py`: Database connection and CRUD operations.
- `auth_system.py`: Login and Signup UI logic.
- `*_dashboard.py`: Dashboard interfaces for different roles.
- `*_tab.py`: Detailed logic for specific tabs (Movies, Booking, etc.).
- `db.sql`: SQL script for database schema creation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
