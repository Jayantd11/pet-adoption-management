# reports_view.py - Reports & Analytics screen
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from matplotlib.ticker import MaxNLocator
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Keep theme consistent with main.py
BG = "#F5F5F7"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#86868B"
BORDER = "#E5E5EA"
ACCENT = "#007AFF"


def init_reports(content, connection, current_role):
    """
    Build the Reports & Analytics view.

    Parameters
    ----------
    content : tk.Frame
        Parent frame from main.py (the content area).
    connection : mysql.connector.MySQLConnection
        Open connection to the Pet_Adoption database.
    current_role : str
        Role of the logged-in user: 'admin', 'manager', 'staff', 'pending', etc.

    Returns
    -------
    dict with:
        "frame"   -> tk.Frame  (root frame for this view)
        "refresh" -> callable  (re-run queries and rebuild the UI)
    """

    # -------- Root frame --------
    frame = tk.Frame(content, bg=BG)
    frame.grid(row=0, column=0, sticky="nsew")

    # Title
    tk.Label(
        frame,
        text="Reports & Analytics",
        bg=BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 24, "bold"),
    ).pack(anchor="w", padx=40, pady=(30, 10))

    # -------- Scrollable region --------
    canvas = tk.Canvas(frame, bg=BG, highlightthickness=0, borderwidth=0)
    vbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    vbar.pack(side="right", fill="y")

    scrollable = tk.Frame(canvas, bg=BG)
    window_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")

    def _on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # keep inner frame width in sync with canvas width
        canvas.itemconfigure(window_id, width=event.width)

    canvas.bind("<Configure>", _on_configure)

    # ============================================================
    # Helper widgets
    # ============================================================

    def make_section(parent, title, subtitle=None):
        """Create a card-like section container."""
        section = tk.Frame(parent, bg=BG)
        section.pack(fill="x", padx=40, pady=(0, 25))

        tk.Label(
            section, text=title, bg=BG, fg=TEXT_PRIMARY,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                section, text=subtitle, bg=BG, fg=TEXT_SECONDARY,
                font=("Segoe UI", 10),
            ).pack(anchor="w", pady=(2, 8))

        card = tk.Frame(
            section,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        card.pack(fill="both", expand=True)
        return card

    def make_summary_card(parent, title, value):
        """Small KPI card used in the top summary row."""
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )
        card.pack(side="left", padx=10, ipadx=22, ipady=18, fill="both", expand=True)

        tk.Label(
            card,
            text=title,
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=16, pady=(0, 4))

        tk.Label(
            card,
            text=str(value),
            bg=CARD_BG,
            fg=ACCENT,
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w", padx=16)
        return card


    def build_bar_chart(parent, title, labels, values):
        """Render a simple matplotlib bar chart inside *parent*."""
        if not labels:
            tk.Label(
                parent,
                text="No data available for this report.",
                bg=CARD_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10, "italic"),
            ).pack(padx=16, pady=16, anchor="w")
            return

        fig = Figure(figsize=(5, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(range(len(labels)), values)  # Use numeric x-axis
        ax.set_title(title)
        
        # Set tick positions and labels
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        # Force y-axis to use integers only
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Call tight_layout AFTER setting labels
        fig.tight_layout()

        canvas_chart = FigureCanvasTkAgg(fig, master=parent)
        canvas_chart.draw()
        canvas_chart.get_tk_widget().pack(fill="both", expand=True)

    def build_table(parent, columns, rows, height=6):
        """Simple ttk.Treeview table for textual reports."""
        if not rows:
            tk.Label(
                parent,
                text="No rows to display.",
                bg=CARD_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10, "italic"),
            ).pack(padx=16, pady=16, anchor="w")
            return

        style = ttk.Style(parent)
        style.configure("Reports.Treeview", background=CARD_BG, fieldbackground=CARD_BG)

        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=height,
            style="Reports.Treeview",
        )
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="w", stretch=True, width=120)

        for row in rows:
            tree.insert("", "end", values=row)

    # ============================================================
    # Role specific builders
    # ============================================================

    def build_staff_reports(cur):
        # --- Pets by species (available only) ---
        card = make_section(
            scrollable,
            "Staff Report: Available Pets by Species",
            "Distribution of currently available pets, grouped by species.",
        )
        cur.execute(
            """
            SELECT COALESCE(species, 'Unknown') AS species, COUNT(*) AS total
            FROM PET
            WHERE adoption_status = 'Available'
            GROUP BY COALESCE(species, 'Unknown')
            ORDER BY total DESC
            """
        )
        rows = cur.fetchall()
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "Available pets by species", labels, values)

        # --- Available pets by branch ---
        card = make_section(
            scrollable,
            "Staff Report: Available Pets by Branch",
            "Helps staff see which branches have more animals to care for.",
        )
        # In build_staff_reports, for the branch chart:
        cur.execute(
            """
            SELECT b.branch_name, COUNT(p.pet_id) AS total
            FROM SHELTER_BRANCH b
            LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id
                            AND p.adoption_status = 'Available'
            GROUP BY b.branch_id, b.branch_name
            ORDER BY total DESC, b.branch_name
            """
        )
        rows = cur.fetchall()
        labels = [r[0].split()[0] for r in rows]  # Just the first word
        values = [r[1] for r in rows]
        build_bar_chart(card, "Available pets per branch", labels, values)

        # --- Recent medical records (last 30 days) ---
        card = make_section(
            scrollable,
            "Staff Report: Recent Medical Activity (Last 30 Days)",
            "Counts of medical records created in the last 30 days, grouped by type.",
        )
        cur.execute(
            """
            SELECT COALESCE(type, 'Unknown') AS type, COUNT(*) AS total
            FROM MEDICAL_RECORD
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY COALESCE(type, 'Unknown')
            ORDER BY total DESC
            """
        )
        rows = cur.fetchall()
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "Medical records (last 30 days)", labels, values)

    def build_manager_reports(cur):
        # --- Branch occupancy vs. capacity ---
        card = make_section(
            scrollable,
            "Manager Report: Branch Occupancy",
            "Compare number of pets at each branch against the stated capacity.",
        )
        cur.execute(
            """
            SELECT b.branch_name,
                   COUNT(p.pet_id) AS pets,
                   COALESCE(b.capacity, 0) AS capacity
            FROM SHELTER_BRANCH b
            LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id
            GROUP BY b.branch_id, b.branch_name, b.capacity
            ORDER BY b.branch_name
            """
        )
        rows = cur.fetchall()
        labels = [r[0].split()[0] for r in rows]  # Just the first word
        pets = [r[1] for r in rows]
        capacities = [r[2] for r in rows]

        if labels:
            # small two-series chart (pets vs capacity)
            fig = Figure(figsize=(5, 2.6), dpi=100)
            ax = fig.add_subplot(111)
            x = range(len(labels))
            ax.bar(x, capacities, label="Capacity", alpha=0.4)
            ax.bar(x, pets, label="Current pets")
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, rotation=25, ha="right")
            ax.set_title("Branch occupancy vs. capacity")
            ax.legend()
            fig.tight_layout()

            canvas_chart = FigureCanvasTkAgg(fig, master=card)
            canvas_chart.draw()
            canvas_chart.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(
                card,
                text="No branches defined in SHELTER_BRANCH.",
                bg=CARD_BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 10, "italic"),
            ).pack(padx=16, pady=16, anchor="w")

        # --- Adoption applications by status ---
        card = make_section(
            scrollable,
            "Manager Report: Adoption Pipeline",
            "Overview of adoption applications grouped by status.",
        )
        cur.execute(
            """
            SELECT COALESCE(status, 'Unknown') AS status, COUNT(*) AS total
            FROM ADOPTION_APPLICATION
            GROUP BY COALESCE(status, 'Unknown')
            ORDER BY total DESC
            """
        )
        rows = cur.fetchall()
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "Applications by status", labels, values)

        # --- Average pet age by species ---
        card = make_section(
            scrollable,
            "Manager Report: Average Pet Age by Species",
            "Helps plan long-term care and adoption strategies.",
        )
        cur.execute(
            """
            SELECT COALESCE(species, 'Unknown') AS species,
                   ROUND(AVG(age), 1) AS avg_age
            FROM PET
            WHERE age IS NOT NULL
            GROUP BY COALESCE(species, 'Unknown')
            ORDER BY avg_age DESC
            """
        )
        rows = cur.fetchall()
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "Average age (years)", labels, values)

    def build_admin_reports(cur):
        # --- Users by role ---
        card = make_section(
            scrollable,
            "Admin Report: User Accounts by Role",
            "Counts of login accounts in USER_ACCOUNT, grouped by role.",
        )
        try:
            cur.execute(
                """
                SELECT role, COUNT(*) AS total
                FROM USER_ACCOUNT
                GROUP BY role
                ORDER BY role
                """
            )
            rows = cur.fetchall()
        except mysql.connector.Error:
            rows = []

        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "User accounts by role", labels, values)

        # --- 5 most recent users ---
        card = make_section(
            scrollable,
            "Admin Report: Recently Created Users",
            "Most recent user accounts in the system.",
        )
        try:
            cur.execute(
                """
                SELECT username, role, created_at
                FROM USER_ACCOUNT
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            rows = cur.fetchall()
        except mysql.connector.Error:
            rows = []

        columns = ("Username", "Role", "Created")
        build_table(card, columns, rows, height=5)

    # ============================================================
    # Refresh logic – this is what main.py calls whenever the
    # Reports tab is opened.
    # ============================================================

    def refresh():
        # Clear any existing dynamic content
        for w in scrollable.winfo_children():
            w.destroy()

        try:
            cur = connection.cursor()

            # ----------- Top KPI summary row (same for all roles) -----------
            summary = tk.Frame(scrollable, bg=BG)
            summary.pack(fill="x", padx=40, pady=(0, 20))

            # Total pets
            cur.execute("SELECT COUNT(*) FROM PET")
            total_pets = cur.fetchone()[0] or 0

            # Available pets
            cur.execute("SELECT COUNT(*) FROM PET WHERE adoption_status = 'Available'")
            available_pets = cur.fetchone()[0] or 0

            # Adopted pets
            cur.execute("SELECT COUNT(*) FROM PET WHERE adoption_status = 'Adopted'")
            adopted_pets = cur.fetchone()[0] or 0

            # Total medical records
            cur.execute("SELECT COUNT(*) FROM MEDICAL_RECORD")
            total_med = cur.fetchone()[0] or 0

            # Total staff
            cur.execute("SELECT COUNT(*) FROM STAFF")
            total_staff = cur.fetchone()[0] or 0

            # Total branches
            cur.execute("SELECT COUNT(*) FROM SHELTER_BRANCH")
            total_branches = cur.fetchone()[0] or 0

            make_summary_card(summary, "Total Pets", total_pets)
            make_summary_card(summary, "Available", available_pets)
            make_summary_card(summary, "Adopted", adopted_pets)
            make_summary_card(summary, "Medical Records", total_med)
            make_summary_card(summary, "Staff", total_staff)
            make_summary_card(summary, "Branches", total_branches)

            # ----------- Role-based detail sections -----------
            role = (current_role or "").lower()

            if role == "admin":
                # Admin gets everything
                build_staff_reports(cur)
                build_manager_reports(cur)
                build_admin_reports(cur)
            elif role == "manager":
                build_manager_reports(cur)
                build_staff_reports(cur)
            elif role == "staff":
                build_staff_reports(cur)
            else:
                # Pending / unknown role – show an explanation
                msg_section = tk.Frame(scrollable, bg=BG)
                msg_section.pack(fill="x", padx=40, pady=(0, 30))

                tk.Label(
                    msg_section,
                    text="Limited access",
                    bg=BG,
                    fg=TEXT_PRIMARY,
                    font=("Segoe UI", 16, "bold"),
                ).pack(anchor="w")

                tk.Label(
                    msg_section,
                    text=(
                        "Your account does not have a staff, manager, or admin role, "
                        "so detailed reports are hidden.\n"
                        "Please contact an administrator if you believe this is an error."
                    ),
                    bg=BG,
                    fg=TEXT_SECONDARY,
                    justify="left",
                    font=("Segoe UI", 11),
                ).pack(anchor="w", pady=(4, 0))

        except mysql.connector.Error as e:
            messagebox.showerror("Reports Error", f"Could not load reports:\n{e}")
        finally:
            try:
                cur.close()
            except Exception:
                pass
    # Populate the reports on initial load
    try:
        refresh()
    except Exception as e:
        print(f"Error in refresh: {e}")
        import traceback
        traceback.print_exc()

    return {"frame": frame, "refresh": refresh}