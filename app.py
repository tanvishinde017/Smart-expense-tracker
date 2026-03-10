import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import hashlib
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- STORAGE ----------------

DATA_DIR = "users_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------------- THEMES ----------------

LIGHT_THEME = {
    "bg": "#f4f6fb",
    "card": "#ffffff",
    "accent": "#6C63FF",
    "accent2": "#00C9A7",
    "danger": "#FF6B6B",
    "text": "#2d3436"
}

DARK_THEME = {
    "bg": "#1e1f26",
    "card": "#2c2f36",
    "accent": "#9b59b6",
    "accent2": "#00C9A7",
    "danger": "#FF6B6B",
    "text": "#ecf0f1"
}

# ---------------- HELPERS ----------------

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return json.load(open(USERS_FILE))
    return {}

def save_users(users):
    json.dump(users, open(USERS_FILE, "w"), indent=2)

def user_file(username):
    return os.path.join(DATA_DIR, f"{username}.json")

def load_user_data(username):
    if os.path.exists(user_file(username)):
        return json.load(open(user_file(username)))
    return {"expenses": [], "monthly_budget": 0}

def save_user_data(username, data):
    json.dump(data, open(user_file(username), "w"), indent=2)

def currency(x):
    return f"₹{x:,.2f}"

# ================= APP =================

class ExpenseApp:

    def __init__(self):

        self.theme = LIGHT_THEME
        self.users = load_users()
        self.current_user = None
        self.data = None
        self.build_login()

# ---------------- LOGIN ----------------

    def build_login(self):

        self.login = tk.Tk()
        self.login.title("Expense Tracker Pro")
        self.login.geometry("420x420")
        self.login.configure(bg=self.theme["bg"])

        tk.Label(self.login,
                 text="💸 Expense Tracker Pro",
                 font=("Segoe UI",22,"bold"),
                 bg=self.theme["bg"],
                 fg=self.theme["accent"]).pack(pady=30)

        self.username = tk.Entry(self.login,font=("Segoe UI",12))
        self.username.pack(pady=10,ipady=6)

        self.password = tk.Entry(self.login,font=("Segoe UI",12),show="*")
        self.password.pack(pady=10,ipady=6)

        tk.Button(self.login,text="Login",
                  bg=self.theme["accent"],
                  fg="white",
                  width=20,
                  command=self.login_user).pack(pady=10)

        tk.Button(self.login,text="Sign Up",
                  bg=self.theme["accent2"],
                  fg="white",
                  width=20,
                  command=self.signup_user).pack()

        self.login.mainloop()

    def login_user(self):

        user=self.username.get()
        pw=self.password.get()

        if user in self.users and self.users[user]["password"]==hash_password(pw):

            self.current_user=user
            self.data=load_user_data(user)

            self.login.destroy()
            self.build_main()

        else:
            messagebox.showerror("Error","Invalid credentials")

    def signup_user(self):

        user=self.username.get()
        pw=self.password.get()

        if user in self.users:
            messagebox.showerror("Error","User already exists")
            return

        self.users[user]={"password":hash_password(pw)}
        save_users(self.users)

        save_user_data(user,{"expenses":[],"monthly_budget":0})

        messagebox.showinfo("Success","Account Created")

# ---------------- MAIN WINDOW ----------------

    def build_main(self):

        self.root=tk.Tk()
        self.root.title("Expense Tracker Pro")
        self.root.state("zoomed")
        self.root.configure(bg=self.theme["bg"])

        # NAVBAR

        navbar=tk.Frame(self.root,bg=self.theme["accent"],height=60)
        navbar.pack(fill="x")

        tk.Label(navbar,
                 text=f"Welcome {self.current_user}",
                 bg=self.theme["accent"],
                 fg="white",
                 font=("Segoe UI",14,"bold")).pack(side="left",padx=20)

        tk.Button(navbar,text="Toggle Theme",
                  bg="white",
                  command=self.toggle_theme).pack(side="right",padx=10)

        tk.Button(navbar,text="Logout",
                  bg="white",
                  fg=self.theme["danger"],
                  command=self.logout).pack(side="right")

        # SIDEBAR

        sidebar=tk.Frame(self.root,bg=self.theme["card"],width=220)
        sidebar.pack(side="left",fill="y")

        self.create_nav_button(sidebar,"Dashboard",self.show_dashboard)
        self.create_nav_button(sidebar,"Add Expense",self.show_add_expense)
        self.create_nav_button(sidebar,"Graphs",self.show_graph)
        self.create_nav_button(sidebar,"Import CSV",self.import_csv)
        self.create_nav_button(sidebar,"Export CSV",self.export_csv)

        self.content=tk.Frame(self.root,bg=self.theme["bg"])
        self.content.pack(fill="both",expand=True)

        self.show_dashboard()
        self.root.mainloop()

    def create_nav_button(self,parent,text,command):

        tk.Button(parent,
                  text=text,
                  width=20,
                  pady=12,
                  bd=0,
                  bg=self.theme["card"],
                  fg=self.theme["text"],
                  command=command).pack(pady=5)

