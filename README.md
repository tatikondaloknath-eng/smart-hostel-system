 Smart Hostel Accommodation System

A full-stack web application designed to manage hostel room allocation, booking, and waitlisting efficiently. This system provides separate portals for students and administrators, ensuring smooth hostel operations.

 Features
 Student Portal
Secure login system
View available rooms and beds visually
Book hostel rooms
Join waiting list if rooms are full
Online payment simulation
Change password functionality
🛠️ Admin Portal
Admin authentication
Add and manage student records
View room occupancy (floor-wise & course-wise)
Edit student details (room, bed, password)
Lock bookings
Monitor waiting list
 Core Concepts Used
Arrays / Lists → Storing student and room records
Allocation Algorithm → Assigning available beds
Queue Data Structure → Managing waiting list
Searching Techniques → Fast student lookup
 Tech Stack
Frontend
HTML, CSS, JavaScript
Dynamic UI with DOM manipulation

 UI code reference:

Backend
Python with Flask
REST API (/api/sync)
Database
MySQL (Aiven Cloud)
Accessed using PyMySQL

 Backend code reference:

Deployment
Gunicorn (Production server)
 Project Structure
project/
│── app.py                # Flask backend
│── templates/
│    └── hostel.html     # Frontend UI
│── requirements.txt
│── README.md
 Installation & Setup
1️ Clone Repository
git clone https://github.com/your-username/hostel-system.git
cd hostel-system
2️ Install Dependencies
pip install flask pymysql cryptography gunicorn
3️ Set Environment Variable (Optional)
export DATABASE_URL="your_mysql_connection_string"
4️ Run Application
Development Mode
python app.py
Production Mode
gunicorn app:app
 API Endpoints
GET /api/sync
Fetch all student and queue data
POST /api/sync
Update student records and waitlist
 Database Schema
Students Table
id, name, course, pass
booked, room, bed
bookingTime
isWaitlisted, waitRoom, waitBed
adminLocked
Queue Table
Stores waiting list in JSON format
 Default Admin Credentials
ID: ADMINAMRITA2000
Password: 0987654321

 Change these before deploying in production.

 How It Works
Student logs in
Selects floor and room
Chooses bed:
Available → Booking
Occupied → Waitlist
Payment simulation
Data stored in MySQL
Admin monitors and controls system
