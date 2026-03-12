import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        tk.Button(frame, text="Login", bg=THEME["gold"], fg="black", font=("Segoe UI", 10, "bold"),
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
        messagebox.showinfo("Success", "Account Created! You can now log in.")

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
        tk.Button(parent, text=text, width=20, pady=10, bg=THEME["card"], fg="white",
                  bd=0, font=("Segoe UI", 10), cursor="hand2", command=cmd).pack(pady=5)

    def show_dashboard(self):
        for w in self.content.winfo_children(): w.destroy()

        total = sum(e["amount"] for e in self.data["expenses"])
        budget = self.data["monthly_budget"]
        remain = budget - total

        tk.Label(self.content, text="Financial Dashboard", font=("Segoe UI", 30, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        frame = tk.Frame(self.content, bg=THEME["bg"])
        frame.pack()

        def card(title, value):
            c = tk.Frame(frame, bg=THEME["card"], padx=40, pady=30)
            tk.Label(c, text=title, fg="white", bg=THEME["card"]).pack()
            tk.Label(c, text=value, font=("Segoe UI", 22, "bold"), fg=THEME["gold"], bg=THEME["card"]).pack()
            c.pack(side="left", padx=20)

        card("Total Spent", currency(total))
        card("Budget", currency(budget))
        card("Remaining", currency(remain))

        if budget == 0: msg = "Set a monthly budget to start tracking."
        elif total > budget: msg = "⚠ You exceeded your monthly budget!"
        elif remain < budget * 0.2: msg = "⚠ Budget almost finished."
        else: msg = "✔ Your spending is under control."

        tk.Label(self.content, text=msg, font=("Segoe UI", 16), fg="white", bg=THEME["bg"]).pack(pady=20)

    def show_add_expense(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Add New Expense", font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        form = tk.Frame(self.content, bg=THEME["bg"])
        form.pack()

        tk.Label(form, text="Amount:", fg="white", bg=THEME["bg"]).grid(row=0, column=0, pady=10)
        amt_ent = tk.Entry(form)
        amt_ent.grid(row=0, column=1)

        tk.Label(form, text="Category:", fg="white", bg=THEME["bg"]).grid(row=1, column=0, pady=10)
        cat_ent = ttk.Combobox(form, values=["Food", "Rent", "Transport", "Shopping", "Bills", "Other"])
        cat_ent.grid(row=1, column=1)

        def save():
            try:
                amt = float(amt_ent.get())
                cat = cat_ent.get()
                if not cat: raise ValueError
                
                expense = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount": amt,
                    "category": cat
                }
                self.data["expenses"].append(expense)
                save_user_data(self.current_user, self.data)
                messagebox.showinfo("Success", "Expense Added")
                self.show_dashboard()
            except:
                messagebox.showerror("Error", "Invalid Input")

        tk.Button(self.content, text="Save Expense", bg=THEME["gold"], command=save).pack(pady=20)

    def set_budget(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Budget Manager", font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        tk.Label(self.content, text="Enter Monthly Budget:", fg="white", bg=THEME["bg"]).pack()
        entry = tk.Entry(self.content, width=30)
        entry.pack(pady=10)

        def update_budget():
            try:
                amt = float(entry.get())
                self.data["monthly_budget"] = amt
                save_user_data(self.current_user, self.data)
                messagebox.showinfo("Saved", "Monthly Budget Updated")
                self.show_dashboard()
            except:
                messagebox.showerror("Error", "Invalid number")

        tk.Button(self.content, text="Update Budget", bg=THEME["gold"], fg="black",
                  command=update_budget).pack(pady=10)

    def show_graphs(self):
        for w in self.content.winfo_children(): w.destroy()

        tk.Label(self.content, text="Expense Insights", font=("Segoe UI", 26, "bold"),
                 fg=THEME["gold"], bg=THEME["bg"]).pack(pady=20)

        graph_type = ttk.Combobox(self.content, values=["Pie", "Bar", "Monthly Trend"])
        graph_type.set("Pie")
        graph_type.pack()

        graph_frame = tk.Frame(self.content, bg=THEME["bg"])
        graph_frame.pack(fill="both", expand=True)

        def draw():
            for w in graph_frame.winfo_children(): w.destroy()
            
            if not self.data["expenses"]:
                tk.Label(graph_frame, text="No data available", fg="white", bg=THEME["bg"]).pack()
                return

            cats = {}
            months = {}
            for e in self.data["expenses"]:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
                m = e["date"][:7]
                months[m] = months.get(m, 0) + e["amount"]

            fig = plt.Figure(figsize=(6, 4), dpi=100, facecolor=THEME["bg"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["bg"])

            if graph_type.get() == "Pie":
                ax.pie(cats.values(), labels=cats.keys(), autopct="%1.1f%%", textprops={'color':"w"})
            elif graph_type.get() == "Bar":
                ax.bar(cats.keys(), cats.values(), color=THEME["gold"])
                ax.tick_params(colors='white')
            else:
                sorted_months = sorted(months.keys())
                ax.plot(sorted_months, [months[m] for m in sorted_months], marker="o", color=THEME["gold"])
                ax.tick_params(colors='white')

            canvas = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=10)

        tk.Button(self.content, text="Generate Graph", bg=THEME["gold"], command=draw).pack(pady=10)

    def logout(self):
        save_user_data(self.current_user, self.data)
        self.root.destroy()
        ExpenseApp()

if __name__ == "__main__":
    ExpenseApp()