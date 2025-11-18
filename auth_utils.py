# auth_utils.py
import hashlib
import mysql.connector

# Constant salt for project (good enough for class-level security)
_SALT = b"pet_adoption_salt_2025"


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using SHA-256 with a fixed salt.
    Returns a hex string of length 64.
    """
    if plain_password is None:
        plain_password = ""
    h = hashlib.sha256()
    h.update(_SALT)
    h.update(plain_password.encode("utf-8"))
    return h.hexdigest()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Check if given plain password matches stored hash.
    """
    if not stored_hash:
        return False
    return hash_password(plain_password) == stored_hash


def ensure_user_table(connection):
    """
    Create USER_ACCOUNT table if it does not exist.
    Safe to call every time at startup.
    """
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USER_ACCOUNT (
            user_id       INT AUTO_INCREMENT PRIMARY KEY,
            username      VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(64) NOT NULL,
            full_name     VARCHAR(100),
            email         VARCHAR(100),
            phone         VARCHAR(30),
            role          ENUM('admin', 'manager', 'staff', 'pending') NOT NULL DEFAULT 'pending',
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    cursor.close()


def create_user(connection, username: str, plain_password: str,
                full_name: str = None, email: str = None, phone: str = None,
                role: str = "pending"):
    """
    Insert a new user. By design here, default role is 'pending'.
    """
    password_hash = hash_password(plain_password)
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO USER_ACCOUNT (username, password_hash, full_name, email, phone, role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, password_hash, full_name, email, phone, role))
        connection.commit()
    finally:
        cursor.close()


def authenticate_user(connection, username: str, plain_password: str):
    """
    Check username/password and return a user dict if valid, else None.
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, password_hash, full_name, email, phone, role
            FROM USER_ACCOUNT
            WHERE username = %s
        """, (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()

    if not row:
        return None

    user_id, uname, pw_hash, full_name, email, phone, role = row
    if not verify_password(plain_password, pw_hash):
        return None

    return {
        "user_id": user_id,
        "username": uname,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "role": role,
    }


def update_user_role(connection, user_id: int, new_role: str):
    """
    Change a user's role (admin-only operation; enforce in GUI).
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE USER_ACCOUNT
            SET role = %s
            WHERE user_id = %s
        """, (new_role, user_id))
        connection.commit()
    finally:
        cursor.close()


def update_user_password(connection, user_id: int, new_plain_password: str):
    """
    Change a user's password to a new value.
    """
    new_hash = hash_password(new_plain_password)
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE USER_ACCOUNT
            SET password_hash = %s
            WHERE user_id = %s
        """, (new_hash, user_id))
        connection.commit()
    finally:
        cursor.close()


def fetch_all_users(connection):
    """
    For future Admin User Management page.
    Returns list of dicts: [{...}, ...]
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT user_id, username, full_name, email, phone, role, created_at
            FROM USER_ACCOUNT
            ORDER BY user_id
        """)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    users = []
    for r in rows:
        user_id, username, full_name, email, phone, role, created_at = r
        users.append({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "role": role,
            "created_at": created_at,
        })
    return users
