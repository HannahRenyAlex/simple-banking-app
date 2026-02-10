ACCOUNTS_FILE = "accounts.txt"


def load_accounts():
    """Load accounts from the accounts file into a dictionary."""
    accounts = {}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                email, password, balance_str = parts
                try:
                    balance = float(balance_str)
                except ValueError:
                    balance = 0.0
                accounts[email] = {"password": password, "balance": balance}
    except FileNotFoundError:
        pass
    return accounts


def save_accounts(accounts):
    """Persist all accounts back to the accounts file."""
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for email, data in accounts.items():
                line = f"{email},{data['password']},{data['balance']}\n"
                f.write(line)
    except OSError as e:
        print(f"Error saving accounts: {e}")


def is_valid_email(email):
    """Basic email validation: must contain '@' and '.', and no spaces."""
    if "@" not in email or "." not in email:
        return False
    if " " in email:
        return False
    return True


def create_account(accounts):
    print("\n=== Create Account ===")
    email = input("Enter email (Gmail preferred): ").strip()

    if not is_valid_email(email):
        print("Invalid email format. Email must contain '@' and '.'.")
        return

    if email in accounts:
        print("An account with this email already exists.")
        return

    password = input("Enter password: ").strip()
    confirm_password = input("Confirm password: ").strip()

    if password != confirm_password:
        print("Passwords do not match. Account not created.")
        return

    accounts[email] = {"password": password, "balance": 0.0}
    save_accounts(accounts)
    print("Account created successfully.")


def login(accounts):
    print("\n=== Login ===")
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()

    user = accounts.get(email)
    if not user:
        print("No account found with that email.")
        return None

    if user["password"] != password:
        print("Incorrect password.")
        return None

    print("Login successful.")
    return email


def deposit(accounts, email):
    print("\n=== Deposit ===")
    try:
        amount_str = input("Enter amount to deposit: ").strip()
        amount = float(amount_str)
        if amount <= 0:
            print("Amount must be greater than 0.")
            return
    except ValueError:
        print("Invalid amount. Please enter a numeric value.")
        return

    accounts[email]["balance"] += amount
    save_accounts(accounts)
    print(f"Deposited {amount:.2f}. New balance: {accounts[email]['balance']:.2f}")


def withdraw(accounts, email):
    print("\n=== Withdraw ===")
    try:
        amount_str = input("Enter amount to withdraw: ").strip()
        amount = float(amount_str)
        if amount <= 0:
            print("Amount must be greater than 0.")
            return
    except ValueError:
        print("Invalid amount. Please enter a numeric value.")
        return

    balance = accounts[email]["balance"]
    if amount > balance:
        print("Insufficient funds.")
        return

    accounts[email]["balance"] -= amount
    save_accounts(accounts)
    print(f"Withdrew {amount:.2f}. New balance: {accounts[email]['balance']:.2f}")


def check_balance(accounts, email):
    print("\n=== Balance ===")
    balance = accounts[email]["balance"]
    print(f"Current balance: {balance:.2f}")


def banking_menu(accounts, email):
    while True:
        print("\n=== Banking Menu ===")
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Check Balance")
        print("4. Logout")

        choice = input("Select an option: ").strip()

        if choice == "1":
            deposit(accounts, email)
        elif choice == "2":
            withdraw(accounts, email)
        elif choice == "3":
            check_balance(accounts, email)
        elif choice == "4":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


def main():
    accounts = load_accounts()

    while True:
        print("\n=== Simple Banking App ===")
        print("1. Login")
        print("2. Create Account")
        print("3. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            email = login(accounts)
            if email:
                banking_menu(accounts, email)
                accounts = load_accounts()
        elif choice == "2":
            create_account(accounts)
            accounts = load_accounts()
        elif choice == "3":
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
