import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import hashlib
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- Constants & Globals ----------------
DATA_DIR = "users_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REMEMBER_FILE = os.path.join(DATA_DIR, "remember.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Default theme colors
LIGHT = {"bg": "white", "fg": "black", "card": "#f7f9fb", "accent": "#1976D2", "danger": "#e74c3c"}
DARK = {"bg": "#2b2f36", "fg": "white", "card": "#39414a", "accent": "#9b59b6", "danger": "#e74c3c"}

# Helper: hash password
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# ---------------- Storage Helpers ----------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def user_file(username):
    return os.path.join(DATA_DIR, f"{username}.json")

def load_user_data(username):
    path = user_file(username)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # default structure
    return {
        "expenses": [],  # list of {id, date, category, amount, note}
        "monthly_budget": 0.0,
        "profile": {"avatar": None},
    }

def save_user_data(username, data):
    with open(user_file(username), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def remember_user(username):
    with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
        json.dump({"username": username}, f)

def forget_remember():
    if os.path.exists(REMEMBER_FILE):
        os.remove(REMEMBER_FILE)

def get_remembered_user():
    if os.path.exists(REMEMBER_FILE):
        with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("username")
    return None

# ---------------- Utility ----------------
def currency(x):
    return f"₹{x:,.2f}"

def parse_float_safe(s):
    try:
        return float(s)
    except:
        return None

def now_date_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------------- App ----------------
class ExpenseApp:
    def __init__(self):
        self.theme = LIGHT
        self.users = load_users()
        self.current_user = None
        self.data = None
        self.filtered_tree_items = []
        self.root = None
        self.main_widgets = {}
        self._build_login()

    # ---------- Login / Signup ----------
    def _build_login(self):
        self.login_win = tk.Tk()
        self.login_win.title("Expense Tracker - Login")
        self.login_win.geometry("420x320")
        self.login_win.configure(bg=self.theme["bg"])
        frame = tk.Frame(self.login_win, bg=self.theme["bg"], padx=16, pady=12)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Expense Tracker", font=("Arial", 18, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=(0,10))

        tk.Label(frame, text="Username", bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w")
        self.li_user = tk.Entry(frame, width=30)
        self.li_user.pack(pady=4)

        tk.Label(frame, text="Password", bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w")
        self.li_pass = tk.Entry(frame, show="*", width=30)
        self.li_pass.pack(pady=4)

        self.remember_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Remember me", variable=self.remember_var, bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w", pady=6)

        tk.Button(frame, text="Login", width=28, command=self._attempt_login).pack(pady=6)
        tk.Button(frame, text="Sign up", width=28, command=self._open_signup).pack(pady=2)
        tk.Button(frame, text="Quit", width=28, command=self.login_win.destroy).pack(pady=2)

        remembered = get_remembered_user()
        if remembered:
            self.li_user.insert(0, remembered)
            self.remember_var.set(True)

        self.login_win.mainloop()

    def _open_signup(self):
        su = tk.Toplevel(self.login_win)
        su.title("Sign Up")
        su.geometry("420x360")
        su.configure(bg=self.theme["bg"])
        frame = tk.Frame(su, padx=12, pady=12, bg=self.theme["bg"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Create account", font=("Arial", 16, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=(0,10))
        tk.Label(frame, text="Username", bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w")
        e_user = tk.Entry(frame, width=30); e_user.pack(pady=4)
        tk.Label(frame, text="Password", bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w")
        e_pass = tk.Entry(frame, show="*", width=30); e_pass.pack(pady=4)
        tk.Label(frame, text="Confirm Password", bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w")
        e_pass2 = tk.Entry(frame, show="*", width=30); e_pass2.pack(pady=4)

        def do_signup():
            username = e_user.get().strip()
            pw = e_pass.get()
            pw2 = e_pass2.get()
            if not username or not pw:
                messagebox.showerror("Error", "Please fill all fields")
                return
            if pw != pw2:
                messagebox.showerror("Error", "Passwords do not match")
                return
            if username in self.users:
                messagebox.showerror("Error", "Username already exists")
                return
            self.users[username] = {"password": hash_password(pw)}
            save_users(self.users)
            # create user file
            save_user_data(username, {"expenses": [], "monthly_budget": 0.0, "profile": {"avatar": None}})
            messagebox.showinfo("Success", "Account created! You can log in now.")
            su.destroy()

        tk.Button(frame, text="Sign Up", width=28, command=do_signup).pack(pady=8)
        tk.Button(frame, text="Cancel", width=28, command=su.destroy).pack()

    def _attempt_login(self):
        user = self.li_user.get().strip()
        pw = self.li_pass.get()
        if user in self.users and self.users[user]["password"] == hash_password(pw):
            if self.remember_var.get():
                remember_user(user)
            else:
                forget_remember()
            self.current_user = user
            self.data = load_user_data(user)
            self.login_win.destroy()
            self._build_main_window()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    # ---------- Main Window ----------
    def _build_main_window(self):
        self.root = tk.Tk()
        self.root.title(f"Expense Tracker - {self.current_user}")
        self.root.state("zoomed")
        self.root.configure(bg=self.theme["bg"])

        # Top bar
        top = tk.Frame(self.root, bg=self.theme["card"], height=60)
        top.pack(side="top", fill="x")
        tk.Label(top, text=f"Welcome, {self.current_user}", bg=self.theme["card"], fg=self.theme["fg"], font=("Arial", 14)).pack(side="left", padx=12)
        tk.Button(top, text="Toggle Theme", command=self._toggle_theme).pack(side="right", padx=8, pady=8)
        tk.Button(top, text="Profile", command=self._open_profile).pack(side="right", padx=8, pady=8)
        tk.Button(top, text="Logout", command=self._logout).pack(side="right", padx=8, pady=8)

        main = tk.Frame(self.root, bg=self.theme["bg"])
        main.pack(fill="both", expand=True)

        # Sidebar
        side = tk.Frame(main, bg=self.theme["card"], width=220)
        side.pack(side="left", fill="y")
        btns = [
            ("Dashboard", self._show_dashboard),
            ("Add Expense", self._show_add_expense),
            ("Graphs", self._show_graphs),
            ("Import CSV", self._import_csv),
            ("Export CSV", self._export_csv),
            ("Export Report (PDF)", self._export_pdf_report),
            ("Reset Month", self._reset_month),
        ]
        for t, cmd in btns:
            b = tk.Button(side, text=t, width=20, command=cmd)
            b.pack(pady=6, padx=8)

        # Content
        content = tk.Frame(main, bg=self.theme["bg"])
        content.pack(side="right", fill="both", expand=True)
        self.main_widgets["content"] = content

        # Start on Dashboard
        self._show_dashboard()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _toggle_theme(self):
        self.theme = DARK if self.theme == LIGHT else LIGHT
        # Rebuild UI quickly for simplicity
        self.root.destroy()
        self._build_main_window()

    def _logout(self):
        save_user_data(self.current_user, self.data)
        self.current_user = None
        self.data = None
        self.root.destroy()
        self.__init__()  # restart app to login

    def _on_close(self):
        save_user_data(self.current_user, self.data)
        self.root.destroy()

    # ---------- Profile ----------
    def _open_profile(self):
        p = tk.Toplevel(self.root)
        p.title("Profile")
        p.geometry("400x220")
        p.configure(bg=self.theme["bg"])

        tk.Label(p, text=f"User: {self.current_user}", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial", 12)).pack(pady=8)
        avatar_label = tk.Label(p, text=f"Avatar: {self.data.get('profile',{}).get('avatar') or 'None'}", bg=self.theme["bg"], fg=self.theme["fg"])
        avatar_label.pack(pady=6)

        def upload_avatar():
            path = filedialog.askopenfilename(title="Select avatar image", filetypes=[("Images","*.png;*.jpg;*.jpeg;*.gif"),("All","*.*")])
            if path:
                self.data.setdefault("profile", {})["avatar"] = path
                avatar_label.config(text=f"Avatar: {path}")
                save_user_data(self.current_user, self.data)

        tk.Button(p, text="Upload Avatar (optional)", command=upload_avatar).pack(pady=8)
        tk.Button(p, text="Close", command=p.destroy).pack()

    # ---------- Dashboard ----------
    def _show_dashboard(self):
        content = self.main_widgets["content"]
        for w in content.winfo_children(): w.destroy()

        header = tk.Frame(content, bg=self.theme["bg"])
        header.pack(fill="x", pady=8)
        tk.Label(header, text="Dashboard", font=("Arial", 18, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left", padx=12)

        # Cards: Budget / Spent / Remaining
        cards = tk.Frame(content, bg=self.theme["bg"])
        cards.pack(fill="x", padx=12, pady=6)

        budget_val = self.data.get("monthly_budget", 0.0)
        total_spent = sum(e["amount"] for e in self.data.get("expenses", []))
        remaining = (budget_val - total_spent) if budget_val>0 else 0.0

        def card_frame(title, value_text):
            f = tk.Frame(cards, bg=self.theme["card"], padx=12, pady=10)
            f.pack(side="left", padx=8, pady=4, ipadx=8, ipady=6)
            tk.Label(f, text=title, bg=self.theme["card"], fg=self.theme["fg"]).pack(anchor="w")
            tk.Label(f, text=value_text, bg=self.theme["card"], fg=self.theme["fg"], font=("Arial", 14, "bold")).pack(anchor="w")
            return f

        card_frame("Monthly Budget", currency(budget_val))
        card_frame("Total Spent", currency(total_spent))
        rem = card_frame("Remaining", currency(remaining))
        if budget_val>0 and total_spent>budget_val:
            tk.Label(rem, text="Budget exceeded!", bg=self.theme["card"], fg=self.theme["danger"], font=("Arial",10,"bold")).pack(anchor="w")

        # Controls: set budget
        control = tk.Frame(content, bg=self.theme["bg"])
        control.pack(fill="x", padx=12, pady=6)
        tk.Label(control, text="Set Monthly Budget:", bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left")
        be = tk.Entry(control, width=12); be.pack(side="left", padx=6)
        def set_budget():
            val = parse_float_safe(be.get())
            if val is None:
                messagebox.showerror("Error", "Enter valid number")
                return
            self.data["monthly_budget"] = float(val)
            save_user_data(self.current_user, self.data)
            messagebox.showinfo("Saved", "Monthly budget updated")
            self._show_dashboard()
        tk.Button(control, text="Set", command=set_budget).pack(side="left", padx=6)

        # Search + tree of expenses
        search_frame = tk.Frame(content, bg=self.theme["bg"])
        search_frame.pack(fill="x", padx=12, pady=(8,0))
        tk.Label(search_frame, text="Search:", bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left")
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side="left", padx=6)
        tk.Button(search_frame, text="Clear", command=lambda: (search_var.set(""), refresh_tree())).pack(side="left", padx=6)

        tree_frame = tk.Frame(content, bg=self.theme["bg"])
        tree_frame.pack(fill="both", expand=True, padx=12, pady=8)

        cols = ("Date", "Category", "Amount", "Note", "ID")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols[:-1]: tree.heading(c, text=c)
        tree.column("ID", width=0, stretch=False)
        tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)

        # Fill tree
        def refresh_tree():
            q = search_var.get().lower()
            for it in tree.get_children():
                tree.delete(it)
            for e in sorted(self.data.get("expenses", []), key=lambda x: x["date"], reverse=True):
                # filter
                if q and not (q in e["category"].lower() or q in e.get("note","").lower() or q in e["date"].lower()):
                    continue
                tree.insert("", "end", values=(e["date"], e["category"], currency(e["amount"]), e.get("note",""), e["id"]))
        refresh_tree()

        # Edit on double click
        def on_double(ev):
            selection = tree.selection()
            if not selection: return
            item = selection[0]
            vals = tree.item(item, "values")
            eid = vals[4]
            self._open_edit_dialog(eid, refresh_tree)
        tree.bind("<Double-1>", on_double)

        # Buttons
        btns = tk.Frame(content, bg=self.theme["bg"])
        btns.pack(fill="x", padx=12, pady=(0,12))
        tk.Button(btns, text="Add Expense", command=self._show_add_expense).pack(side="left", padx=6)
        tk.Button(btns, text="Delete Selected", command=lambda: self._delete_selected(tree, refresh_tree)).pack(side="left", padx=6)
        tk.Button(btns, text="Delete All", command=lambda: self._delete_all(confirm=True, cb=refresh_tree)).pack(side="left", padx=6)
        tk.Button(btns, text="Show Graphs", command=self._show_graphs).pack(side="left", padx=6)

        # Search binding
        search_entry.bind("<KeyRelease>", lambda e: refresh_tree())

    # ---------- Add Expense ----------
    def _show_add_expense(self):
        content = self.main_widgets["content"]
        for w in content.winfo_children(): w.destroy()

        frame = tk.Frame(content, bg=self.theme["bg"], padx=12, pady=12)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Add Expense", font=("Arial",18,"bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(anchor="w", pady=(0,8))

        form = tk.Frame(frame, bg=self.theme["bg"])
        form.pack(anchor="w", pady=6)

        tk.Label(form, text="Category:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, padx=6, pady=6)
        cat_var = tk.StringVar()
        cat = ttk.Combobox(form, textvariable=cat_var, values=["Food","Transport","Shopping","Bills","Others"], width=20)
        cat.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(form, text="Amount:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, padx=6, pady=6)
        amount = tk.Entry(form)
        amount.grid(row=1, column=1, padx=6, pady=6)

        tk.Label(form, text="Note:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=2, column=0, padx=6, pady=6)
        note = tk.Entry(form, width=40)
        note.grid(row=2, column=1, padx=6, pady=6)

        def add():
            amt = parse_float_safe(amount.get())
            if amt is None:
                messagebox.showerror("Error", "Enter valid amount")
                return
            c = cat_var.get().strip() or "Others"
            entry = {
                "id": f"{int(datetime.now().timestamp()*1000)}",
                "date": now_date_str(),
                "category": c,
                "amount": float(amt),
                "note": note.get().strip()
            }
            self.data.setdefault("expenses", []).append(entry)
            save_user_data(self.current_user, self.data)
            messagebox.showinfo("Added", "Expense added")
            self._show_dashboard()

            # Check budget exceed
            total_spent = sum(e["amount"] for e in self.data["expenses"])
            if self.data.get("monthly_budget",0) > 0 and total_spent > self.data.get("monthly_budget"):
                messagebox.showwarning("Budget Exceeded", "⚠️ You have exceeded your monthly budget!")

        tk.Button(form, text="Add Expense", command=add).grid(row=3, column=1, pady=12)

    # ---------- Edit Expense ----------
    def _open_edit_dialog(self, eid, refresh_cb=None):
        exp = next((e for e in self.data.get("expenses", []) if e["id"]==eid), None)
        if not exp:
            messagebox.showerror("Error", "Expense not found")
            return
        d = tk.Toplevel(self.root)
        d.title("Edit Expense")
        d.geometry("380x260")
        d.configure(bg=self.theme["bg"])
        tk.Label(d, text="Edit Expense", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",12,"bold")).pack(pady=6)
        frm = tk.Frame(d, bg=self.theme["bg"])
        frm.pack(pady=6)

        tk.Label(frm, text="Category:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, padx=6, pady=6)
        cvar = tk.StringVar(value=exp["category"])
        ttk.Combobox(frm, textvariable=cvar, values=["Food","Transport","Shopping","Bills","Others"]).grid(row=0, column=1, padx=6, pady=6)

        tk.Label(frm, text="Amount:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=1, column=0, padx=6, pady=6)
        aentry = tk.Entry(frm); aentry.grid(row=1, column=1, padx=6, pady=6); aentry.insert(0,str(exp["amount"]))

        tk.Label(frm, text="Note:", bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=2, column=0, padx=6, pady=6)
        nentry = tk.Entry(frm, width=30); nentry.grid(row=2, column=1, padx=6, pady=6); nentry.insert(0, exp.get("note",""))

        def save_edits():
            amt = parse_float_safe(aentry.get())
            if amt is None:
                messagebox.showerror("Error", "Invalid amount")
                return
            exp["category"] = cvar.get().strip() or "Others"
            exp["amount"] = float(amt)
            exp["note"] = nentry.get().strip()
            save_user_data(self.current_user, self.data)
            messagebox.showinfo("Saved", "Expense updated")
            d.destroy()
            if refresh_cb: refresh_cb()

        tk.Button(d, text="Save", command=save_edits).pack(pady=8)

    # ---------- Delete ----------
    def _delete_selected(self, tree, refresh_cb=None):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an expense to delete")
            return
        if not messagebox.askyesno("Confirm", "Delete selected expense(s)?"): return
        for it in sel:
            vals = tree.item(it, "values")
            eid = vals[4]
            self.data["expenses"] = [e for e in self.data["expenses"] if e["id"]!=eid]
        save_user_data(self.current_user, self.data)
        if refresh_cb: refresh_cb()

    def _delete_all(self, confirm=True, cb=None):
        if confirm and not messagebox.askyesno("Confirm", "Delete ALL expenses?"): return
        self.data["expenses"] = []
        save_user_data(self.current_user, self.data)
        if cb: cb()
        messagebox.showinfo("Done", "All expenses deleted")

    # ---------- Graphs ----------
    def _show_graphs(self):
        content = self.main_widgets["content"]
        for w in content.winfo_children(): w.destroy()

        header = tk.Frame(content, bg=self.theme["bg"])
        header.pack(fill="x", pady=8)
        tk.Label(header, text="Graphs", font=("Arial",18,"bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(side="left", padx=12)

        # Controls
        ctrl = tk.Frame(content, bg=self.theme["bg"])
        ctrl.pack(fill="x", padx=12, pady=6)
        chart_type = tk.StringVar(value="Pie")
        ttk.Combobox(ctrl, textvariable=chart_type, values=["Pie","Bar"], width=10).pack(side="left", padx=6)
        tk.Button(ctrl, text="Refresh", command=lambda: plot()).pack(side="left", padx=6)
        tk.Button(ctrl, text="Save PNG", command=lambda: save_plot(chart_type.get())).pack(side="left", padx=6)
        tk.Button(ctrl, text="Save PDF", command=lambda: save_plot(chart_type.get(), fmt="pdf")).pack(side="left", padx=6)

        graph_frame = tk.Frame(content, bg=self.theme["bg"])
        graph_frame.pack(fill="both", expand=True, padx=12, pady=12)

        fig = plt.Figure(figsize=(6,5))
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def plot():
            ax.clear()
            exps = self.data.get("expenses", [])
            if not exps:
                ax.text(0.5,0.5,"No expenses to display", ha="center")
                canvas.draw(); return
            # aggregate by category
            cats = {}
            for e in exps:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
            labels = list(cats.keys()); vals = list(cats.values())
            typ = chart_type.get()
            if typ == "Pie":
                ax.pie(vals, labels=labels, autopct="%1.1f%%")
                ax.set_title("Expenses by Category")
            else:
                ax.bar(labels, vals)
                ax.set_title("Expenses by Category (Bar)")
                ax.set_ylabel("Amount")
            canvas.draw()

        def save_plot(typ, fmt="png"):
            # produce an off-screen figure similar to display and save
            exps = self.data.get("expenses", [])
            if not exps:
                messagebox.showwarning("No data", "No expenses to save")
                return
            cats = {}
            for e in exps:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
            labels = list(cats.keys()); vals = list(cats.values())
            fig2 = plt.Figure(figsize=(8,6))
            ax2 = fig2.add_subplot(111)
            if typ == "Pie":
                ax2.pie(vals, labels=labels, autopct="%1.1f%%")
            else:
                ax2.bar(labels, vals)
                ax2.set_ylabel("Amount")
            file = filedialog.asksaveasfilename(defaultextension=f".{fmt}", filetypes=[(fmt.upper(),f"*.{fmt}")])
            if file:
                fig2.savefig(file)
                messagebox.showinfo("Saved", f"Saved to {file}")

        plot()

    # ---------- CSV Import / Export ----------
    def _export_csv(self):
        exps = self.data.get("expenses", [])
        if not exps:
            messagebox.showwarning("No data", "No expenses to export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id","date","category","amount","note"])
            for e in exps:
                writer.writerow([e["id"], e["date"], e["category"], e["amount"], e.get("note","")])
        messagebox.showinfo("Exported", f"Exported {len(exps)} items to {path}")

    def _import_csv(self):
        path = filedialog.askopenfilename(title="Import CSV", filetypes=[("CSV","*.csv")])
        if not path: return
        added = 0
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Expect columns: date,category,amount,note (id optional)
                try:
                    amt = float(row.get("amount") or row.get("Amount") or 0)
                except:
                    continue
                ent = {
                    "id": row.get("id") or f"{int(datetime.now().timestamp()*1000)}_{added}",
                    "date": row.get("date") or now_date_str(),
                    "category": row.get("category") or row.get("Category") or "Others",
                    "amount": amt,
                    "note": row.get("note") or row.get("Note") or ""
                }
                self.data.setdefault("expenses", []).append(ent)
                added += 1
        save_user_data(self.current_user, self.data)
        messagebox.showinfo("Imported", f"Imported {added} expenses from CSV")

    # ---------- Export PDF Report ----------
    def _export_pdf_report(self):
        exps = self.data.get("expenses", [])
        if not exps:
            messagebox.showwarning("No data", "No expenses to report")
            return
        # simple one-page PDF with summary & small pie chart using matplotlib
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not path: return
        # summary
        budget = self.data.get("monthly_budget",0)
        total = sum(e["amount"] for e in exps)
        remaining = budget - total
        cats = {}
        for e in exps:
            cats[e["category"]] = cats.get(e["category"],0) + e["amount"]
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        fig.suptitle(f"Expense Report - {self.current_user}\nGenerated: {now_date_str()}", fontsize=12)
        ax1 = fig.add_axes([0.1, 0.55, 0.8, 0.35])
        ax1.pie(list(cats.values()), labels=list(cats.keys()), autopct="%1.1f%%")
        ax1.set_title("Expenses by Category")
        ax2 = fig.add_axes([0.1, 0.2, 0.8, 0.25])
        summary_text = f"Monthly Budget: {currency(budget)}\nTotal Spent: {currency(total)}\nRemaining: {currency(remaining)}\nNumber of entries: {len(exps)}"
        ax2.text(0, 0.5, summary_text, fontsize=11)
        ax2.axis("off")
        fig.savefig(path)
        plt.close(fig)
        messagebox.showinfo("Saved", f"Report exported to {path}")

    # ---------- Reset Month ----------
    def _reset_month(self):
        if not messagebox.askyesno("Confirm", "This will delete all expenses (use carefully). Continue?"):
            return
        self.data["expenses"] = []
        save_user_data(self.current_user, self.data)
        messagebox.showinfo("Done", "All expenses cleared")
        self._show_dashboard()

# ---------------- Run ----------------
if __name__ == "__main__":
    ExpenseApp()
