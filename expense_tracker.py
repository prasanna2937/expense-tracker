import sqlite3
from datetime import date, datetime


def connect():
    return sqlite3.connect("expenses.db")


def create_table():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            date TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_amount():
    while True:
        try:
            amount = float(input("Amount: "))
            if amount > 0:
                return amount
            print("Amount must be greater than 0!")
        except ValueError:
            print("Please enter a number!")


def get_date():
    while True:
        text = input("Date (YYYY-MM-DD, press Enter for today): ").strip()
        if text == "":
            return date.today().isoformat()
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            print("Wrong format! Example: 2026-10-16")


def add_transaction():
    print("\n1. Income")
    print("2. Expense")
    choice = input("Choose (1/2): ").strip()

    if choice == "1":
        t_type = "income"
    elif choice == "2":
        t_type = "expense"
    else:
        print("Please choose 1 or 2.")
        return

    category = input("Category (e.g. Salary, Food, Travel): ").strip().title()
    if category == "":
        print("Category is required!")
        return

    amount = get_amount()
    t_date = get_date()
    note = input("Note (optional): ").strip()

    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (type, category, amount, date, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (t_type, category, amount, t_date, note)
    )
    conn.commit()
    conn.close()
    print(f"{t_type.title()} saved!")


def view_transactions():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, date, type, category, amount, note "
        "FROM transactions ORDER BY date DESC, id DESC"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No transactions yet.")
        return

    print(f"\n{'ID':<5}{'Date':<13}{'Type':<10}{'Category':<15}{'Amount':<12}{'Note':<20}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<5}{r[1]:<13}{r[2]:<10}{r[3]:<15}{r[4]:<12.2f}{(r[5] or ''):<20}")


def show_balance():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'")
    income = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'")
    expense = cur.fetchone()[0]
    conn.close()

    print("\n=== Balance ===")
    print(f"Total income  : {income:.2f}")
    print(f"Total expense : {expense:.2f}")
    print(f"Balance       : {income - expense:.2f}")


def category_summary():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT category, SUM(amount) AS total "
        "FROM transactions WHERE type = 'expense' "
        "GROUP BY category ORDER BY total DESC"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No expenses yet.")
        return

    grand_total = sum(r[1] for r in rows)
    print(f"\n{'Category':<15}{'Total':<12}{'% of expenses':<15}")
    print("-" * 42)
    for category, total in rows:
        percent = total / grand_total * 100
        print(f"{category:<15}{total:<12.2f}{percent:<15.1f}")


def monthly_summary():
    month = input("Month (YYYY-MM, press Enter for this month): ").strip()
    if month == "":
        month = date.today().strftime("%Y-%m")

    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT type, COALESCE(SUM(amount), 0) "
        "FROM transactions WHERE strftime('%Y-%m', date) = ? "
        "GROUP BY type",
        (month,)
    )
    totals = dict(cur.fetchall())

    cur.execute(
        "SELECT category, SUM(amount) "
        "FROM transactions WHERE type = 'expense' AND strftime('%Y-%m', date) = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (month,)
    )
    top = cur.fetchone()
    conn.close()

    income = totals.get("income", 0)
    expense = totals.get("expense", 0)

    print(f"\n=== Summary for {month} ===")
    print(f"Income  : {income:.2f}")
    print(f"Expense : {expense:.2f}")
    print(f"Saved   : {income - expense:.2f}")
    if top:
        print(f"Highest spending category: {top[0]} ({top[1]:.2f})")
    else:
        print("No expenses in this month.")


def delete_transaction():
    view_transactions()
    try:
        tid = int(input("\nEnter ID to delete: "))
    except ValueError:
        print("ID must be a number!")
        return

    confirm = input("Are you sure? (y/n): ").lower()
    if confirm != "y":
        print("Cancelled.")
        return

    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = ?", (tid,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        print("No transaction with that ID.")
    else:
        print("Transaction deleted!")


def main():
    create_table()

    while True:
        print("\n=== Expense Tracker ===")
        print("1. Add income / expense")
        print("2. View all transactions")
        print("3. Show balance")
        print("4. Category wise expenses")
        print("5. Monthly summary")
        print("6. Delete transaction")
        print("7. Exit")

        choice = input("Choose (1-7): ").strip()

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            show_balance()
        elif choice == "4":
            category_summary()
        elif choice == "5":
            monthly_summary()
        elif choice == "6":
            delete_transaction()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Please choose 1 to 7.")


main()