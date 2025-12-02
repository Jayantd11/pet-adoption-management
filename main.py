import mysql.connector
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------- DATABASE CONNECTION ----------
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='Pet_Adoption'
)
cursor = connection.cursor()

cursor.execute("SELECT branch_id, branch_name FROM SHELTER_BRANCH")
branches = cursor.fetchall()
branch_options = {f"{name} (ID {bid})": bid for bid, name in branches}

print("Connected successfully to Pet_Adoption database")

from auth_utils import ensure_user_table
from login_screen import show_login
from access_control import can_access
from user_management import init_user_management
from profile_dialog import open_change_password_dialog
from reports_view import init_reports



# Handles for secure pages/tables
medical_frame = None
staff_frame = None
medical_table = None
staff_table = None


# ---------- COLORS / STYLE ----------
BG = "#F5F5F7"          # main background 
CARD_BG = "#FFFFFF"      # cards / panels
SIDEBAR_BG = "#2C2C2E"   # dark sidebar
SIDEBAR_BORDER = "#3A3A3C"
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#86868B"
SIDEBAR_TEXT = "#000000"
SIDEBAR_TEXT_INACTIVE = "#98989D"
ACCENT = "#007AFF"       # brighter blue
ACCENT_HOVER = "#0051D5"
ACCENT_SOFT = "#E8F4FF"
SUCCESS = "#34C759"
DANGER = "#FF3B30"
WARNING = "#FF9500"
BORDER = "#E5E5EA"
INPUT_BG = "#FFFFFF"
INPUT_BORDER = "#D1D1D6"
INPUT_FOCUS = "#007AFF"

ensure_user_table(connection)

# Login/signup before opening main app window
current_user = show_login(connection)
if current_user is None:
    # User closed login window; exit app
    raise SystemExit("No login; exiting.")

CURRENT_USER_ROLE = current_user["role"]
CURRENT_USERNAME = current_user["username"]
CURRENT_USER = current_user 
print(f"Logged in as {CURRENT_USERNAME} with role {CURRENT_USER_ROLE}")


# ---------- ROOT ----------
root = Tk()
root.title("Pet Adoption Management")
root.state("zoomed")
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview",
                background=CARD_BG,
                foreground=TEXT_PRIMARY,
                fieldbackground=CARD_BG,
                rowheight=32,
                bordercolor=BORDER,
                borderwidth=0,
                font=("Segoe UI", 10))

style.configure("Treeview.Heading",
                background=CARD_BG,
                foreground=TEXT_SECONDARY,
                font=("Segoe UI", 10, "bold"),
                borderwidth=0)

style.map("Treeview", 
          background=[("selected", ACCENT_SOFT)],
          foreground=[("selected", ACCENT)])

# Combobox styling
style.configure("TCombobox",
                fieldbackground=INPUT_BG,
                background=INPUT_BG,
                foreground=TEXT_PRIMARY,
                bordercolor=INPUT_BORDER,
                lightcolor=INPUT_BG,
                darkcolor=INPUT_BG,
                arrowcolor=TEXT_SECONDARY)


# ---------- GLOBAL WIDGET HANDLES ----------
pet_table_dashboard = None
pet_table_manage = None
status_label = None

sidebar_buttons = {}
frames = {}


# ---------- HELPER: SUMMARY QUERIES ----------
def get_species_counts():
    cursor.execute("SELECT species, COUNT(*) FROM PET GROUP BY species")
    rows = cursor.fetchall()
    cats = dogs = others = 0
    for species, count in rows:
        s = (species or "").strip().upper()
        if "CAT" in s:
            cats += count
        elif "DOG" in s:
            dogs += count
        else:
            others += count
    total = cats + dogs + others
    return total, cats, dogs, others


def get_branch_counts():
    cursor.execute("""
        SELECT b.branch_name, COUNT(p.pet_id)
        FROM SHELTER_BRANCH b
        LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id
        GROUP BY b.branch_id, b.branch_name
        ORDER BY b.branch_name
    """)
    return cursor.fetchall()


# ---------- CORE FUNCTIONS ----------
def clear_fields():
    entry_name.delete(0, END)
    entry_gender.delete(0, END)
    entry_species.delete(0, END)
    entry_breed.delete(0, END)
    entry_age.delete(0, END)
    entry_description.delete(0, END)
    entry_arrival.delete(0, END)
    branch_var.set("")


