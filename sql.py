import mysql.connector
# Services.msc - mysql - start
# & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
# Connect to local MySQL Serve
#FOR LOGIN USERNAME AND PASSWORD
#ADMIN USERNAME: admin1
#ADMIN PASSWORD: SQLProject@fall25
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Arnav111!!!'
)


cursor = connection.cursor()

db_name = "Pet_Adoption"
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
cursor.execute(f"USE {db_name}")

cursor.execute(f"CREATE TABLE IF NOT EXISTS SHELTER_BRANCH ( "
        "branch_id INT AUTO_INCREMENT PRIMARY KEY,"
        "branch_name VARCHAR(100) NOT NULL, "
        "address VARCHAR(255), "
        "phone VARCHAR(20), "
        "capacity INT, "
        "manager_name VARCHAR(100))")

cursor.execute("CREATE TABLE IF NOT EXISTS ADOPTER ("
        "    adopter_id INT AUTO_INCREMENT PRIMARY KEY, "
        "    first_name VARCHAR(50) NOT NULL, "
        "    last_name VARCHAR(50) NOT NULL, "
        "    email VARCHAR(100) UNIQUE NOT NULL, "
        "    phone VARCHAR(20), "
        "    address VARCHAR(255), "
        "    background_check_status VARCHAR(50), "
        "    preferences TEXT"
        ")")

cursor.execute("CREATE TABLE IF NOT EXISTS STAFF ("
        "    staff_id INT AUTO_INCREMENT PRIMARY KEY, "
        "    first_name VARCHAR(50) NOT NULL, "
        "    last_name VARCHAR(50) NOT NULL, "
        "    email VARCHAR(100) UNIQUE NOT NULL, "
        "    phone VARCHAR(20), "
        "    role VARCHAR(50), "
        "    hire_date DATE, "
        "    ssn VARCHAR(11) UNIQUE NOT NULL, "
        "    shelter_branch_id INT, "
        "    FOREIGN KEY (shelter_branch_id) REFERENCES SHELTER_BRANCH(branch_id)"
        ")")

#pet db - https://data.montgomerycountymd.gov/Public-Safety/Adoptable-Pets/e54u-qx42/data_preview
cursor.execute("CREATE TABLE IF NOT EXISTS PET ("
        "    pet_id INT AUTO_INCREMENT PRIMARY KEY, "
        "    name VARCHAR(50) NOT NULL, "
        "    gender VARCHAR(10), "
        "    species VARCHAR(50), "
        "    breed VARCHAR(50), "
        "    age INT, "
        "    description TEXT, "
        "    adoption_status VARCHAR(50) DEFAULT 'Available', "
        "    arrival_date DATE, "
        "    shelter_branch_id INT, "
        "    FOREIGN KEY (shelter_branch_id) REFERENCES SHELTER_BRANCH(branch_id)"
        ")")

cursor.execute(
    "CREATE TABLE IF NOT EXISTS MEDICAL_RECORD ("
        "    record_id INT AUTO_INCREMENT PRIMARY KEY, "
        "    type VARCHAR(100), "
        "    date DATE, "
        "    medication VARCHAR(255), "
        "    vet_staff_id INT, "
        "    description TEXT, "
        "    pet_id INT, "
        "    FOREIGN KEY (pet_id) REFERENCES PET(pet_id), "
        "    FOREIGN KEY (vet_staff_id) REFERENCES STAFF(staff_id)"
        ")"
)

cursor.execute(
    "CREATE TABLE IF NOT EXISTS ADOPTION_APPLICATION ("
        "    application_id INT AUTO_INCREMENT PRIMARY KEY, "
        "    status VARCHAR(50), "
        "    review_notes TEXT, "
        "    application_date DATE, "
        "    decision_date DATE, "
        "    adopter_id INT, "
        "    pet_id INT, "
        "    FOREIGN KEY (adopter_id) REFERENCES ADOPTER(adopter_id), "
        "    FOREIGN KEY (pet_id) REFERENCES PET(pet_id)"
        ")"
)

connection.commit()