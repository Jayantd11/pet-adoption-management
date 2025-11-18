# reports_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

BG = "#F5F5F7"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#86868B"
BORDER = "#E5E5EA"


def init_reports(content, connection):
    """
    Creates the Reports frame.
    Returns:
        {
          "frame": <Frame>,
          "refresh": <callable to reload data>
        }
    """
    frame = tk.Frame(content, bg=BG)
    frame.grid(row=0, column=0, sticky="nsew")

    # Title
    tk.Label(
        frame,
        text="Reports & Analytics",
        bg=BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 24, "bold")
    ).pack(anchor="w", padx=40, pady=(30, 20))

    # --------- TOP SUMMARY CARDS ---------
    summary_row = tk.Frame(frame, bg=BG)
    summary_row.pack(fill="x", padx=40, pady=(0, 20))

    def make_card(parent, title):
        c = tk.Frame(parent, bg=CARD_BG,
                     highlightthickness=1, highlightbackground=BORDER)
        c.pack(side="left", fill="both", expand=True, padx=6, ipadx=20, ipady=12)
        tk.Label(
            c, text=title, bg=CARD_BG, fg=TEXT_SECONDARY,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))
        val = tk.Label(
            c, text="–", bg=CARD_BG, fg=TEXT_PRIMARY,
            font=("Segoe UI", 20, "bold")
        )
        val.pack(anchor="w")
        return val

    total_pets_lbl    = make_card(summary_row, "Total Pets")
    total_mr_lbl      = make_card(summary_row, "Total Medical Records")
    total_staff_lbl   = make_card(summary_row, "Total Staff")
    total_branches_lbl = make_card(summary_row, "Total Branches")

    # --------- PET AGE STATS (MIN / MAX / AVG / COUNT / SUM) ---------
    age_card = tk.Frame(frame, bg=CARD_BG,
                        highlightthickness=1, highlightbackground=BORDER)
    age_card.pack(fill="x", padx=40, pady=(0, 20))

    tk.Label(
        age_card,
        text="Pet Age Summary (uses MIN / MAX / AVG / COUNT / SUM)",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", padx=24, pady=(12, 4))

    age_inner = tk.Frame(age_card, bg=CARD_BG)
    age_inner.pack(fill="x", padx=24, pady=(0, 16))

    cols_age = ("TotalPets", "MinAge", "MaxAge", "AvgAge", "SumAge")
    age_tree = ttk.Treeview(age_inner, columns=cols_age, show="headings", height=1)
    for col, w in zip(cols_age, (100, 80, 80, 90, 100)):
        age_tree.heading(col, text=col)
        age_tree.column(col, width=w, anchor="w")
    age_tree.pack(fill="x")

    # --------- PETS PER BRANCH ---------
    branch_card = tk.Frame(frame, bg=CARD_BG,
                           highlightthickness=1, highlightbackground=BORDER)
    branch_card.pack(fill="both", expand=True, padx=40, pady=(0, 20))

    tk.Label(
        branch_card,
        text="Pets per Branch (COUNT)",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", padx=24, pady=(12, 4))

    branch_inner = tk.Frame(branch_card, bg=CARD_BG)
    branch_inner.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    cols_branch = ("Branch", "PetCount")
    branch_tree = ttk.Treeview(branch_inner, columns=cols_branch, show="headings", height=6)
    for col, w in zip(cols_branch, (260, 120)):
        branch_tree.heading(col, text=col)
        branch_tree.column(col, width=w, anchor="w")

    b_scroll = tk.Scrollbar(branch_inner, orient="vertical", command=branch_tree.yview)
    branch_tree.configure(yscrollcommand=b_scroll.set)
    branch_tree.pack(side="left", fill="both", expand=True)
    b_scroll.pack(side="right", fill="y")

    # --------- MEDICAL RECORDS PER PET ---------
    mr_card = tk.Frame(frame, bg=CARD_BG,
                       highlightthickness=1, highlightbackground=BORDER)
    mr_card.pack(fill="both", expand=True, padx=40, pady=(0, 30))

    tk.Label(
        mr_card,
        text="Top Pets by Medical Records (COUNT)",
        bg=CARD_BG,
        fg=TEXT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w", padx=24, pady=(12, 4))

    mr_inner = tk.Frame(mr_card, bg=CARD_BG)
    mr_inner.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    cols_mr = ("PetID", "Name", "RecordCount")
    mr_tree = ttk.Treeview(mr_inner, columns=cols_mr, show="headings", height=8)
    for col, w in zip(cols_mr, (80, 200, 120)):
        mr_tree.heading(col, text=col)
        mr_tree.column(col, width=w, anchor="w")

    mr_scroll = tk.Scrollbar(mr_inner, orient="vertical", command=mr_tree.yview)
    mr_tree.configure(yscrollcommand=mr_scroll.set)
    mr_tree.pack(side="left", fill="both", expand=True)
    mr_scroll.pack(side="right", fill="y")

    # --------- REFRESH FUNCTION (RUNS QUERIES) ---------
    def refresh():
        cur = connection.cursor()

        try:
            # 1) Summary: total pets / mr / staff / branches (COUNT)
            cur.execute("SELECT COUNT(*) FROM PET")
            total_pets_lbl.config(text=str(cur.fetchone()[0] or 0))

            cur.execute("SELECT COUNT(*) FROM medical_record")
            total_mr_lbl.config(text=str(cur.fetchone()[0] or 0))

            cur.execute("SELECT COUNT(*) FROM staff")
            total_staff_lbl.config(text=str(cur.fetchone()[0] or 0))

            cur.execute("SELECT COUNT(*) FROM SHELTER_BRANCH")
            total_branches_lbl.config(text=str(cur.fetchone()[0] or 0))

            # 2) Age stats: MIN / MAX / AVG / COUNT / SUM
            for r in age_tree.get_children():
                age_tree.delete(r)

            cur.execute("""
                SELECT
                    COUNT(*)      AS total_pets,
                    MIN(age)      AS min_age,
                    MAX(age)      AS max_age,
                    AVG(age)      AS avg_age,
                    SUM(age)      AS sum_age
                FROM PET
                WHERE age IS NOT NULL
            """)
            row = cur.fetchone()
            if row:
                total_pets, min_age, max_age, avg_age, sum_age = row
                age_tree.insert(
                    "",
                    "end",
                    values=(
                        total_pets or 0,
                        min_age if min_age is not None else "–",
                        max_age if max_age is not None else "–",
                        f"{avg_age:.2f}" if avg_age is not None else "–",
                        sum_age if sum_age is not None else 0,
                    )
                )

            # 3) Pets per branch (COUNT)
            for r in branch_tree.get_children():
                branch_tree.delete(r)

            cur.execute("""
                SELECT b.branch_name,
                       COUNT(p.pet_id) AS pet_count
                FROM SHELTER_BRANCH b
                LEFT JOIN PET p
                     ON p.shelter_branch_id = b.branch_id
                GROUP BY b.branch_id, b.branch_name
                ORDER BY b.branch_name
            """)
            for name, pet_count in cur.fetchall():
                branch_tree.insert("", "end", values=(name, pet_count))

            # 4) Top pets by medical records (COUNT)
            for r in mr_tree.get_children():
                mr_tree.delete(r)

            cur.execute("""
                SELECT p.pet_id,
                       p.name,
                       COUNT(mr.record_id) AS rec_count
                FROM PET p
                LEFT JOIN medical_record mr
                       ON mr.pet_id = p.pet_id
                GROUP BY p.pet_id, p.name
                ORDER BY rec_count DESC, p.name
                LIMIT 20
            """)
            for pet_id, name, rec_count in cur.fetchall():
                mr_tree.insert("", "end", values=(pet_id, name, rec_count))

        except mysql.connector.Error as e:
            messagebox.showerror("Reports Error", f"Could not load reports:\n{e}")
        finally:
            cur.close()

    return {"frame": frame, "refresh": refresh}
