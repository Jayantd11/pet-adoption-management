# login_screen.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

from auth_utils import authenticate_user, create_user


def show_login(connection):
    """
    Open a blocking login/signup window.
    Returns a user dict on successful login, or None if user closes the window.
    """
    logged_in_user = {"value": None}  # mutable holder

    root = tk.Tk()
    root.title("Login - Pet Adoption System")
    root.geometry("420x320")
    root.resizable(False, False)

    # ---------- BASIC LAYOUT ----------
    main = ttk.Frame(root, padding=20)
    main.pack(fill="both", expand=True)

    title = ttk.Label(main, text="Pet Adoption Login", font=("Segoe UI", 16, "bold"))
    title.pack(pady=(0, 10))

    # Username / password fields
    user_var = tk.StringVar()
    pw_var = tk.StringVar()

    user_row = ttk.Frame(main)
    user_row.pack(fill="x", pady=(10, 4))
    ttk.Label(user_row, text="Username:").pack(anchor="w")
    user_entry = ttk.Entry(user_row, textvariable=user_var)
    user_entry.pack(fill="x")

    pw_row = ttk.Frame(main)
    pw_row.pack(fill="x", pady=(10, 4))
    ttk.Label(pw_row, text="Password:").pack(anchor="w")
    pw_entry = ttk.Entry(pw_row, textvariable=pw_var, show="*")
    pw_entry.pack(fill="x")

    msg_label = ttk.Label(main, text="", foreground="red")
    msg_label.pack(anchor="w", pady=(6, 0))

    btn_row = ttk.Frame(main)
    btn_row.pack(fill="x", pady=(20, 0))

    # ---------- HANDLERS ----------

    def do_login(*_):
        username = user_var.get().strip()
        password = pw_var.get().strip()

        if not username or not password:
            msg_label.config(text="Please enter username and password.")
            return

        user = authenticate_user(connection, username, password)
        if not user:
            msg_label.config(text="Invalid username or password.")
            return

        # If pending → allow login but warn OR block. You said:
        # "pending will only see dashboard", so we allow login.
        if user["role"] == "pending":
            messagebox.showinfo(
                "Pending Approval",
                "Your account is pending. You can log in, but only see the dashboard until an admin assigns a role."
            )

        logged_in_user["value"] = user
        root.destroy()

    def open_signup():
        SignupWindow(connection, parent=root)

    ttk.Button(btn_row, text="Login", command=do_login).pack(side="left", padx=(0, 10))
    ttk.Button(btn_row, text="Sign Up", command=open_signup).pack(side="left")

    # Bind Enter key to login
    root.bind("<Return>", do_login)

    user_entry.focus_set()
    root.mainloop()

    return logged_in_user["value"]


class SignupWindow:
    """
    Simple Sign Up dialog:
    - username
    - full name
    - email
    - phone
    - password + confirm
    Role is always 'pending' here; only admin can assign others.
    """
    def __init__(self, connection, parent=None):
        self.connection = connection
        self.parent = parent

        self.top = tk.Toplevel(parent)
        self.top.title("Sign Up - Pet Adoption")
        self.top.geometry("420x420")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        main = ttk.Frame(self.top, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Create Account", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))

        self.username_var = tk.StringVar()
        self.fullname_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.pw1_var = tk.StringVar()
        self.pw2_var = tk.StringVar()

        def add_field(label, var, show=None):
            row = ttk.Frame(main)
            row.pack(fill="x", pady=(6, 2))
            ttk.Label(row, text=label).pack(anchor="w")
            e = ttk.Entry(row, textvariable=var, show=show)
            e.pack(fill="x")
            return e

        self.username_entry = add_field("Username", self.username_var)
        add_field("Full Name", self.fullname_var)
        add_field("Email", self.email_var)
        add_field("Phone", self.phone_var)
        add_field("Password", self.pw1_var, show="*")
        add_field("Confirm Password", self.pw2_var, show="*")

        self.msg_label = ttk.Label(main, text="", foreground="red")
        self.msg_label.pack(anchor="w", pady=(6, 0))

        btn_row = ttk.Frame(main)
        btn_row.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_row, text="Create Account", command=self.create_account).pack(side="left", padx=(0, 10))
        ttk.Button(btn_row, text="Cancel", command=self.top.destroy).pack(side="left")

        self.username_entry.focus_set()

    def create_account(self):
        username = self.username_var.get().strip()
        full_name = self.fullname_var.get().strip() or None
        email = self.email_var.get().strip() or None
        phone = self.phone_var.get().strip() or None
        pw1 = self.pw1_var.get()
        pw2 = self.pw2_var.get()

        if not username or not pw1 or not pw2:
            self.msg_label.config(text="Username and password fields are required.")
            return

        if pw1 != pw2:
            self.msg_label.config(text="Passwords do not match.")
            return

        try:
            create_user(
                self.connection,
                username=username,
                plain_password=pw1,
                full_name=full_name,
                email=email,
                phone=phone,
                role="pending"  # always pending on sign-up
            )
        except mysql.connector.IntegrityError:
            self.msg_label.config(text="Username already exists.")
            return
        except Exception as e:
            self.msg_label.config(text=f"Error: {e}")
            return

        messagebox.showinfo(
            "Account Created",
            "Your account has been created.\n"
            "An admin must assign your role.\nYou can log in as 'pending' and see the dashboard."
        )
        self.top.destroy()