# ---------------- DASHBOARD ----------------

    def show_dashboard(self):

        for w in self.content.winfo_children():
            w.destroy()

        total=sum(e["amount"] for e in self.data["expenses"])
        count=len(self.data["expenses"])

        tk.Label(self.content,
                 text="📊 Dashboard",
                 font=("Segoe UI",26,"bold"),
                 bg=self.theme["bg"],
                 fg=self.theme["accent"]).pack(pady=20)

        cards=tk.Frame(self.content,bg=self.theme["bg"])
        cards.pack()

        def card(title,value):

            c=tk.Frame(cards,
                       bg=self.theme["card"],
                       padx=40,
                       pady=25)

            tk.Label(c,text=title,
                     font=("Segoe UI",12),
                     bg=self.theme["card"]).pack()

            tk.Label(c,text=value,
                     font=("Segoe UI",22,"bold"),
                     bg=self.theme["card"],
                     fg=self.theme["accent"]).pack()

            c.pack(side="left",padx=20)

        card("Total Spent",currency(total))
        card("Total Expenses",count)

# ---------------- ADD EXPENSE ----------------

    def show_add_expense(self):

        for w in self.content.winfo_children():
            w.destroy()

        tk.Label(self.content,
                 text="💸 Add Expense",
                 font=("Segoe UI",24,"bold"),
                 bg=self.theme["bg"],
                 fg=self.theme["accent"]).pack(pady=20)

        form=tk.Frame(self.content,bg=self.theme["card"],padx=40,pady=30)
        form.pack(pady=10)

        labels=["Category","Description","Amount","Date"]

        for i,l in enumerate(labels):
            tk.Label(form,text=l,bg=self.theme["card"],
                     font=("Segoe UI",11)).grid(row=i,column=0,padx=10,pady=8,sticky="w")

        category=ttk.Combobox(form,
            values=["Food","Travel","Shopping","Bills","Health","Other"],
            width=25)

        category.grid(row=0,column=1)
        category.set("Food")

        desc=tk.Entry(form,width=28)
        desc.grid(row=1,column=1)

        amount=tk.Entry(form,width=28)
        amount.grid(row=2,column=1)

        date=tk.Entry(form,width=28)
        date.insert(0,datetime.now().strftime("%Y-%m-%d"))
        date.grid(row=3,column=1)

        def add():

            try:
                amt=float(amount.get())
            except:
                messagebox.showerror("Error","Invalid amount")
                return

            self.data["expenses"].append({
                "category":category.get(),
                "description":desc.get(),
                "amount":amt,
                "date":date.get()
            })

            save_user_data(self.current_user,self.data)

            messagebox.showinfo("Success","Expense Added")
            self.show_add_expense()

        tk.Button(form,text="Add Expense",
                  bg=self.theme["accent"],
                  fg="white",
                  width=20,
                  command=add).grid(row=4,columnspan=2,pady=15)

        # TABLE

        table_frame=tk.Frame(self.content)
        table_frame.pack(pady=20)

        columns=("Date","Category","Description","Amount")

        tree=ttk.Treeview(table_frame,
                          columns=columns,
                          show="headings",
                          height=10)

        for col in columns:
            tree.heading(col,text=col)
            tree.column(col,width=160)

        scrollbar=ttk.Scrollbar(table_frame,orient="vertical",command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.grid(row=0,column=0)
        scrollbar.grid(row=0,column=1,sticky="ns")

        for e in self.data["expenses"]:
            tree.insert("",tk.END,values=(
                e["date"],
                e["category"],
                e.get("description",""),
                currency(e["amount"])
            ))

# ---------------- GRAPH ----------------

    def show_graph(self):

        for w in self.content.winfo_children():
            w.destroy()

        cats={}

        for e in self.data["expenses"]:
            cats[e["category"]]=cats.get(e["category"],0)+e["amount"]

        fig=plt.Figure(figsize=(6,5))
        ax=fig.add_subplot(111)

        if cats:
            ax.pie(cats.values(),labels=cats.keys(),autopct="%1.1f%%")

        canvas=FigureCanvasTkAgg(fig,master=self.content)
        canvas.draw()
        canvas.get_tk_widget().pack()

# ---------------- CSV ----------------

    def export_csv(self):

        path=filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return

        with open(path,"w",newline="") as f:

            writer=csv.writer(f)
            writer.writerow(["date","category","amount"])

            for e in self.data["expenses"]:
                writer.writerow([e["date"],e["category"],e["amount"]])

        messagebox.showinfo("Exported","CSV Saved")

    def import_csv(self):

        path=filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not path:
            return

        with open(path) as f:

            reader=csv.DictReader(f)

            for row in reader:
                self.data["expenses"].append({
                    "date":row["date"],
                    "category":row["category"],
                    "amount":float(row["amount"])
                })

        save_user_data(self.current_user,self.data)

        messagebox.showinfo("Imported","CSV Loaded")
        self.show_add_expense()

# ---------------- OTHER ----------------

    def toggle_theme(self):

        self.theme=DARK_THEME if self.theme==LIGHT_THEME else LIGHT_THEME
        self.root.destroy()
        self.build_main()

    def logout(self):

        save_user_data(self.current_user,self.data)
        self.root.destroy()
        self.__init__()

# ---------------- RUN ----------------

if __name__=="__main__":
    ExpenseApp()