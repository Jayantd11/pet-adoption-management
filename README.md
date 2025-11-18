# Pet Adoption Management System

The Pet Adoption Management System is a Python desktop application designed to manage pet records, medical histories, staff information, and user accounts for an animal shelter.  
It uses Tkinter for the graphical interface and MySQL for the database backend.

This project includes user authentication, role-based access control, CRUD operations for pets, secure medical record viewing, staff listings, and multi-level analytics reports.

---

## Features

### 1. User Authentication and Management

- Login system with SHA-256 salted password hashing  
- User signup with default role `pending`  
- Admin-only user management:
  - Change user roles  
  - Reset passwords  
  - Delete users  
- Users can change their own password  
- Logout functionality  

---

### 2. Pet Management

- Add pets  
- Update pets  
- Delete pets  
- Search pets by name, species, or breed  
- Pet listings on dashboard and manage pages  
- Dashboard statistics:
  - Total pets  
  - Cats  
  - Dogs  
  - Others  

---

### 3. Medical Records

- Role-restricted access  
- View pet medical history including:
  - Diagnosis  
  - Medication  
  - Vet/staff name  
  - Date  
  - Notes  

---

### 4. Staff Information

- Restricted to manager/admin roles  
- Display staff name, role, branch, phone, and email  

---

### 5. Reports and Analytics

Includes SQL aggregation reports using **MIN, MAX, AVG, COUNT, SUM**, such as:

- Total pets, staff, branches, medical records  
- Pet age summary (min, max, average, total, count)  
- Pets per branch  
- Top pets by number of medical records  
- Overall managerial-level overview  

---

## User Roles

| Role     | Dashboard | Add/Manage Pets | Medical Records | Staff | Reports | User Management |
|----------|-----------|-----------------|------------------|--------|---------|------------------|
| pending  | Yes       | No              | No               | No     | No      | No               |
| staff    | Yes       | No              | Yes              | No     | No      | No               |
| manager  | Yes       | Yes             | Yes              | Yes    | Yes     | No               |
| admin    | Yes       | Yes             | Yes              | Yes    | Yes     | Yes              |

---

## System Requirements

- Python 3.x  
- MySQL Server  
- Python package:
  - `mysql-connector-python`

---

## Before Running

1. Install MySQL Server  
2. Start MySQL service (Windows):
   - Press `Win + R` → type `services.msc`  
   - Find `MySQL` or `MySQL80`  
   - Right-click → `Start`  
3. Create the `Pet_Adoption` database and tables  
4. Update MySQL connection credentials in code if needed  

---

## Running the Application

Run:

```bash
python main.py
```

---

##  Project Structure
```
project/
|-- main.py
|-- login_view.py
|-- signup_view.py
|-- user_management.py
|-- reports_view.py
|-- access_control.py
|-- auth_utils.py
|-- (other GUI/view modules)
|-- README.md
```
