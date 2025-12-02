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

    #Helper widgets

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
        style.configure("Reports.Treeview", background=CARD_BG, fieldbackground=CARD_BG,
                        rowheight=28, font=("Segoe UI", 10))
        style.configure("Reports.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Create a frame to hold treeview + scrollbar
        table_frame = tk.Frame(parent, bg=CARD_BG)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=height,
            style="Reports.Treeview",
        )
        
        # Add horizontal scrollbar for wide tables
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=h_scroll.set)
        
        tree.pack(side="top", fill="both", expand=True)
        h_scroll.pack(side="bottom", fill="x")

        # Calculate column widths based on content
        for col in columns:
            # Get max width needed for this column
            max_width = len(str(col)) * 10  # Header width estimate
            for row in rows:
                col_idx = columns.index(col) if isinstance(columns, tuple) else list(columns).index(col)
                cell_val = str(row[col_idx]) if col_idx < len(row) else ""
                cell_width = len(cell_val) * 9  # Content width estimate
                max_width = max(max_width, cell_width)
            
            # Set reasonable min/max bounds
            col_width = max(100, min(max_width + 20, 300))
            
            tree.heading(col, text=col, anchor="center")
            tree.column(col, anchor="center", width=col_width, minwidth=80, stretch=True)

        for row in rows:
            tree.insert("", "end", values=row)

    # Role specific builders

    def build_staff_reports(cur):
        # --- 1. Pets by species (available only) ---
        card = make_section(
            scrollable,
            "Staff Report 1: Available Pets by Species",
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

        # --- 2. Available pets by branch ---
        card = make_section(
            scrollable,
            "Staff Report 2: Available Pets by Branch",
            "Helps staff see which branches have more animals to care for.",
        )
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

        # --- 3. Recent medical records (last 30 days) ---
        card = make_section(
            scrollable,
            "Staff Report 3: Recent Medical Activity (Last 30 Days)",
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

        # --- 4. Pet Age Statistics (MIN, MAX, AVG, COUNT) ---
        card = make_section(
            scrollable,
            "Staff Report 4: Pet Age Statistics",
            "Age analysis of available pets - youngest, oldest, average",
        )
        cur.execute(
            """
            SELECT 
                MIN(age) AS youngest,
                MAX(age) AS oldest,
                ROUND(AVG(age), 1) AS avg_age,
                COUNT(*) AS total_pets
            FROM PET
            WHERE adoption_status = 'Available' AND age IS NOT NULL
            """
        )
        row = cur.fetchone()
        if row and row[3] > 0:
            stats_frame = tk.Frame(card, bg=CARD_BG)
            stats_frame.pack(fill="x", padx=20, pady=15)
            
            stats = [
                ("Youngest", f"{row[0]} yrs"),
                ("Oldest", f"{row[1]} yrs"),
                ("Average", f"{row[2]} yrs"),
                ("Total Pets", str(row[3]))
            ]
            for label, val in stats:
                stat_card = tk.Frame(stats_frame, bg="#F0F0F5", bd=1, relief="solid")
                stat_card.pack(side="left", padx=8, ipadx=18, ipady=12, fill="both", expand=True)
                tk.Label(stat_card, text=label, bg="#F0F0F5", fg=TEXT_SECONDARY,
                         font=("Segoe UI", 9, "bold")).pack()
                tk.Label(stat_card, text=val, bg="#F0F0F5", fg=ACCENT,
                         font=("Segoe UI", 16, "bold")).pack()
        else:
            tk.Label(card, text="No age data available.", bg=CARD_BG, fg=TEXT_SECONDARY,
                     font=("Segoe UI", 10, "italic")).pack(padx=16, pady=16, anchor="w")

        # --- 5. Medical Records per Pet (COUNT, MAX) ---
        card = make_section(
            scrollable,
            "Staff Report 5: Pets with Most Medical Records",
            "Identifies high-care animals needing attention.",
        )
        cur.execute(
            """
            SELECT p.name, p.species, COUNT(m.record_id) AS record_count
            FROM PET p
            LEFT JOIN MEDICAL_RECORD m ON p.pet_id = m.pet_id
            GROUP BY p.pet_id, p.name, p.species
            HAVING COUNT(m.record_id) > 0
            ORDER BY record_count DESC
            LIMIT 10
            """
        )
        rows = cur.fetchall()
        columns = ("Pet Name", "Species", "# Records")
        build_table(card, columns, rows, height=6)

    def build_manager_reports(cur):
        # --- 1. Adoption applications by status ---
        card = make_section(
            scrollable,
            "Manager Report 1: Adoption Pipeline",
            "Overview of adoption applications grouped by status. ",
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

        # --- 2. Average pet age by species ---
        card = make_section(
            scrollable,
            "Manager Report 2: Average Pet Age by Species",
            "Helps plan long-term care and adoption strategies. ",
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

        # --- 3. Staff Distribution by Branch (COUNT, SUM) ---
        card = make_section(
            scrollable,
            "Manager Report 3: Staff Distribution by Branch",
            "Number of staff members at each branch for resource planning. ",
        )
        cur.execute(
            """
            SELECT b.branch_name, COUNT(s.staff_id) AS staff_count
            FROM SHELTER_BRANCH b
            LEFT JOIN STAFF s ON s.shelter_branch_id = b.branch_id
            GROUP BY b.branch_id, b.branch_name
            ORDER BY staff_count DESC
            """
        )
        rows = cur.fetchall()
        labels = [r[0].split()[0] for r in rows]
        values = [r[1] for r in rows]
        build_bar_chart(card, "Staff per branch", labels, values)
        
        # Show total staff as summary
        cur.execute("SELECT COUNT(*) FROM STAFF")
        total = cur.fetchone()[0] or 0
        tk.Label(card, text=f"Total Staff (SUM): {total}", bg=CARD_BG, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(0, 10))

        # --- 4. Pet Age Range by Branch (MIN, MAX, AVG, COUNT) ---
        card = make_section(
            scrollable,
            "Manager Report 4: Pet Age Range by Branch",
            "Age statistics per branch for capacity and care planning. ",
        )
        cur.execute(
            """
            SELECT b.branch_name,
                   MIN(p.age) AS min_age,
                   MAX(p.age) AS max_age,
                   ROUND(AVG(p.age), 1) AS avg_age,
                   COUNT(p.pet_id) AS pet_count
            FROM SHELTER_BRANCH b
            LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id AND p.age IS NOT NULL
            GROUP BY b.branch_id, b.branch_name
            ORDER BY b.branch_name
            """
        )
        rows = cur.fetchall()
        columns = ("Branch", "Min Age", "Max Age", "Avg Age", "Pet Count")
        build_table(card, columns, rows, height=5)

        # --- 5. Longest Shelter Stays (MIN arrival_date, DATEDIFF) ---
        card = make_section(
            scrollable,
            "Manager Report 5: Longest Shelter Stays",
            "Available pets waiting longest for adoption - prioritize outreach.",
        )
        cur.execute(
            """
            SELECT p.name, p.species, p.arrival_date,
                   DATEDIFF(CURDATE(), p.arrival_date) AS days_in_shelter
            FROM PET p
            WHERE p.adoption_status = 'Available' AND p.arrival_date IS NOT NULL
            ORDER BY days_in_shelter DESC
            LIMIT 10
            """
        )
        rows = cur.fetchall()
        columns = ("Pet Name", "Species", "Arrival Date", "Days in Shelter")
        build_table(card, columns, rows, height=6)

    def build_admin_reports(cur):
        # --- 1. Users by role ---
        card = make_section(
            scrollable,
            "Admin Report 1: User Accounts by Role",
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

        # --- 2. Most recent users ---
        card = make_section(
            scrollable,
            "Admin Report 2: Recently Created Users",
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

        # --- 3. System-wide Pet Statistics (MIN, MAX, AVG, SUM, COUNT) ---
        card = make_section(
            scrollable,
            "Admin Report 3: System-wide Pet Statistics",
            "Comprehensive age analysis across all pets.",
        )
        cur.execute(
            """
            SELECT 
                COUNT(*) AS total_pets,
                MIN(age) AS min_age,
                MAX(age) AS max_age,
                ROUND(AVG(age), 1) AS avg_age,
                SUM(age) AS total_age_sum
            FROM PET
            WHERE age IS NOT NULL
            """
        )
        row = cur.fetchone()
        if row and row[0] > 0:
            stats_frame = tk.Frame(card, bg=CARD_BG)
            stats_frame.pack(fill="x", padx=20, pady=15)
            
            stats = [
                ("Total Pets", str(row[0]), "COUNT"),
                ("Youngest", f"{row[1]} yrs", "MIN"),
                ("Oldest", f"{row[2]} yrs", "MAX"),
                ("Average Age", f"{row[3]} yrs", "AVG"),
                ("Sum of Ages", f"{row[4]} yrs", "SUM")
            ]
            for label, val, agg in stats:
                stat_card = tk.Frame(stats_frame, bg="#F0F0F5", bd=1, relief="solid")
                stat_card.pack(side="left", padx=6, ipadx=14, ipady=10, fill="both", expand=True)
                tk.Label(stat_card, text=f"{label}", bg="#F0F0F5", fg=TEXT_SECONDARY,
                         font=("Segoe UI", 9, "bold")).pack()
                tk.Label(stat_card, text=val, bg="#F0F0F5", fg=ACCENT,
                         font=("Segoe UI", 14, "bold")).pack()
                tk.Label(stat_card, text=f"({agg})", bg="#F0F0F5", fg=TEXT_SECONDARY,
                         font=("Segoe UI", 8)).pack()
        else:
            tk.Label(card, text="No pet age data available.", bg=CARD_BG, fg=TEXT_SECONDARY,
                     font=("Segoe UI", 10, "italic")).pack(padx=16, pady=16, anchor="w")

        # --- 4. Medical Records Overview (COUNT, SUM, AVG) ---
        card = make_section(
            scrollable,
            "Admin Report 4: Medical Records Overview",
            "System-wide medical activity analysis.",
        )
        cur.execute(
            """
            SELECT COUNT(*) AS total_records,
                   COUNT(DISTINCT pet_id) AS pets_with_records,
                   ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT pet_id), 0), 1) AS avg_records_per_pet
            FROM MEDICAL_RECORD
            """
        )
        row = cur.fetchone()
        
        # Get busiest vet staff
        cur.execute(
            """
            SELECT CONCAT(s.first_name, ' ', s.last_name) AS vet_name, 
                   COUNT(m.record_id) AS record_count
            FROM MEDICAL_RECORD m
            JOIN STAFF s ON m.vet_staff_id = s.staff_id
            GROUP BY m.vet_staff_id, s.first_name, s.last_name
            ORDER BY record_count DESC
            LIMIT 5
            """
        )
        vet_rows = cur.fetchall()
        
        if row:
            stats_frame = tk.Frame(card, bg=CARD_BG)
            stats_frame.pack(fill="x", padx=20, pady=15)
            
            stats = [
                ("Total Records", str(row[0] or 0), "COUNT"),
                ("Pets with Records", str(row[1] or 0), "COUNT"),
                ("Avg per Pet", str(row[2] or 0), "AVG")
            ]
            for label, val, agg in stats:
                stat_card = tk.Frame(stats_frame, bg="#F0F0F5", bd=1, relief="solid")
                stat_card.pack(side="left", padx=8, ipadx=18, ipady=12, fill="both", expand=True)
                tk.Label(stat_card, text=label, bg="#F0F0F5", fg=TEXT_SECONDARY,
                         font=("Segoe UI", 9, "bold")).pack()
                tk.Label(stat_card, text=val, bg="#F0F0F5", fg=ACCENT,
                         font=("Segoe UI", 16, "bold")).pack()
                tk.Label(stat_card, text=f"({agg})", bg="#F0F0F5", fg=TEXT_SECONDARY,
                         font=("Segoe UI", 8)).pack()
        
        # Busiest vets table
        if vet_rows:
            tk.Label(card, text="Busiest Veterinary Staff (by record count):", bg=CARD_BG, 
                     fg=TEXT_SECONDARY, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(10, 5))
            columns = ("Staff Name", "Records Handled")
            build_table(card, columns, vet_rows, height=4)

        # --- 5. Branch Capacity Utilization (COUNT, SUM, AVG) ---
        card = make_section(
            scrollable,
            "Admin Report 5: Branch Capacity Utilization",
            "System-wide capacity analysis across all branches.",
        )
        cur.execute(
            """
            SELECT b.branch_name,
                   COUNT(p.pet_id) AS current_pets,
                   b.capacity,
                   ROUND(COUNT(p.pet_id) * 100.0 / NULLIF(b.capacity, 0), 1) AS utilization_pct
            FROM SHELTER_BRANCH b
            LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id
            GROUP BY b.branch_id, b.branch_name, b.capacity
            ORDER BY utilization_pct DESC
            """
        )
        branch_rows = cur.fetchall()
        columns = ("Branch", "Current Pets", "Capacity", "Utilization %")
        build_table(card, columns, branch_rows, height=5)
        
        # System-wide summary
        cur.execute(
            """
            SELECT SUM(pet_count) AS total_pets,
                   SUM(capacity) AS total_capacity,
                   ROUND(SUM(pet_count) * 100.0 / NULLIF(SUM(capacity), 0), 1) AS overall_utilization
            FROM (
                SELECT COUNT(p.pet_id) AS pet_count, COALESCE(b.capacity, 0) AS capacity
                FROM SHELTER_BRANCH b
                LEFT JOIN PET p ON p.shelter_branch_id = b.branch_id
                GROUP BY b.branch_id, b.capacity
            ) AS branch_stats
            """
        )
        summary = cur.fetchone()
        if summary and summary[1]:
            tk.Label(card, 
                     text=f"System Total: {summary[0] or 0} pets / {summary[1]} capacity = {summary[2] or 0}% utilization (SUM, AVG)",
                     bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(10, 15))

    # Refresh logic – this is what main.py calls whenever the
    # Reports tab is opened.

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