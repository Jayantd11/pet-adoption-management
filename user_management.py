# user_management.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

from auth_utils import fetch_all_users, update_user_role, update_user_password

BG = "#F5F5F7"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#86868B"
BORDER = "#E5E5EA"


ROLE_CHOICES = ("pending", "staff", "manager", "admin")


def init_user_management(content, connection):
    """
    Creates the User Management frame (admin-only).
    Returns dict with:
      {
        "frame": <Frame>,
        "refresh": <callable to refresh user table>
      }
    """
    frame = tk.Frame(content, bg=BG)
    frame.grid(row=0, column=0, sticky="nsew")

    # Title
    tk.Label(
        frame,
        text="User Management",
        bg=BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 24, "bold")
    ).pack(anchor="w", padx=40, pady=(30, 20))

    # Container
    container = tk.Frame(frame, bg=BG)
    container.pack(fill="both", expand=True, padx=40, pady=(0, 30))

    # Left: table
    table_card = tk.Frame(container, bg=CARD_BG,
                          highlightthickness=1, highlightbackground=BORDER)
    table_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(
        table_card,
        text="Users",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", padx=24, pady=(16, 4))

    cols = ("UserID", "Username", "FullName", "Email", "Phone", "Role", "CreatedAt")
    tree = ttk.Treeview(table_card, columns=cols, show="headings", height=16)
    for col, w in zip(cols, (70, 120, 150, 170, 100, 90, 160)):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")

    scroll = tk.Scrollbar(table_card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True, padx=2, pady=(0, 4))
    scroll.pack(side="right", fill="y")

    # Right: controls
    side_card = tk.Frame(container, bg=CARD_BG,
                         highlightthickness=1, highlightbackground=BORDER)
    side_card.pack(side="left", fill="y", padx=(10, 0))

    inner = tk.Frame(side_card, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        inner,
        text="Selected User",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", pady=(0, 10))

    selected_user_id = {"value": None}

    # Helper to add labeled read-only entry
    def ro_field(label_text):
        wrap = tk.Frame(inner, bg=CARD_BG)
        wrap.pack(fill="x", pady=(2, 4))
        tk.Label(
            wrap,
            text=label_text,
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        ent = tk.Entry(
            wrap,
            bg="#F9F9F9",
            fg=TEXT_PRIMARY,
            relief="solid",
            bd=1,
            font=("Segoe UI", 10),
            state="readonly"
        )
        ent.pack(fill="x", ipady=3)
        return ent

    ent_username = ro_field("Username")
    ent_role = ro_field("Current Role")

    # Role change
    tk.Label(
        inner,
        text="Change Role",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w", pady=(10, 4))

    role_var = tk.StringVar()
    role_combo = ttk.Combobox(inner, textvariable=role_var,
                              values=ROLE_CHOICES, state="readonly")
    role_combo.pack(fill="x", pady=(0, 6))

    def on_change_role():
        uid = selected_user_id["value"]
        if uid is None:
            messagebox.showwarning("No selection", "Select a user first.")
            return
        new_role = role_var.get().strip()
        if not new_role:
            messagebox.showwarning("No role", "Select a new role.")
            return
        try:
            update_user_role(connection, uid, new_role)
            messagebox.showinfo("Role Updated", "User role updated successfully.")
            refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update role:\n{e}")

    tk.Button(
        inner,
        text="Update Role",
        command=on_change_role,
        bg="#007AFF",
        fg="white",
        relief="flat",
        padx=12, pady=6,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2"
    ).pack(fill="x", pady=(0, 10))

    # Password reset
    tk.Label(
        inner,
        text="Reset Password",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w", pady=(8, 4))

    pw1_var = tk.StringVar()
    pw2_var = tk.StringVar()

    def pw_field(label, var):
        wrap = tk.Frame(inner, bg=CARD_BG)
        wrap.pack(fill="x", pady=(2, 2))
        tk.Label(
            wrap,
            text=label,
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9)
        ).pack(anchor="w")
        e = tk.Entry(
            wrap,
            textvariable=var,
            show="*",
            bg="white",
            fg=TEXT_PRIMARY,
            relief="solid",
            bd=1,
            font=("Segoe UI", 10)
        )
        e.pack(fill="x", ipady=3)
        return e

    pw1_entry = pw_field("New Password", pw1_var)
    pw2_entry = pw_field("Confirm Password", pw2_var)

    def on_reset_password():
        uid = selected_user_id["value"]
        if uid is None:
            messagebox.showwarning("No selection", "Select a user first.")
            return
        p1 = pw1_var.get()
        p2 = pw2_var.get()
        if not p1 or not p2:
            messagebox.showwarning("Missing", "Enter and confirm the new password.")
            return
        if p1 != p2:
            messagebox.showwarning("Mismatch", "Passwords do not match.")
            return
        try:
            update_user_password(connection, uid, p1)
            messagebox.showinfo("Password Reset", "Password updated successfully.")
            pw1_var.set("")
            pw2_var.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Could not reset password:\n{e}")

    tk.Button(
        inner,
        text="Reset Password",
        command=on_reset_password,
        bg="#34C759",
        fg="white",
        relief="flat",
        padx=12, pady=6,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2"
    ).pack(fill="x", pady=(6, 10))

    # Delete user
    tk.Label(
        inner,
        text="Danger Zone",
        bg=CARD_BG,
        fg="#FF3B30",
        font=("Segoe UI", 10, "bold")
    ).pack(anchor="w", pady=(10, 4))

    def on_delete_user():
        uid = selected_user_id["value"]
        if uid is None:
            messagebox.showwarning("No selection", "Select a user first.")
            return
        if not messagebox.askyesno(
            "Delete User",
            "Are you sure you want to delete this user? This cannot be undone."
        ):
            return
        try:
            cur = connection.cursor()
            cur.execute("DELETE FROM USER_ACCOUNT WHERE user_id = %s", (uid,))
            connection.commit()
            cur.close()
            messagebox.showinfo("Deleted", "User deleted.")
            selected_user_id["value"] = None
            ent_username.config(state="normal")
            ent_username.delete(0, "end")
            ent_username.config(state="readonly")
            ent_role.config(state="normal")
            ent_role.delete(0, "end")
            ent_role.config(state="readonly")
            refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete user:\n{e}")

    tk.Button(
        inner,
        text="Delete User",
        command=on_delete_user,
        bg="#FF3B30",
        fg="white",
        relief="flat",
        padx=12, pady=6,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2"
    ).pack(fill="x", pady=(2, 0))

    # ---------- Refresh ----------
    def refresh():
        for r in tree.get_children():
            tree.delete(r)

        try:
            users = fetch_all_users(connection)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Could not load users:\n{e}")
            return

        for u in users:
            tree.insert(
                "",
                "end",
                values=(
                    u["user_id"],
                    u["username"],
                    u["full_name"] or "",
                    u["email"] or "",
                    u["phone"] or "",
                    u["role"],
                    u["created_at"],
                ),
            )

    # When selecting a row
    def on_select(event):
        sel = tree.selection()
        if not sel:
            return
        item = tree.item(sel[0])
        vals = item["values"]
        if not vals:
            return

        uid, uname, _, _, _, role, _ = vals
        selected_user_id["value"] = uid

        ent_username.config(state="normal")
        ent_username.delete(0, "end")
        ent_username.insert(0, uname)
        ent_username.config(state="readonly")

        ent_role.config(state="normal")
        ent_role.delete(0, "end")
        ent_role.insert(0, role)
        ent_role.config(state="readonly")

        role_var.set(role)

    tree.bind("<<TreeviewSelect>>", on_select)

    return {"frame": frame, "refresh": refresh}
