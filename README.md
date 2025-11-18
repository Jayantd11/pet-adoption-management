Pet Adoption Management System

This project is a full-featured desktop application for managing a pet adoption shelter.
It is built using Python (Tkinter) for the graphical interface and MySQL as the database backend.

The system supports user authentication, role-based access control, pet management, staff information, medical records, and multiple analytical reports.

Features
1. User Authentication and Role Management

Secure login using SHA-256 salted password hashing

User signup with automatic pending role assignment

Admin-only User Management interface

Role assignment for:

pending

staff

manager

admin

Admin functions:

Reset user passwords

Change user roles

Delete users

Each user can change their own password

Logout functionality included

2. Pet Management

Add new pets to the system

Update or delete existing pet records

Search pets by name, species, or breed

Pet listing table with sorting and filtering

Automatic branch assignment through dropdown menus

Dashboard with live statistics:

Total pets

Total cats, dogs, and others

3. Medical Records Management

Role-protected access

View medical diagnosis history for each pet

Records include:

Diagnosis type

Medication

Vet/staff responsible

Date

Notes

4. Staff Information

Secure, role-restricted access

Displays staff:

Name

Role

Branch

Phone

Email

5. Reports and Analytics

Includes multiple SQL-based reports (using MIN, MAX, AVG, COUNT, and SUM):

Total counts:

Pets

Medical records

Staff

Shelter branches

Pet age statistics (min, max, average, sum, and total)

Pets per branch

Top pets by number of medical records

Managerial-level overview for data-driven insights

System Requirements
Software Required

Python 3.x

MySQL Server

Required Python packages:

mysql-connector-python

(Other dependencies are part of Python standard library)

Before Running the Application

Ensure MySQL Server is installed.

Start the MySQL service on Windows:

Press Win + R, type services.msc, press Enter.

Find the MySQL service (MySQL or MySQL80).

Right-click → Start.

Create the Pet_Adoption database and required tables.

Ensure that your local MySQL username, password, and host match the values in the code.

Running the Application

From the project directory, run:

python main.py


This will start the login interface and load the full dashboard after successful login.

Default Admin Credentials

An initial administrator account is provided for first-time access:

Username: admin1
Password: SQLProject@fall25


This account can:

Access all sections

Manage users

Assign roles

View all reports and staff data

Signing Up as a New User

Click the Sign Up button on the login screen.

Fill in the fields (username, full name, email, phone, password).

New accounts start as pending users.

An admin must update the role before full access is granted.
