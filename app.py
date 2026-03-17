import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

# =====================================================
# STORAGE & THEME
# =====================================================
DATA_DIR = "users_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

THEME = {
    "bg": "#0f0f0f",
    "card": "#1c1c1c",
    "gold": "#D4AF37",
    "text": "#ffffff",
    "danger": "#ff4d4d"
}

# =====================================================
# HELPERS
# =====================================================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def user_file(username):
    return os.path.join(DATA_DIR, f"{username}.json")

def load_user_data(username):
    if os.path.exists(user_file(username)):
        with open(user_file(username), "r") as f:
            data = json.load(f)
    else:
        data = {}

    data.setdefault("expenses", [])
    data.setdefault("monthly_budget", 0)
    data.setdefault("budget_history", [])
    return data

def save_user_data(username, data):
    with open(user_file(username), "w") as f:
        json.dump(data, f, indent=2)

def currency(x):
    return f"₹{x:,.2f}"

# =====================================================
# APP CLASS
# =====================================================
class ExpenseApp:
    def __init__(self):
        self.users = load_users()
        self.current_user = None
        self.data = None
        self.root = None
        self.alert_shown = False
        self.build_login()

    def build_login(self):
        self.login = tk.Tk()
        self.login.title("Expense Tracker Pro - Login")
        self.login.state("zoomed")
        self.login.configure(bg=THEME["bg"])

        frame = tk.Frame(self.login, bg=THEME["bg"])
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="💰 Expense Tracker Pro", font=("Segoe UI", 40, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=30)

        tk.Label(frame, text="Username", fg=THEME["text"], bg=THEME["bg"]).pack()
        self.username_ent = tk.Entry(frame, width=30, font=("Segoe UI", 12))
        self.username_ent.pack(pady=10)

        tk.Label(frame, text="Password", fg=THEME["text"], bg=THEME["bg"]).pack()
        self.password_ent = tk.Entry(frame, show="*", width=30, font=("Segoe UI", 12))
        self.password_ent.pack(pady=10)

        tk.Button(frame, text="Login", bg=THEME["gold"], fg="black",
                  width=20, height=2, bd=0, command=self.login_user).pack(pady=10)

        tk.Button(frame, text="Create Account", bg=THEME["card"], fg="white",
                  width=20, bd=0, command=self.signup_user).pack()

        self.login.mainloop()

    def login_user(self):
        user = self.username_ent.get()
        pw = self.password_ent.get()

        if user in self.users and self.users[user]["password"] == hash_password(pw):
            self.current_user = user
            self.data = load_user_data(user)
            self.login.destroy()
            self.build_main()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def signup_user(self):
        user = self.username_ent.get()
        pw = self.password_ent.get()

        if not user or not pw:
            messagebox.showwarning("Warning", "Fields cannot be empty")
            return

        if user in self.users:
            messagebox.showerror("Error", "User exists")
            return

        self.users[user] = {"password": hash_password(pw)}
        save_users(self.users)
        save_user_data(user, {"expenses": [], "monthly_budget": 0, "budget_history": []})
        messagebox.showinfo("Success", "Account Created!")

    def build_main(self):
        self.root = tk.Tk()
        self.root.title(f"Expense Tracker Pro - {self.current_user}")
        self.root.state("zoomed")
        self.root.configure(bg=THEME["bg"])

        sidebar = tk.Frame(self.root, bg=THEME["card"], width=220)
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="💰 Menu", bg=THEME["card"], fg=THEME["gold"],
                 font=("Segoe UI", 18, "bold")).pack(pady=20)

        self.nav_button(sidebar, "Dashboard", self.show_dashboard)
        self.nav_button(sidebar, "Add Expense", self.show_add_expense)
        self.nav_button(sidebar, "Set Budget", self.set_budget)
        self.nav_button(sidebar, "Graphs", self.show_graphs)
        self.nav_button(sidebar, "Logout", self.logout)

        self.content = tk.Frame(self.root, bg=THEME["bg"])
        self.content.pack(fill="both", expand=True)

        self.show_dashboard()
        self.root.mainloop()

    def nav_button(self, parent, text, cmd):
        btn = tk.Label(parent, text=text, width=20, pady=10,
                       bg=THEME["card"], fg="white",
                       font=("Segoe UI", 10), cursor="hand2")
        btn.pack(pady=5)

        btn.bind("<Enter>", lambda e: btn.config(bg="#2a2a2a"))
        btn.bind("<Leave>", lambda e: btn.config(bg=THEME["card"]))
        btn.bind("<Button-1>", lambda e: cmd())

    # ================= FIXED DASHBOARD =================
    def show_dashboard(self):
        for w in self.content.winfo_children():
            w.destroy()

        total = sum(e["amount"] for e in self.data["expenses"])
        budget = self.data["monthly_budget"]
        remain = budget - total

        tk.Label(self.content, text="Financial Dashboard",
                 font=("Segoe UI", 30, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        percent = (total / budget * 100) if budget > 0 else 0

        # MESSAGE
        if budget == 0:
            msg = "⚠ Please set your monthly budget"
            color = "orange"
        elif percent >= 100:
            msg = "🚨 Budget Exceeded!"
            color = THEME["danger"]
        elif percent >= 80:
            msg = "⚠ Warning: You are close to your budget"
            color = "orange"
        else:
            msg = "✅ You are managing your budget well"
            color = "green"

        tk.Label(self.content, text=msg,
                 fg=color, bg=THEME["bg"],
                 font=("Segoe UI", 14, "bold")).pack(pady=10)

        # ALERT
        if percent >= 80 and not self.alert_shown:
            messagebox.showwarning("Budget Alert", "80% budget used!")
            self.alert_shown = True
        if percent < 80:
            self.alert_shown = False

        # PROGRESS BAR
        progress = ttk.Progressbar(self.content, length=400)
        progress.pack(pady=10)

        label = tk.Label(self.content, text="", fg="white", bg=THEME["bg"])
        label.pack()

        def animate(val=0):
            if val <= percent:
                progress["value"] = val
                label.config(text=f"{val:.1f}% used")
                self.content.after(10, lambda: animate(val + 1))
            else:
                label.config(text=f"{percent:.1f}% used")

        animate()

        # CARDS
        frame = tk.Frame(self.content, bg=THEME["bg"])
        frame.pack(pady=20)

        def card(title, value):
            c = tk.Frame(frame, bg=THEME["card"], padx=40, pady=30)
            tk.Label(c, text=title, fg="white", bg=THEME["card"]).pack()
            tk.Label(c, text=value, font=("Segoe UI", 22, "bold"),
                     fg=THEME["gold"], bg=THEME["card"]).pack()
            c.pack(side="left", padx=20)

        card("Total Spent", currency(total))
        card("Budget", currency(budget))
        card("Remaining", currency(remain))

   
    # ================= ADD EXPENSE WITH TABLE =================
    def show_add_expense(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Add New Expense",
                 font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        form = tk.Frame(self.content, bg=THEME["bg"])
        form.pack()

        amt_ent = tk.Entry(form)
        cat_ent = ttk.Combobox(form, values=["Food", "Rent", "Transport", "Shopping", "Bills", "Other"])

        tk.Label(form, text="Amount:", fg="white", bg=THEME["bg"]).grid(row=0, column=0, pady=10)
        amt_ent.grid(row=0, column=1)

        tk.Label(form, text="Category:", fg="white", bg=THEME["bg"]).grid(row=1, column=0, pady=10)
        cat_ent.grid(row=1, column=1)

        def save():
            try:
                expense = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount": float(amt_ent.get()),
                    "category": cat_ent.get()
                }
                self.data["expenses"].append(expense)
                save_user_data(self.current_user, self.data)
                self.show_add_expense()
            except:
                messagebox.showerror("Error", "Invalid Input")

        tk.Button(self.content, text="Save Expense", bg=THEME["gold"],
                  command=save).pack(pady=10)

        # TABLE
        columns = ("Date", "Amount", "Category")
        tree = ttk.Treeview(self.content, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)

        for i, e in enumerate(self.data["expenses"]):
            tree.insert("", "end", iid=i,
                        values=(e["date"], e["amount"], e["category"]))

        tree.pack(fill="both", expand=True, pady=20)

        # DELETE
        def delete():
            selected = tree.selection()
            if not selected: return
            idx = int(selected[0])
            del self.data["expenses"][idx]
            save_user_data(self.current_user, self.data)
            self.show_add_expense()

        tk.Button(self.content, text="Delete Selected",
                  bg=THEME["danger"], command=delete).pack()

        # EXPORT
        def export():
            file = filedialog.asksaveasfilename(defaultextension=".csv")
            if not file: return
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Amount", "Category"])
                for e in self.data["expenses"]:
                    writer.writerow([e["date"], e["amount"], e["category"]])
            messagebox.showinfo("Exported", "Data exported successfully")

        tk.Button(self.content, text="Export to Excel",
                  bg=THEME["gold"], command=export).pack(pady=10)

    # ================= GRAPHS =================
    def show_graphs(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Expense Insights",
                 font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        graph_type = ttk.Combobox(self.content,
                                  values=["Pie", "Bar", "Monthly Trend", "Combined"])
        graph_type.set("Pie")
        graph_type.pack()

        graph_frame = tk.Frame(self.content, bg=THEME["bg"])
        graph_frame.pack(fill="both", expand=True)

        def draw():
            for w in graph_frame.winfo_children(): w.destroy()

            cats = {}
            months = {}

            for e in self.data["expenses"]:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
                m = e["date"][:7]
                months[m] = months.get(m, 0) + e["amount"]

            fig = plt.Figure(figsize=(6, 4))
            ax = fig.add_subplot(111)

            if graph_type.get() == "Pie":
                ax.pie(cats.values(), labels=cats.keys(), autopct="%1.1f%%")
            elif graph_type.get() == "Bar":
                ax.bar(cats.keys(), cats.values())
            elif graph_type.get() == "Monthly Trend":
                ax.plot(list(months.keys()), list(months.values()), marker="o")
            else:
                ax.bar(cats.keys(), cats.values(), alpha=0.6)
                ax.plot(list(months.keys()), list(months.values()), color="red")

            ax.set_title("Expense Analysis")
            ax.grid(True)

            canvas = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()

        tk.Button(self.content, text="Generate Graph",
                  bg=THEME["gold"], command=draw).pack(pady=10)

    def set_budget(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Budget Manager",
                 font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        entry = tk.Entry(self.content)
        entry.pack(pady=10)

        def update():
            self.data["monthly_budget"] = float(entry.get())
            save_user_data(self.current_user, self.data)
            self.show_dashboard()

        tk.Button(self.content, text="Update Budget",
                  bg=THEME["gold"], command=update).pack()

    def logout(self):
        save_user_data(self.current_user, self.data)
        self.root.destroy()
        ExpenseApp()

if __name__ == "__main__":
    ExpenseApp()