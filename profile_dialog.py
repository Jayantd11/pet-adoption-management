import tkinter as tk
from tkinter import ttk, messagebox

from auth_utils import authenticate_user, update_user_password


def open_change_password_dialog(root, connection, current_user):
    """
    current_user is the dict returned from authenticate_user / show_login:
      { user_id, username, full_name, email, phone, role }
    """
    dlg = tk.Toplevel(root)
    dlg.title("Change Password")
    dlg.resizable(False, False)
    dlg.transient(root)
    dlg.grab_set()

    dlg.geometry("380x260")

    main = ttk.Frame(dlg, padding=20)
    main.pack(fill="both", expand=True)

    ttk.Label(
        main,
        text=f"Change Password ({current_user['username']})",
        font=("Segoe UI", 12, "bold")
    ).pack(anchor="w", pady=(0, 10))

    old_var = tk.StringVar()
    new1_var = tk.StringVar()
    new2_var = tk.StringVar()

    def add_field(label, var):
        row = ttk.Frame(main)
        row.pack(fill="x", pady=(6, 2))
        ttk.Label(row, text=label).pack(anchor="w")
        ent = ttk.Entry(row, textvariable=var, show="*")
        ent.pack(fill="x")
        return ent

    old_entry = add_field("Current Password", old_var)
    add_field("New Password", new1_var)
    add_field("Confirm New Password", new2_var)

    msg = ttk.Label(main, text="", foreground="red")
    msg.pack(anchor="w", pady=(6, 0))

    def do_change():
        old = old_var.get()
        n1 = new1_var.get()
        n2 = new2_var.get()

        if not old or not n1 or not n2:
            msg.config(text="All fields are required.")
            return

        # Verify old password
        u = authenticate_user(connection, current_user["username"], old)
        if not u:
            msg.config(text="Current password is incorrect.")
            return

        if n1 != n2:
            msg.config(text="New passwords do not match.")
            return

        try:
            update_user_password(connection, current_user["user_id"], n1)
            messagebox.showinfo("Password Changed", "Your password has been updated.")
            dlg.destroy()
        except Exception as e:
            msg.config(text=f"Error: {e}")

    btn_row = ttk.Frame(main)
    btn_row.pack(fill="x", pady=(14, 0))
    ttk.Button(btn_row, text="Save", command=do_change).pack(side="left")
    ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(side="left", padx=(8, 0))

    old_entry.focus_set()