def add_pet():
    try:
        name = entry_name.get().strip()
        gender = entry_gender.get().strip()
        species = entry_species.get().strip()
        breed = entry_breed.get().strip()
        age = entry_age.get().strip()
        description = entry_description.get().strip()
        arrival_date = entry_arrival.get().strip()
        selected_branch = branch_var.get()
        branch_id = branch_options.get(selected_branch)

        if not name or not species:
            set_status("Error: Name and Species are required.")
            return

        if age and not age.isdigit():
            set_status("Error: Age must be numeric.")
            return

        if arrival_date:
            try:
                datetime.strptime(arrival_date, "%Y-%m-%d")
            except ValueError:
                set_status("Error: Invalid date format (YYYY-MM-DD).")
                return

        sql = """
        INSERT INTO PET
        (name, gender, species, breed, age, description, arrival_date, shelter_branch_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        values = (name, gender, species, breed, age or None,
                  description, arrival_date or None, branch_id)
        cursor.execute(sql, values)
        connection.commit()

        set_status(f"Added pet '{name}'.")
        clear_fields()
        refresh_dashboard()
        refresh_manage_table()
    except Exception as e:
        set_status(f"Error: {e}")


def delete_pet():
    pet_id = entry_delete_id.get().strip()
    if not pet_id:
        set_status("Error: Enter Pet ID to delete.")
        return
    try:
        cursor.execute("DELETE FROM PET WHERE pet_id=%s", (pet_id,))
        connection.commit()
        if cursor.rowcount == 0:
            set_status("No pet found with that ID.")
        else:
            set_status(f"Deleted Pet ID {pet_id}.")
        entry_delete_id.delete(0, END)
        refresh_dashboard()
        refresh_manage_table()
    except Exception as e:
        set_status(f"Error: {e}")


def update_pet():
    pet_id = entry_update_id.get().strip()
    if not pet_id:
        set_status("Error: Enter Pet ID to update.")
        return

    name = entry_upd_name.get().strip()
    age = entry_upd_age.get().strip()
    description = entry_upd_desc.get().strip()

    if age and not age.isdigit():
        set_status("Error: Age must be numeric.")
        return

    try:
        cursor.execute("SELECT * FROM PET WHERE pet_id=%s", (pet_id,))
        if cursor.fetchone() is None:
            set_status("No pet found with that ID.")
            return

        cursor.execute(
            "UPDATE PET SET name=%s, age=%s, description=%s WHERE pet_id=%s",
            (name or None, age or None, description or None, pet_id)
        )
        connection.commit()
        set_status(f"Updated Pet ID {pet_id}.")
        clear_update_fields()
        refresh_dashboard()
        refresh_manage_table()
    except Exception as e:
        set_status(f"Error: {e}")


def clear_update_fields():
    entry_update_id.delete(0, END)
    entry_upd_name.delete(0, END)
    entry_upd_age.delete(0, END)
    entry_upd_desc.delete(0, END)

def build_bar_chart(parent, title, labels, values):
    fig = Figure(figsize=(5, 2.4), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(labels, values)
    ax.set_title(title)
    ax.tick_params(axis='x', rotation=30)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

def search_pets():
    query = entry_search.get().strip()
    if not query:
        refresh_manage_table()
        set_status("Showing all pets.")
        return

    sql = """
    SELECT pet_id, name, species, breed, age, shelter_branch_id
    FROM PET
    WHERE name LIKE %s OR species LIKE %s OR breed LIKE %s
    """
    like = f"%{query}%"
    cursor.execute(sql, (like, like, like))
    rows = cursor.fetchall()
    update_table(pet_table_manage, rows)
    set_status(f"Search results for '{query}'.")


def refresh_manage_table():
    cursor.execute("""
        SELECT pet_id, name, species, breed, age, shelter_branch_id
        FROM PET
        ORDER BY pet_id
    """)
    rows = cursor.fetchall()
    update_table(pet_table_manage, rows)


def refresh_dashboard():
    # Summary cards
    total, cats, dogs, others = get_species_counts()
    total_label_val.config(text=str(total))
    cats_label_val.config(text=str(cats))
    dogs_label_val.config(text=str(dogs))
    others_label_val.config(text=str(others))

    # Branch cards
    for w in branch_cards_frame.winfo_children():
        w.destroy()
    
    branch_list = get_branch_counts()
    for idx, (name, count) in enumerate(branch_list):
        # Truncate name to just show county name
        display_name = name
        if "County" in name:
            display_name = name.split("County")[0] + "County"
        
        card = Frame(branch_cards_frame, bg=CARD_BG, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)
        # First card has no left padding, rest have right padding
        if idx == len(branch_list) - 1:
            card.pack(side=LEFT, padx=0, pady=0, fill=BOTH, expand=True)
        else:
            card.pack(side=LEFT, padx=(0, 12), pady=0, fill=BOTH, expand=True)
        
        # Add inner padding
        inner = Frame(card, bg=CARD_BG)
        inner.pack(fill=BOTH, expand=True, padx=24, ipady=16)
        
        Label(inner, text=display_name, bg=CARD_BG, fg=TEXT_SECONDARY,
              font=("Segoe UI", 10)).pack(anchor=W, pady=(4, 0))
        Label(inner, text=str(count), bg=CARD_BG, fg=TEXT_PRIMARY,
              font=("Segoe UI", 20, "bold")).pack(anchor=W, pady=(4, 4))

    # Dashboard table
    cursor.execute("""
        SELECT pet_id, name, species, breed, age, shelter_branch_id
        FROM PET
        ORDER BY pet_id
    """)
    rows = cursor.fetchall()
    update_table(pet_table_dashboard, rows)


def update_table(tree, rows):
    if tree is None:
        return
    for r in tree.get_children():
        tree.delete(r)
    for row in rows:
        tree.insert("", "end", values=row)


def set_status(text):
    if status_label is not None:
        status_label.config(text=text)

def show_frame(name):
    frame = frames.get(name)
    if not frame:
        return

    if not can_access(CURRENT_USER_ROLE, name):
        set_status("You do not have permission to access this section.")
        return

    def _raise_and_status(msg=None):
        frame.tkraise()
        set_active_button(name)
        if msg:
            set_status(msg)

    if name == "dashboard":
        refresh_dashboard()
        _raise_and_status("Dashboard loaded")
    elif name == "manage":
        refresh_manage_table()
        _raise_and_status("Manage pets")
    elif name == "add":
        _raise_and_status("Add a new pet")
    elif name == "medical":
        refresh_medical_table()
        _raise_and_status("Medical Records (secure)")
    elif name == "staff":
        refresh_staff_table()
        _raise_and_status("Staff Details (secure)")
    elif name == "user_admin":
        refresh_user_admin()
        _raise_and_status("User Management (admin)")
    elif name == "reports":
        refresh_reports()
        _raise_and_status("Reports & Analytics")


# ---------- SIDEBAR / NAV ----------
main_container = Frame(root, bg=BG)
main_container.pack(fill=BOTH, expand=True)

# Sidebar
sidebar = Frame(main_container, bg=SIDEBAR_BG, width=240,
                highlightthickness=0)
sidebar.pack(side=LEFT, fill=Y)

# Content area
content = Frame(main_container, bg=BG)
content.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
content.grid_rowconfigure(0, weight=1)
content.grid_columnconfigure(0, weight=1)

# ---------- MEDICAL RECORDS FRAME ----------
medical_frame = Frame(content, bg=BG)
medical_frame.grid(row=0, column=0, sticky="nsew")
frames["medical"] = medical_frame

Label(
    medical_frame,
    text="Medical Records",
    bg=BG,
    fg=TEXT_PRIMARY,
    font=("Segoe UI", 24, "bold")
).pack(anchor="w", padx=40, pady=(30, 20))

# Scrollable container
med_canvas = Canvas(medical_frame, bg=BG, highlightthickness=0)
med_vbar   = Scrollbar(medical_frame, orient=VERTICAL, command=med_canvas.yview)
med_canvas.configure(yscrollcommand=med_vbar.set)
med_canvas.pack(side=LEFT, fill=BOTH, expand=True)
med_vbar.pack(side=RIGHT, fill=Y)

med_scrollable = Frame(med_canvas, bg=BG)
med_scrollable.bind(
    "<Configure>",
    lambda e: med_canvas.configure(scrollregion=med_canvas.bbox("all"))
)
med_win = med_canvas.create_window((0, 0), window=med_scrollable, anchor="nw")
med_canvas.bind(
    "<Configure>",
    lambda e: med_canvas.itemconfig(med_win, width=e.width)
)

# Header card
med_hdr = Frame(med_scrollable, bg=CARD_BG,
                highlightthickness=1, highlightbackground=BORDER)
med_hdr.pack(fill=X, padx=40, pady=(0, 20))

Frame(med_hdr, bg=CARD_BG).pack(fill=X, padx=24, pady=16)

Label(
    med_hdr,
    text="(Secure) View of Medical Records",
    bg=CARD_BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=24, pady=(0, 2))

Label(
    med_hdr,
    text="Access is password-protected for this session.",
    bg=CARD_BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 10)
).pack(anchor="w", padx=24, pady=(0, 14))

# Table section
med_tbl_section = Frame(med_scrollable, bg=BG)
med_tbl_section.pack(fill=BOTH, expand=True, padx=40, pady=(0, 30))

Label(
    med_tbl_section,
    text="Records",
    bg=BG,
    fg=TEXT_SECONDARY,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", pady=(0, 12))

med_tbl_container = Frame(
    med_tbl_section,
    bg=CARD_BG,
    highlightthickness=1,
    highlightbackground=BORDER
)
med_tbl_container.pack(fill=BOTH, expand=True)

med_columns = (
    "RecordID",    
    "PetID",     
    "PetName",     
    "Type",       
    "Medication",  
    "Vet",         
    "Date",        
    "Notes"        
)

medical_table = ttk.Treeview(
    med_tbl_container,
    columns=med_columns,
    show="headings",
    height=14
)

# Nice headers + explicit widths so Date is always visible
header_text = {
    "RecordID":   "Record ID",
    "PetID":      "Pet ID",
    "PetName":    "Pet",
    "Type":       "Diagnosis",
    "Medication": "Treatment",
    "Vet":        "Vet / Staff",
    "Date":       "Date",
    "Notes":      "Notes",
}

col_widths = {
    "RecordID":   80,
    "PetID":      70,
    "PetName":    150,
    "Type":       150,
    "Medication": 200,
    "Vet":        160,
    "Date":       110,
    "Notes":      250,
}

for col in med_columns:
    medical_table.heading(col, text=header_text[col])
    # Date slightly centered, others left-aligned
    anchor = "center" if col == "Date" else "w"
    medical_table.column(col, width=col_widths[col], anchor=anchor)

med_scroll = Scrollbar(med_tbl_container, orient=VERTICAL, command=medical_table.yview)
medical_table.configure(yscrollcommand=med_scroll.set)
medical_table.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
med_scroll.pack(side=RIGHT, fill=Y)


def refresh_medical_table():
    """
    Loads medical records with joined pet + staff info.

    Columns returned (in order):
      record_id, pet_id, pet_name, type, medication, vet_name, date, description
    This matches med_columns above.
    """
    try:
        cursor.execute("""
            SELECT
                mr.record_id,
                mr.pet_id,
                p.name AS pet_name,
                mr.type,
                mr.medication,
                CONCAT(s.first_name, ' ', s.last_name) AS vet_name,
                mr.date,
                mr.description
            FROM medical_record mr
            LEFT JOIN pet   p ON p.pet_id   = mr.pet_id
            LEFT JOIN staff s ON s.staff_id = mr.vet_staff_id
            ORDER BY mr.record_id DESC
        """)
        rows = cursor.fetchall()
        update_table(medical_table, rows)
        set_status(f"Medical Records: {len(rows)} row(s)")
    except mysql.connector.Error as e:
        update_table(medical_table, [])
        set_status("Medical Records: query error")
        messagebox.showerror("Medical Records error", f"{e}")

# ----- MEDICAL EDIT FORM (ADD / UPDATE / DELETE) -----

med_edit_card = Frame(med_scrollable, bg=CARD_BG,
                      highlightthickness=1, highlightbackground=BORDER)
med_edit_card.pack(fill=X, padx=40, pady=(20, 30))

med_edit_inner = Frame(med_edit_card, bg=CARD_BG)
med_edit_inner.pack(fill=BOTH, padx=24, pady=20)

Label(med_edit_inner, text="Edit Medical Record (Staff / Admin)",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=4,
                                           sticky="w", pady=(0, 16))

Label(med_edit_inner, text="Record ID (for update / delete)",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).grid(row=1, column=0,
                                          sticky="w", pady=(0, 4), padx=(0, 8))
med_rec_id_var = StringVar()
entry_med_rec_id = Entry(med_edit_inner,
                         textvariable=med_rec_id_var,
                         bg=INPUT_BG, fg=TEXT_PRIMARY,
                         relief="solid", bd=1,
                         highlightcolor=INPUT_FOCUS,
                         highlightthickness=1,
                         font=("Segoe UI", 10), width=15)
entry_med_rec_id.config(highlightbackground=INPUT_BORDER)
entry_med_rec_id.grid(row=1, column=1, sticky="w", pady=(0, 8))

def med_field(lbl, r, c, width=25):
    Label(med_edit_inner, text=lbl,
          bg=CARD_BG, fg=TEXT_SECONDARY,
          font=("Segoe UI", 10, "bold")).grid(row=r, column=c*2,
                                              sticky="w", pady=(0, 4), padx=(0, 8))
    e = Entry(med_edit_inner,
              bg=INPUT_BG, fg=TEXT_PRIMARY,
              relief="solid", bd=1,
              highlightcolor=INPUT_FOCUS,
              highlightthickness=1,
              font=("Segoe UI", 10), width=width)
    e.config(highlightbackground=INPUT_BORDER)
    e.grid(row=r, column=c*2 + 1, sticky="we", pady=(0, 8))
    return e

entry_med_pet   = med_field("Pet ID",           2, 0, width=10)
entry_med_type  = med_field("Diagnosis / Type", 2, 1)
entry_med_med   = med_field("Medication",       3, 0)
entry_med_vet   = med_field("Vet Staff ID",     3, 1, width=10)
entry_med_date  = med_field("Date (YYYY-MM-DD)",4, 0)
entry_med_notes = med_field("Notes",            4, 1, width=40)

def clear_med_form():
    med_rec_id_var.set("")
    for e in (entry_med_pet, entry_med_type, entry_med_med,
              entry_med_vet, entry_med_date, entry_med_notes):
        e.delete(0, END)

def add_med_record():
    try:
        pet_id = entry_med_pet.get().strip()
        if not pet_id:
            set_status("Error: Pet ID required.")
            return

        r_type = entry_med_type.get().strip() or None
        med    = entry_med_med.get().strip() or None
        vet_id = entry_med_vet.get().strip() or None
        date   = entry_med_date.get().strip() or None
        notes  = entry_med_notes.get().strip() or None

        sql = """
            INSERT INTO medical_record
            (type, date, medication, vet_staff_id, description, pet_id)
            VALUES (%s,%s,%s,%s,%s,%s)
        """
        vals = (r_type, date, med, vet_id or None, notes, pet_id)
        cursor.execute(sql, vals)
        connection.commit()
        set_status("Added medical record.")
        clear_med_form()
        refresh_medical_table()
    except Exception as e:
        set_status(f"Medical add error: {e}")

def update_med_record():
    rid = med_rec_id_var.get().strip()
    if not rid:
        set_status("Error: enter Record ID to update.")
        return
    try:
        cursor.execute("SELECT record_id FROM medical_record WHERE record_id=%s", (rid,))
        if cursor.fetchone() is None:
            set_status("No record found with that ID.")
            return

        pet_id = entry_med_pet.get().strip() or None
        r_type = entry_med_type.get().strip() or None
        med    = entry_med_med.get().strip() or None
        vet_id = entry_med_vet.get().strip() or None
        date   = entry_med_date.get().strip() or None
        notes  = entry_med_notes.get().strip() or None

        sql = """
            UPDATE medical_record
            SET type=%s, date=%s, medication=%s,
                vet_staff_id=%s, description=%s, pet_id=%s
            WHERE record_id=%s
        """
        vals = (r_type, date, med, vet_id, notes, pet_id, rid)
        cursor.execute(sql, vals)
        connection.commit()
        set_status(f"Updated medical record {rid}.")
        clear_med_form()
        refresh_medical_table()
    except Exception as e:
        set_status(f"Medical update error: {e}")

def delete_med_record():
    rid = med_rec_id_var.get().strip()
    if not rid:
        set_status("Error: enter Record ID to delete.")
        return
    try:
        cursor.execute("DELETE FROM medical_record WHERE record_id=%s", (rid,))
        connection.commit()
        if cursor.rowcount == 0:
            set_status("No record found with that ID.")
        else:
            set_status(f"Deleted medical record {rid}.")
        clear_med_form()
        refresh_medical_table()
    except Exception as e:
        set_status(f"Medical delete error: {e}")


med_btn_row = Frame(med_edit_inner, bg=CARD_BG)
med_btn_row.grid(row=5, column=0, columnspan=4,
                 sticky="e", pady=(12, 0))

Button(med_btn_row, text="Add Record", command=add_med_record,
       bg=ACCENT, fg="white",
       activebackground=ACCENT_HOVER,
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(med_btn_row, text="Update Record", command=update_med_record,
       bg=SUCCESS, fg="white",
       activebackground="#28A745",
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(med_btn_row, text="Delete Record", command=delete_med_record,
       bg=DANGER, fg="white",
       activebackground="#E02020",
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(med_btn_row, text="Clear", command=clear_med_form,
       bg=CARD_BG, fg=TEXT_PRIMARY,
       activebackground=BG,
       relief="solid", bd=1,
       padx=16, pady=8,
       font=("Segoe UI", 10),
       cursor="hand2").pack(side=LEFT)


def on_med_select(event):
    sel = medical_table.focus()
    if not sel:
        return
    vals = medical_table.item(sel, "values")
    # (RecordID, PetID, PetName, Type, Medication, Vet, Date, Notes)
    med_rec_id_var.set(str(vals[0]))
    entry_med_pet.delete(0, END)
    entry_med_pet.insert(0, str(vals[1]))
    entry_med_type.delete(0, END)
    entry_med_type.insert(0, vals[3] or "")
    entry_med_med.delete(0, END)
    entry_med_med.insert(0, vals[4] or "")
    entry_med_date.delete(0, END)
    entry_med_date.insert(0, vals[6] or "")
    entry_med_notes.delete(0, END)
    entry_med_notes.insert(0, vals[7] or "")

medical_table.bind("<<TreeviewSelect>>", on_med_select)



# ---------- STAFF DETAILS FRAME ----------
staff_frame = Frame(content, bg=BG)
staff_frame.grid(row=0, column=0, sticky="nsew")
frames["staff"] = staff_frame

Label(staff_frame, text="Staff Details",
      bg=BG, fg=TEXT_PRIMARY, font=("Segoe UI", 24, "bold")
).pack(anchor="w", padx=40, pady=(30, 20))

# Scrollable container
st_canvas = Canvas(staff_frame, bg=BG, highlightthickness=0)
st_vbar = Scrollbar(staff_frame, orient=VERTICAL, command=st_canvas.yview)
st_canvas.configure(yscrollcommand=st_vbar.set)
st_canvas.pack(side=LEFT, fill=BOTH, expand=True)
st_vbar.pack(side=RIGHT, fill=Y)

st_scrollable = Frame(st_canvas, bg=BG)
st_scrollable.bind("<Configure>", lambda e: st_canvas.configure(scrollregion=st_canvas.bbox("all")))
st_win = st_canvas.create_window((0, 0), window=st_scrollable, anchor="nw")
st_canvas.bind("<Configure>", lambda e: st_canvas.itemconfig(st_win, width=e.width))

# Header card
st_hdr = Frame(st_scrollable, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
st_hdr.pack(fill=X, padx=40, pady=(0, 20))
Frame(st_hdr, bg=CARD_BG).pack(fill=X, padx=24, pady=16)
Label(st_hdr, text="(Secure) View of Staff",
      bg=CARD_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=24, pady=(0, 2))
Label(st_hdr, text="Access is password-protected for this session.",
      bg=CARD_BG, fg=TEXT_SECONDARY, font=("Segoe UI", 10)
).pack(anchor="w", padx=24, pady=(0, 14))

# Table section
st_tbl_section = Frame(st_scrollable, bg=BG)
st_tbl_section.pack(fill=BOTH, expand=True, padx=40, pady=(0, 30))

Label(st_tbl_section, text="Staff", bg=BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 11, "bold")
).pack(anchor="w", pady=(0, 12))

st_tbl_container = Frame(st_tbl_section, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
st_tbl_container.pack(fill=BOTH, expand=True)

st_columns = ("StaffID", "Name", "Role", "Branch", "Phone", "Email")
staff_table = ttk.Treeview(st_tbl_container, columns=st_columns, show="headings", height=14)
for col, w in zip(st_columns, (80, 220, 150, 200, 140, 240)):
    staff_table.heading(col, text=col)
    staff_table.column(col, anchor="w", width=w)

st_scrollbar = Scrollbar(st_tbl_container, orient=VERTICAL, command=staff_table.yview)
staff_table.configure(yscrollcommand=st_scrollbar.set)
staff_table.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
st_scrollbar.pack(side=RIGHT, fill=Y)

# --- STAFF EDITING HELPERS ---

def refresh_staff_table():
    try:
        cursor.execute("""
            SELECT s.staff_id,
                   CONCAT(s.first_name, ' ', s.last_name) AS name,
                   s.role,
                   b.branch_name AS branch,
                   s.phone,
                   s.email
            FROM staff s
            LEFT JOIN shelter_branch b ON b.branch_id = s.shelter_branch_id
            ORDER BY s.staff_id
        """)
        rows = cursor.fetchall()

        cleaned = []
        for r in rows:
            r = list(r)
            # branch at index 3
            if r[3] is None:
                r[3] = ""
            cleaned.append(tuple(r))

        update_table(staff_table, cleaned)
        set_status(f"Staff: {len(cleaned)} row(s)")
    except Exception as e:
        update_table(staff_table, [])
        set_status(f"Staff: query error: {e}")

# ----- STAFF EDIT FORM (ADD / UPDATE / DELETE) -----

staff_edit_card = Frame(st_scrollable, bg=CARD_BG,
                        highlightthickness=1, highlightbackground=BORDER)
staff_edit_card.pack(fill=X, padx=40, pady=(0, 30))

staff_edit_inner = Frame(staff_edit_card, bg=CARD_BG)
staff_edit_inner.pack(fill=BOTH, padx=24, pady=20)

Label(staff_edit_inner, text="Edit Staff (Admin / Manager)",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=4,
                                           sticky="w", pady=(0, 16))

def make_field(lbl, r, c, width=25):
    Label(staff_edit_inner, text=lbl,
          bg=CARD_BG, fg=TEXT_SECONDARY,
          font=("Segoe UI", 10, "bold")).grid(row=r, column=c*2,
                                              sticky="w", pady=(0, 4), padx=(0, 8))
    e = Entry(staff_edit_inner,
              bg=INPUT_BG, fg=TEXT_PRIMARY,
              relief="solid", bd=1,
              highlightcolor=INPUT_FOCUS,
              highlightthickness=1,
              font=("Segoe UI", 10), width=width)
    e.config(highlightbackground=INPUT_BORDER)
    e.grid(row=r, column=c*2 + 1, sticky="we", pady=(0, 8))
    return e

staff_id_var = StringVar()
Label(staff_edit_inner, text="Staff ID (for update / delete)",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).grid(row=1, column=0,
                                          sticky="w", pady=(0, 4), padx=(0, 8))
entry_staff_id = Entry(staff_edit_inner,
                       textvariable=staff_id_var,
                       bg=INPUT_BG, fg=TEXT_PRIMARY,
                       relief="solid", bd=1,
                       highlightcolor=INPUT_FOCUS,
                       highlightthickness=1,
                       font=("Segoe UI", 10), width=15)
entry_staff_id.config(highlightbackground=INPUT_BORDER)
entry_staff_id.grid(row=1, column=1, sticky="w", pady=(0, 8))

entry_staff_fname = make_field("First Name", 2, 0)
entry_staff_lname = make_field("Last Name", 2, 1)
entry_staff_email = make_field("Email", 3, 0)
entry_staff_phone = make_field("Phone", 3, 1)
entry_staff_role  = make_field("Role (title)", 4, 0)
entry_staff_ssn   = make_field("SSN (###-##-####)", 4, 1)
entry_staff_hire  = make_field("Hire Date (YYYY-MM-DD)", 5, 0)

Label(staff_edit_inner, text="Branch ID",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).grid(row=5, column=2,
                                          sticky="w", pady=(0, 4), padx=(0, 8))
entry_staff_branch = Entry(staff_edit_inner,
                           bg=INPUT_BG, fg=TEXT_PRIMARY,
                           relief="solid", bd=1,
                           highlightcolor=INPUT_FOCUS,
                           highlightthickness=1,
                           font=("Segoe UI", 10), width=10)
entry_staff_branch.config(highlightbackground=INPUT_BORDER)
entry_staff_branch.grid(row=5, column=3, sticky="w", pady=(0, 8))

def clear_staff_form():
    staff_id_var.set("")
    for e in (entry_staff_fname, entry_staff_lname, entry_staff_email,
              entry_staff_phone, entry_staff_role, entry_staff_ssn,
              entry_staff_hire, entry_staff_branch):
        e.delete(0, END)

def add_staff():
    try:
        first = entry_staff_fname.get().strip()
        last  = entry_staff_lname.get().strip()
        email = entry_staff_email.get().strip()
        phone = entry_staff_phone.get().strip()
        role  = entry_staff_role.get().strip()
        ssn   = entry_staff_ssn.get().strip()
        hire  = entry_staff_hire.get().strip()
        branch_id = entry_staff_branch.get().strip()

        if not first or not last or not email or not ssn:
            set_status("Error: first, last, email, SSN required.")
            return

        sql = """
            INSERT INTO staff
            (first_name, last_name, email, phone, role, hire_date, ssn, shelter_branch_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        vals = (first, last, email, phone or None, role or None,
                hire or None, ssn, branch_id or None)
        cursor.execute(sql, vals)
        connection.commit()
        set_status(f"Added staff '{first} {last}'.")
        clear_staff_form()
        refresh_staff_table()
    except Exception as e:
        set_status(f"Staff add error: {e}")

def update_staff():
    sid = staff_id_var.get().strip()
    if not sid:
        set_status("Error: enter Staff ID to update.")
        return
    try:
        cursor.execute("SELECT staff_id FROM staff WHERE staff_id=%s", (sid,))
        if cursor.fetchone() is None:
            set_status("No staff found with that ID.")
            return

        first = entry_staff_fname.get().strip() or None
        last  = entry_staff_lname.get().strip() or None
        email = entry_staff_email.get().strip() or None
        phone = entry_staff_phone.get().strip() or None
        role  = entry_staff_role.get().strip() or None
        ssn   = entry_staff_ssn.get().strip() or None
        hire  = entry_staff_hire.get().strip() or None
        branch_id = entry_staff_branch.get().strip() or None

        sql = """
            UPDATE staff
            SET first_name=%s, last_name=%s, email=%s, phone=%s,
                role=%s, hire_date=%s, ssn=%s, shelter_branch_id=%s
            WHERE staff_id=%s
        """
        vals = (first, last, email, phone, role, hire, ssn, branch_id, sid)
        cursor.execute(sql, vals)
        connection.commit()
        set_status(f"Updated staff ID {sid}.")
        clear_staff_form()
        refresh_staff_table()
    except Exception as e:
        set_status(f"Staff update error: {e}")

def delete_staff():
    sid = staff_id_var.get().strip()
    if not sid:
        set_status("Error: enter Staff ID to delete.")
        return
    try:
        cursor.execute("DELETE FROM staff WHERE staff_id=%s", (sid,))
        connection.commit()
        if cursor.rowcount == 0:
            set_status("No staff found with that ID.")
        else:
            set_status(f"Deleted staff ID {sid}.")
        clear_staff_form()
        refresh_staff_table()
    except Exception as e:
        set_status(f"Staff delete error: {e}")

btn_row = Frame(staff_edit_inner, bg=CARD_BG)
btn_row.grid(row=6, column=0, columnspan=4,
             sticky="e", pady=(12, 0))

Button(btn_row, text="Add Staff", command=add_staff,
       bg=ACCENT, fg="white",
       activebackground=ACCENT_HOVER,
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(btn_row, text="Update Staff", command=update_staff,
       bg=SUCCESS, fg="white",
       activebackground="#28A745",
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(btn_row, text="Delete Staff", command=delete_staff,
       bg=DANGER, fg="white",
       activebackground="#E02020",
       relief="flat", padx=16, pady=8,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(btn_row, text="Clear", command=clear_staff_form,
       bg=CARD_BG, fg=TEXT_PRIMARY,
       activebackground=BG,
       relief="solid", bd=1, padx=16, pady=8,
       font=("Segoe UI", 10),
       cursor="hand2").pack(side=LEFT)


def on_staff_select(event):
    sel = staff_table.focus()
    if not sel:
        return
    vals = staff_table.item(sel, "values")
    staff_id = vals[0]
    staff_id_var.set(str(staff_id))
    
    # Fetch full record from database (including SSN, hire_date, branch_id)
    try:
        cursor.execute("""
            SELECT first_name, last_name, email, phone, role, ssn, hire_date, shelter_branch_id
            FROM STAFF WHERE staff_id = %s
        """, (staff_id,))
        row = cursor.fetchone()
        if row:
            first_name, last_name, email, phone, role, ssn, hire_date, branch_id = row
            
            entry_staff_fname.delete(0, END)
            entry_staff_fname.insert(0, first_name or "")
            entry_staff_lname.delete(0, END)
            entry_staff_lname.insert(0, last_name or "")
            entry_staff_email.delete(0, END)
            entry_staff_email.insert(0, email or "")
            entry_staff_phone.delete(0, END)
            entry_staff_phone.insert(0, phone or "")
            entry_staff_role.delete(0, END)
            entry_staff_role.insert(0, role or "")
            entry_staff_ssn.delete(0, END)
            entry_staff_ssn.insert(0, ssn or "")
            entry_staff_hire.delete(0, END)
            entry_staff_hire.insert(0, str(hire_date) if hire_date else "")
            entry_staff_branch.delete(0, END)
            entry_staff_branch.insert(0, str(branch_id) if branch_id else "")
    except Exception as e:
        set_status(f"Error loading staff details: {e}")

staff_table.bind("<<TreeviewSelect>>", on_staff_select)





def truncate_after_county(name: str) -> str:
    if not name:
        return ""
    s = str(name)
    i = s.lower().find("county")
    if i != -1:
        return s[: i + len("County")].strip()   # keep “…County”
    return s

def create_nav_button(text, command):
    btn = Button(sidebar,
                 text=text,
                 anchor="w",
                 relief="flat",
                 bd=0,
                 padx=24,
                 pady=14,
                 font=("Segoe UI", 11),
                 bg=SIDEBAR_BG,
                 fg=SIDEBAR_TEXT_INACTIVE,
                 activebackground=SIDEBAR_BORDER,
                 activeforeground=SIDEBAR_TEXT,
                 cursor="hand2")
    btn.config(command=command)
    btn.pack(fill=X, padx=8, pady=2)
    return btn


def set_active_button(active_key):
    for key, btn in sidebar_buttons.items():
        if key == active_key:
            btn.config(bg=ACCENT, fg=SIDEBAR_TEXT, font=("Segoe UI", 11, "bold"))
        else:
            btn.config(bg=SIDEBAR_BG, fg=SIDEBAR_TEXT_INACTIVE, font=("Segoe UI", 11))



# ---------- DASHBOARD FRAME ----------
dashboard_frame = Frame(content, bg=BG)
dashboard_frame.grid(row=0, column=0, sticky="nsew")
frames["dashboard"] = dashboard_frame

# Title
dash_title = Label(dashboard_frame,
                   text="Dashboard",
                   bg=BG, fg=TEXT_PRIMARY,
                   font=("Segoe UI", 24, "bold"))
dash_title.pack(anchor="w", padx=40, pady=(30, 20))

# Summary cards row
summary_frame = Frame(dashboard_frame, bg=BG)
summary_frame.pack(fill=X, padx=40, pady=(0, 20))

def make_summary_card(parent, title, color=ACCENT):
    card = Frame(parent, bg=CARD_BG, bd=0,
                 highlightthickness=1, highlightbackground=BORDER)
    card.pack(side=LEFT, padx=10, pady=0, ipadx=28, ipady=20, fill=BOTH, expand=True)
    
    Label(card, text=title, bg=CARD_BG, fg=TEXT_SECONDARY,
          font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 8))
    
    val_label = Label(card, text="0", bg=CARD_BG, fg=color,
                      font=("Segoe UI", 32, "bold"))
    val_label.pack(anchor="w")
    return val_label

total_label_val = make_summary_card(summary_frame, "Total Pets", TEXT_PRIMARY)
cats_label_val = make_summary_card(summary_frame, "Cats", ACCENT)
dogs_label_val = make_summary_card(summary_frame, "Dogs", SUCCESS)
others_label_val = make_summary_card(summary_frame, "Others", WARNING)

# Branch summary section
branch_section = Frame(dashboard_frame, bg=BG)
branch_section.pack(fill=X, padx=40, pady=(0, 20))

Label(branch_section, text="Branches", bg=BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

branch_cards_frame = Frame(branch_section, bg=BG)
branch_cards_frame.pack(fill=X)

# Dashboard table section
table_section = Frame(dashboard_frame, bg=BG)
table_section.pack(fill=BOTH, expand=True, padx=40, pady=(0, 30))

Label(table_section, text="Recent Pets", bg=BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

table_container_dash = Frame(table_section, bg=CARD_BG, 
                             highlightthickness=1, highlightbackground=BORDER)
table_container_dash.pack(fill=BOTH, expand=True)

columns = ("ID", "Name", "Species", "Breed", "Age", "BranchID")
pet_table_dashboard = ttk.Treeview(table_container_dash,
                                   columns=columns,
                                   show="headings")

for col in columns:
    pet_table_dashboard.heading(col, text=col)
    pet_table_dashboard.column(col, anchor="w", width=120)

scroll_dash = Scrollbar(table_container_dash,
                        orient=VERTICAL,
                        command=pet_table_dashboard.yview)
pet_table_dashboard.configure(yscrollcommand=scroll_dash.set)

pet_table_dashboard.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
scroll_dash.pack(side=RIGHT, fill=Y)


# ---------- ADD PET FRAME ----------
add_frame = Frame(content, bg=BG)
add_frame.grid(row=0, column=0, sticky="nsew")
frames["add"] = add_frame

# Create scrollable container for Add Pet
add_canvas = Canvas(add_frame, bg=BG, highlightthickness=0)
add_scrollbar = Scrollbar(add_frame, orient=VERTICAL, command=add_canvas.yview)
add_canvas.configure(yscrollcommand=add_scrollbar.set)

add_canvas.pack(side=LEFT, fill=BOTH, expand=True)
add_scrollbar.pack(side=RIGHT, fill=Y)

add_scrollable_frame = Frame(add_canvas, bg=BG)
add_scrollable_frame.bind(
    "<Configure>",
    lambda e: add_canvas.configure(scrollregion=add_canvas.bbox("all"))
)

add_canvas_frame = add_canvas.create_window((0, 0), window=add_scrollable_frame, anchor="nw")

def resize_add_frame(event):
    add_canvas.itemconfig(add_canvas_frame, width=event.width)
add_canvas.bind("<Configure>", resize_add_frame)

# Title
Label(add_scrollable_frame, text="Add New Pet",
      bg=BG, fg=TEXT_PRIMARY,
      font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=40, pady=(30, 20))

# Form container with card styling
form_container = Frame(add_scrollable_frame, bg=CARD_BG, highlightthickness=1, 
                       highlightbackground=BORDER)
form_container.pack(fill=X, padx=40, pady=(0, 20), ipady=20)

form = Frame(form_container, bg=CARD_BG)
form.pack(fill=X, padx=30, pady=20)

def labeled_entry(parent, label_text, is_large=False):
    wrapper = Frame(parent, bg=CARD_BG)
    wrapper.pack(fill=X, pady=10)
    
    Label(wrapper, text=label_text,
          bg=CARD_BG, fg=TEXT_SECONDARY,
          font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
    
    entry = Entry(wrapper, bg=INPUT_BG, fg=TEXT_PRIMARY,
                  relief="solid", bd=1,
                  highlightcolor=INPUT_FOCUS,
                  highlightthickness=1,
                  font=("Segoe UI", 11))
    entry.config(highlightbackground=INPUT_BORDER)
    entry.pack(fill=X, ipady=10)
    return entry

entry_name = labeled_entry(form, "Pet Name *")
entry_species = labeled_entry(form, "Species *")

# Two column layout for gender and breed
row1 = Frame(form, bg=CARD_BG)
row1.pack(fill=X, pady=10)

col1 = Frame(row1, bg=CARD_BG)
col1.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
col2 = Frame(row1, bg=CARD_BG)
col2.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

Label(col1, text="Gender", bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
entry_gender = Entry(col1, bg=INPUT_BG, fg=TEXT_PRIMARY,
                    relief="solid", bd=1,
                    highlightcolor=INPUT_FOCUS,
                    highlightthickness=1,
                    font=("Segoe UI", 11))
entry_gender.config(highlightbackground=INPUT_BORDER)
entry_gender.pack(fill=X, ipady=10)

Label(col2, text="Breed", bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
entry_breed = Entry(col2, bg=INPUT_BG, fg=TEXT_PRIMARY,
                   relief="solid", bd=1,
                   highlightcolor=INPUT_FOCUS,
                   highlightthickness=1,
                   font=("Segoe UI", 11))
entry_breed.config(highlightbackground=INPUT_BORDER)
entry_breed.pack(fill=X, ipady=10)

# Two column layout for age and arrival
row2 = Frame(form, bg=CARD_BG)
row2.pack(fill=X, pady=10)

col3 = Frame(row2, bg=CARD_BG)
col3.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
col4 = Frame(row2, bg=CARD_BG)
col4.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

Label(col3, text="Age", bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
entry_age = Entry(col3, bg=INPUT_BG, fg=TEXT_PRIMARY,
                 relief="solid", bd=1,
                 highlightcolor=INPUT_FOCUS,
                 highlightthickness=1,
                 font=("Segoe UI", 11))
entry_age.config(highlightbackground=INPUT_BORDER)
entry_age.pack(fill=X, ipady=10)

Label(col4, text="Arrival Date (YYYY-MM-DD)", bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
entry_arrival = Entry(col4, bg=INPUT_BG, fg=TEXT_PRIMARY,
                     relief="solid", bd=1,
                     highlightcolor=INPUT_FOCUS,
                     highlightthickness=1,
                     font=("Segoe UI", 11))
entry_arrival.config(highlightbackground=INPUT_BORDER)
entry_arrival.pack(fill=X, ipady=10)

entry_description = labeled_entry(form, "Description")

# Branch combobox
branch_wrap = Frame(form, bg=CARD_BG)
branch_wrap.pack(fill=X, pady=10)
Label(branch_wrap, text="Shelter Branch",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
branch_var = StringVar()
entry_branch = ttk.Combobox(branch_wrap,
                            textvariable=branch_var,
                            state="readonly",
                            font=("Segoe UI", 11))
entry_branch["values"] = list(branch_options.keys())
entry_branch.pack(fill=X, ipady=8)

# Button row
button_row = Frame(add_scrollable_frame, bg=BG)
button_row.pack(fill=X, padx=40, pady=(0, 20))

btn_add = Button(button_row,
                 text="Add Pet",
                 command=add_pet,
                 bg=ACCENT,
                 fg="#000000",
                 activebackground=ACCENT_HOVER,
                 activeforeground="white",
                 relief="flat",
                 padx=32, pady=12,
                 font=("Segoe UI", 11, "bold"),
                 cursor="hand2")
btn_add.pack(side=LEFT, padx=(0, 10))

btn_clear = Button(button_row,
                  text="Clear",
                  command=clear_fields,
                  bg=CARD_BG,
                  fg=TEXT_PRIMARY,
                  activebackground=BG,
                  activeforeground=TEXT_PRIMARY,
                  relief="solid",
                  bd=1,
                  padx=32, pady=12,
                  font=("Segoe UI", 11),
                  cursor="hand2")
btn_clear.pack(side=LEFT)


# ----- MANAGE PETS FRAME -----
manage_frame = Frame(content, bg=BG)
manage_frame.grid(row=0, column=0, sticky="nsew")
frames["manage"] = manage_frame

Label(manage_frame, text="Manage Pets",
      bg=BG, fg=TEXT_PRIMARY,
      font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=40, pady=(30, 20))

# Create scrollable container
canvas = Canvas(manage_frame, bg=BG, highlightthickness=0)
scrollbar = Scrollbar(manage_frame, orient=VERTICAL, command=canvas.yview)

canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.pack(side=RIGHT, fill=Y)

scrollable_frame = Frame(canvas, bg=BG)
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def resize_inner_frame(event):
    canvas.itemconfig(canvas_frame, width=event.width)
canvas.bind("<Configure>", resize_inner_frame)

# Search section with card styling
search_card = Frame(scrollable_frame, bg=CARD_BG, highlightthickness=1,
                   highlightbackground=BORDER)
search_card.pack(fill=X, padx=40, pady=(0, 20))

search_inner = Frame(search_card, bg=CARD_BG)
search_inner.pack(fill=X, padx=24, pady=20)

Label(search_inner, text="Search Pets", bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

search_row = Frame(search_inner, bg=CARD_BG)
search_row.pack(fill=X)

entry_search = Entry(search_row,
                     bg=INPUT_BG, fg=TEXT_PRIMARY,
                     relief="solid", bd=1,
                     highlightcolor=INPUT_FOCUS,
                     highlightthickness=1,
                     font=("Segoe UI", 11))
entry_search.config(highlightbackground=INPUT_BORDER)
entry_search.pack(side=LEFT, fill=X, expand=True, ipady=10, padx=(0, 10))

Button(search_row, text="Search",
       command=search_pets,
       bg=ACCENT, fg="#000000",
       activebackground=ACCENT_HOVER,
       activeforeground="white",
       relief="flat",
       padx=24, pady=10,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(side=LEFT, padx=(0, 8))

Button(search_row, text="Refresh",
       command=refresh_manage_table,
       bg=CARD_BG, fg=TEXT_PRIMARY,
       activebackground=BG,
       activeforeground=TEXT_PRIMARY,
       relief="solid", bd=1,
       padx=24, pady=10,
       font=("Segoe UI", 10),
       cursor="hand2").pack(side=LEFT)

# Table section
table_section = Frame(scrollable_frame, bg=BG)
table_section.pack(fill=BOTH, expand=True, padx=40, pady=(0, 20))

Label(table_section, text="All Pets", bg=BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

table_container = Frame(table_section, bg=CARD_BG, 
                       highlightthickness=1, highlightbackground=BORDER)
table_container.pack(fill=BOTH, expand=True)

pet_table_manage = ttk.Treeview(table_container,
                                columns=columns,
                                show="headings",
                                height=12)
for col in columns:
    pet_table_manage.heading(col, text=col)
    pet_table_manage.column(col, anchor="w", width=120)

scroll_manage = Scrollbar(table_container,
                          orient=VERTICAL,
                          command=pet_table_manage.yview)
pet_table_manage.configure(yscrollcommand=scroll_manage.set)

pet_table_manage.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
scroll_manage.pack(side=RIGHT, fill=Y)

# Actions section - 2 columns
actions_row = Frame(scrollable_frame, bg=BG)
actions_row.pack(fill=X, padx=40, pady=(0, 30))

# Delete section
delete_card = Frame(actions_row, bg=CARD_BG, highlightthickness=1,
                   highlightbackground=BORDER)
delete_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

delete_inner = Frame(delete_card, bg=CARD_BG)
delete_inner.pack(fill=BOTH, padx=24, pady=20)

Label(delete_inner, text="Delete Pet",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 16))

Label(delete_inner, text="Pet ID",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

entry_delete_id = Entry(delete_inner,
                        bg=INPUT_BG, fg=TEXT_PRIMARY,
                        relief="solid", bd=1,
                        highlightcolor=INPUT_FOCUS,
                        highlightthickness=1,
                        font=("Segoe UI", 11))
entry_delete_id.config(highlightbackground=INPUT_BORDER)
entry_delete_id.pack(fill=X, ipady=10, pady=(0, 12))

Button(delete_inner, text="Delete Pet",
       command=delete_pet,
       bg=DANGER, fg="#000000",
       activebackground="#E02020",
       activeforeground="white",
       relief="flat",
       padx=24, pady=10,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(fill=X)

# Update section
update_card = Frame(actions_row, bg=CARD_BG, highlightthickness=1,
                   highlightbackground=BORDER)
update_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

update_inner = Frame(update_card, bg=CARD_BG)
update_inner.pack(fill=BOTH, padx=24, pady=20)

Label(update_inner, text="Update Pet",
      bg=CARD_BG, fg=TEXT_SECONDARY,
      font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 16))

def upd_field(label_text):
    Label(update_inner, text=label_text,
          bg=CARD_BG, fg=TEXT_SECONDARY,
          font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
    e = Entry(update_inner,
              bg=INPUT_BG, fg=TEXT_PRIMARY,
              relief="solid", bd=1,
              highlightcolor=INPUT_FOCUS,
              highlightthickness=1,
              font=("Segoe UI", 11))
    e.config(highlightbackground=INPUT_BORDER)
    e.pack(fill=X, ipady=10, pady=(0, 12))
    return e

entry_update_id = upd_field("Pet ID")
entry_upd_name = upd_field("Name")
entry_upd_age = upd_field("Age")
entry_upd_desc = upd_field("Description")

Button(update_inner, text="Update Pet",
       command=update_pet,
       bg=SUCCESS, fg="#000000",
       activebackground="#28A745",
       activeforeground="white",
       relief="flat",
       padx=24, pady=10,
       font=("Segoe UI", 10, "bold"),
       cursor="hand2").pack(fill=X)


# ---------- MOUSE WHEEL ----------
def _on_manage_mousewheel(event):
    if event.delta > 0:
        canvas.yview_scroll(-1, "units")
    else:
        canvas.yview_scroll(1, "units")

def _on_table_mousewheel(event):
    if event.delta > 0:
        pet_table_manage.yview_scroll(-1, "units")
    else:
        pet_table_manage.yview_scroll(1, "units")

def _on_add_mousewheel(event):
    if event.delta > 0:
        add_canvas.yview_scroll(-1, "units")
    else:
        add_canvas.yview_scroll(1, "units")

def bind_manage_mousewheel(_event):
    canvas.bind_all("<MouseWheel>", _on_manage_mousewheel)

def unbind_manage_mousewheel(_event):
    canvas.unbind_all("<MouseWheel>")

def bind_table_mousewheel(_event):
    canvas.unbind_all("<MouseWheel>")
    pet_table_manage.bind_all("<MouseWheel>", _on_table_mousewheel)

def unbind_table_mousewheel(_event):
    pet_table_manage.unbind_all("<MouseWheel>")
    canvas.bind_all("<MouseWheel>", _on_manage_mousewheel)

def bind_add_mousewheel(_event):
    add_canvas.bind_all("<MouseWheel>", _on_add_mousewheel)

def unbind_add_mousewheel(_event):
    add_canvas.unbind_all("<MouseWheel>")

# hook the enter/leave events
scrollable_frame.bind("<Enter>", bind_manage_mousewheel)
scrollable_frame.bind("<Leave>", unbind_manage_mousewheel)

pet_table_manage.bind("<Enter>", bind_table_mousewheel)
pet_table_manage.bind("<Leave>", unbind_table_mousewheel)

add_scrollable_frame.bind("<Enter>", bind_add_mousewheel)
add_scrollable_frame.bind("<Leave>", unbind_add_mousewheel)

# --- USER MANAGEMENT FRAME (ADMIN ONLY SECTION) ---
user_admin = init_user_management(content, connection)
frames["user_admin"] = user_admin["frame"]
refresh_user_admin = user_admin["refresh"]

# --- REPORTS FRAME (MANAGER / ADMIN) ---
reports = init_reports(content, connection, CURRENT_USER_ROLE)
frames["reports"] = reports["frame"]
refresh_reports = reports["refresh"]


# ---------- NAV BUTTONS ----------
def add_nav_if_allowed(key, label, callback):
    if can_access(CURRENT_USER_ROLE, key):
        sidebar_buttons[key] = create_nav_button(label, callback)

add_nav_if_allowed("dashboard", "📊  Dashboard",
                   lambda: show_frame("dashboard"))
add_nav_if_allowed("add", "➕  Add Pet",
                   lambda: show_frame("add"))
add_nav_if_allowed("manage", "⚙️  Manage Pets",
                   lambda: show_frame("manage"))
add_nav_if_allowed("medical", "🩺  Medical Records",
                   lambda: show_frame("medical"))
add_nav_if_allowed("staff", "👥  Staff Details",
                   lambda: show_frame("staff"))
add_nav_if_allowed("user_admin", "🛠  User Management",
                   lambda: show_frame("user_admin"))
add_nav_if_allowed("reports", "📈  Reports",
                   lambda: show_frame("reports"))



# --- PROFILE & LOGOUT BUTTONS AT BOTTOM ---
def logout():
    root.destroy()

profile_btn = Button(
    sidebar,
    text=f"👤  {CURRENT_USERNAME}",
    anchor="w",
    relief="flat",
    bd=0,
    padx=24,
    pady=10,
    font=("Segoe UI", 10),
    bg="#2C2C2E",
    fg="#000000",
    activebackground="#3A3A3C",
    activeforeground="#FFFFFF",
    cursor="hand2",
    command=lambda: open_change_password_dialog(root, connection, CURRENT_USER)
)
profile_btn.pack(side=BOTTOM, fill=X, padx=8, pady=(0, 2))

logout_btn = Button(
    sidebar,
    text="🚪  Logout",
    anchor="w",
    relief="flat",
    bd=0,
    padx=24,
    pady=10,
    font=("Segoe UI", 10),
    bg="#2C2C2E",
    fg="#000000",
    activebackground="#3A3A3C",
    activeforeground="#FFFFFF",
    cursor="hand2",
    command=logout
)
logout_btn.pack(side=BOTTOM, fill=X, padx=8, pady=(0, 16))                   


# ---------- STATUS BAR ----------
status_bar = Frame(root, bg=CARD_BG, highlightthickness=1,
                   highlightbackground=BORDER, highlightcolor=BORDER)
status_bar.pack(side=BOTTOM, fill=X)

status_label = Label(status_bar,
                     text="Ready",
                     bg=CARD_BG,
                     fg=TEXT_SECONDARY,
                     anchor="w",
                     font=("Segoe UI", 10))
status_label.pack(side=LEFT, padx=40, pady=10)

set_status(f"Logged in as {CURRENT_USERNAME} ({CURRENT_USER_ROLE})")

# ---------- INITIAL VIEW ----------
show_frame("dashboard")
refresh_dashboard()

root.mainloop()