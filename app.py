import streamlit as st
import json
from datetime import datetime


ACCOUNTS_FILE = "accounts.txt"


def is_valid_email(email: str) -> bool:
    """Basic email validation: must contain '@' and '.', and no spaces."""
    if "@" not in email or "." not in email:
        return False
    if " " in email:
        return False
    return True


def _now_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_currency(amount: float) -> str:
    """Format a number as INR currency, e.g. ₹19,900.00."""
    return f"₹{float(amount):,.2f}"


def _migrate_single_account_to_multi(data: dict) -> None:
    """
    Ensure each user dict has an 'accounts' list.
    If old single-account fields exist, wrap them into a single account entry.
    """
    if "accounts" in data and isinstance(data["accounts"], list) and data["accounts"]:
        return

    bank_name = data.get("bank_name", "")
    account_number = data.get("account_number", "ACCT-1")
    balance = float(data.get("balance", 0.0))
    transactions = data.get("transactions", [])

    account = {
        "account_id": account_number,
        "account_type": "Savings",
        "bank_name": bank_name,
        "balance": balance,
        "transactions": [],
    }

    for tx in transactions:
        try:
            amt = float(tx.get("amount", 0.0))
        except (TypeError, ValueError):
            amt = 0.0
        account["transactions"].append(
            {
                "timestamp": tx.get("timestamp", _now_timestamp()),
                "type": tx.get("type", "deposit"),
                "amount": amt,
            }
        )

    data["accounts"] = [account]


def load_accounts() -> dict:
    """Load all users from accounts.txt (one JSON object per line)."""
    users: dict = {}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                email = data.get("email")
                if not email:
                    continue
                data.setdefault("first_name", "")
                data.setdefault("last_name", "")
                data.setdefault("password", "")
                data.setdefault("created_at", _now_timestamp())
                _migrate_single_account_to_multi(data)
                users[email] = data
    except FileNotFoundError:
        pass
    return users


def save_accounts(users: dict) -> None:
    """Persist all users back to accounts.txt as one JSON object per line."""
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for user in users.values():
                f.write(json.dumps(user) + "\n")
    except OSError as e:
        st.error(f"Error saving accounts: {e}")


def append_transaction(account: dict, tx_type: str, amount: float) -> None:
    """Append a transaction to a specific account's transaction history."""
    tx = {
        "timestamp": _now_timestamp(),
        "type": tx_type,
        "amount": float(amount),
    }
    account.setdefault("transactions", [])
    account["transactions"].append(tx)


def render_app_header() -> None:
    st.title("Simple Banking Application")
    st.caption("Streamlit-based banking system with file storage")
    st.divider()


def show_login_create_forgot() -> None:
    """Authentication area: Login, Create Account, Forgot Password."""
    render_app_header()

    if st.session_state.get("logout_message"):
        st.info(st.session_state["logout_message"])
        st.session_state["logout_message"] = ""

    tab_login, tab_create, tab_forgot = st.tabs(
        ["Login", "Create Account", "Forgot Password"]
    )

    # LOGIN TAB
    with tab_login:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button", use_container_width=True):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                users = load_accounts()
                user = users.get(email)
                if not user:
                    st.error("No account found with that email.")
                elif user.get("password") != password:
                    st.error("Incorrect password.")
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email
                    st.session_state["current_page"] = "account_select"
                    st.session_state["selected_account_index"] = 0
                    st.success("Login successful!")
                    st.rerun()

    # CREATE ACCOUNT TAB
    with tab_create:
        st.subheader("Create Account")
        first_name = st.text_input("First name", key="create_first_name")
        last_name = st.text_input("Last name", key="create_last_name")
        email = st.text_input("Email", key="create_email")
        bank_name = st.text_input("Bank name", key="create_bank_name")
        account_number = st.text_input(
            "Bank account number / ID",
            key="create_account_number",
        )
        starting_balance = st.number_input(
            "Starting balance",
            min_value=0.0,
            step=0.01,
            key="create_starting_balance",
        )
        account_type = st.selectbox(
            "Account type",
            ["Savings", "Current"],
            key="create_account_type",
        )
        password = st.text_input("Password", type="password", key="create_password")
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="create_confirm_password",
        )

        if st.button("Create Account", key="create_button", use_container_width=True):
            if (
                not first_name
                or not last_name
                or not email
                or not bank_name
                or not account_number
                or not password
                or not confirm_password
            ):
                st.error("Please fill in all fields.")
            elif not is_valid_email(email):
                st.error("Invalid email format. Email must contain '@' and '.'.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                users = load_accounts()
                if email in users:
                    st.error("A user with this email already exists.")
                else:
                    account = {
                        "account_id": account_number,
                        "account_type": account_type,
                        "bank_name": bank_name,
                        "balance": float(starting_balance),
                        "transactions": [],
                    }
                    if starting_balance > 0:
                        append_transaction(account, "deposit", float(starting_balance))

                    user = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "password": password,
                        "created_at": _now_timestamp(),
                        "accounts": [account],
                    }
                    users[email] = user
                    save_accounts(users)
                    st.success("Account created successfully! You can now login.")

    # FORGOT PASSWORD TAB
    with tab_forgot:
        st.subheader("Forgot Password")
        email = st.text_input("Registered email", key="forgot_email")
        new_password = st.text_input("New password", type="password", key="forgot_new_password")
        confirm_new_password = st.text_input(
            "Confirm new password",
            type="password",
            key="forgot_confirm_new_password",
        )

        if st.button("Reset Password", key="forgot_button", use_container_width=True):
            if not email or not new_password or not confirm_new_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_new_password:
                st.error("Passwords do not match.")
            else:
                users = load_accounts()
                user = users.get(email)
                if not user:
                    st.error("No account found with that email.")
                else:
                    user["password"] = new_password
                    save_accounts(users)
                    st.success("Password has been reset. You can now login with your new password.")


def get_current_user() -> dict | None:
    """Return the currently logged-in user dict, or None."""
    email = st.session_state.get("user_email")
    if not email:
        return None
    users = load_accounts()
    user = users.get(email)
    if not user:
        return None
    _migrate_single_account_to_multi(user)
    return user


def save_current_user(user: dict) -> None:
    """Persist changes for the current user back to accounts file."""
    email = user.get("email")
    if not email:
        return
    users = load_accounts()
    users[email] = user
    save_accounts(users)


def get_selected_account(user: dict) -> dict | None:
    """Get the currently selected account dict for the user."""
    accounts = user.get("accounts", [])
    if not accounts:
        return None
    idx = st.session_state.get("selected_account_index", 0)
    if not isinstance(idx, int) or idx < 0 or idx >= len(accounts):
        idx = 0
        st.session_state["selected_account_index"] = 0
    return accounts[idx]


def show_account_selection() -> None:
    """Page to select or add bank accounts under the same user."""
    render_app_header()
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        return

    st.subheader("Select Bank Account")

    accounts = user.get("accounts", [])
    if not accounts:
        st.info("No accounts found. Please add a new account.")
    else:
        options = []
        for i, acc in enumerate(accounts):
            label = (
                f"{acc.get('account_type', 'Savings')} - "
                f"{acc.get('account_id', f'ACCT-{i+1}')} "
                f"({acc.get('bank_name', '')})"
            )
            options.append(label)

        selected_label = st.radio(
            "Choose an account to operate on:",
            options=options,
            index=st.session_state.get("selected_account_index", 0),
            key="account_select_radio",
        )
        selected_index = options.index(selected_label)
        st.session_state["selected_account_index"] = selected_index

        acc = accounts[selected_index]
        st.write("### Selected Account Details")
        st.write(f"**Account ID / Number:** {acc.get('account_id', '')}")
        st.write(f"**Account type:** {acc.get('account_type', '')}")
        st.write(f"**Bank name:** {acc.get('bank_name', '')}")
        st.write(f"**Balance:** {format_currency(float(acc.get('balance', 0.0)))}")

        if st.button("Continue to Main Menu", use_container_width=True, key="account_select_continue"):
            st.session_state["current_page"] = "main_menu"
            st.rerun()

    st.divider()
    st.subheader("Add New Account")

    with st.form("add_account_form", clear_on_submit=False):
        new_account_id = st.text_input("New account ID / Number", key="new_account_id")
        new_account_type = st.selectbox(
            "Account type",
            ["Savings", "Current"],
            key="new_account_type",
        )
        new_bank_name = st.text_input("Bank name", key="new_account_bank_name")
        new_starting_balance = st.number_input(
            "Starting balance",
            min_value=0.0,
            step=0.01,
            key="new_account_starting_balance",
        )
        submitted = st.form_submit_button("Add Account")
        if submitted:
            if not new_account_id or not new_bank_name:
                st.error("Please fill in all required fields for the new account.")
            else:
                new_account = {
                    "account_id": new_account_id,
                    "account_type": new_account_type,
                    "bank_name": new_bank_name,
                    "balance": float(new_starting_balance),
                    "transactions": [],
                }
                if new_starting_balance > 0:
                    append_transaction(new_account, "deposit", float(new_starting_balance))
                user.setdefault("accounts", [])
                user["accounts"].append(new_account)
                save_current_user(user)
                st.session_state["selected_account_index"] = len(user["accounts"]) - 1
                st.success("New account added successfully.")
                st.rerun()


def show_main_menu() -> None:
    render_app_header()
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    st.subheader("Main Menu")
    st.write(
        f"Logged in as: **{user.get('first_name', '')} {user.get('last_name', '')}** "
        f"({user.get('email', '')})"
    )
    st.write(
        f"Active account: **{account.get('account_type', '')} - {account.get('account_id', '')} "
        f"({account.get('bank_name', '')})**"
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Deposit", use_container_width=True, key="menu_deposit"):
            st.session_state["current_page"] = "deposit"
            st.rerun()
    with col2:
        if st.button("Withdraw", use_container_width=True, key="menu_withdraw"):
            st.session_state["current_page"] = "withdraw"
            st.rerun()
    with col3:
        if st.button("Check Balance", use_container_width=True, key="menu_balance"):
            st.session_state["current_page"] = "balance"
            st.rerun()
    with col4:
        if st.button("Transaction History", use_container_width=True, key="menu_history"):
            st.session_state["current_page"] = "history"
            st.rerun()

    st.divider()

    col5, col6 = st.columns(2)
    with col5:
        if st.button("Profile", use_container_width=True, key="menu_profile"):
            st.session_state["current_page"] = "profile"
            st.rerun()
    with col6:
        if st.button("Switch Account", use_container_width=True, key="menu_switch_account"):
            st.session_state["current_page"] = "account_select"
            st.rerun()

    st.divider()
    if st.button("Logout", use_container_width=True, key="menu_logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        st.session_state["current_page"] = "auth"
        st.session_state["logout_message"] = "You have been logged out."
        st.info("Logged out successfully.")
        st.rerun()


def back_to_main_menu_button() -> None:
    if st.button("← Back to Main Menu", key=f"back_{st.session_state.get('current_page', '')}"):
        st.session_state["current_page"] = "main_menu"
        st.rerun()


def show_deposit_page() -> None:
    render_app_header()
    st.subheader("Deposit")
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    back_to_main_menu_button()
    st.write(f"Current balance: {format_currency(float(account.get('balance', 0.0)))}")

    amount = st.number_input("Amount to deposit", min_value=0.01, step=0.01, key="deposit_amount_page")
    if st.button("Confirm Deposit", use_container_width=True, key="deposit_confirm"):
        if amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            account["balance"] = float(account.get("balance", 0.0)) + float(amount)
            append_transaction(account, "deposit", float(amount))
            save_current_user(user)
            st.success(
                f"Deposited {format_currency(float(amount))}. "
                f"New balance: {format_currency(float(account['balance']))}"
            )


def show_withdraw_page() -> None:
    render_app_header()
    st.subheader("Withdraw")
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    back_to_main_menu_button()
    st.write(f"Current balance: {format_currency(float(account.get('balance', 0.0)))}")

    amount = st.number_input("Amount to withdraw", min_value=0.01, step=0.01, key="withdraw_amount_page")
    if st.button("Confirm Withdraw", use_container_width=True, key="withdraw_confirm"):
        balance = float(account.get("balance", 0.0))
        if amount <= 0:
            st.error("Amount must be greater than 0.")
        elif amount > balance:
            st.error("Insufficient balance for this withdrawal.")
        else:
            account["balance"] = balance - float(amount)
            append_transaction(account, "withdraw", float(amount))
            save_current_user(user)
            st.success(
                f"Withdrew {format_currency(float(amount))}. "
                f"New balance: {format_currency(float(account['balance']))}"
            )


def show_balance_page() -> None:
    render_app_header()
    st.subheader("Account Balance")
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    back_to_main_menu_button()

    balance = float(account.get("balance", 0.0))
    st.metric("Current Balance", format_currency(balance))


def show_history_page() -> None:
    render_app_header()
    st.subheader("Transaction History")
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    back_to_main_menu_button()

    transactions = account.get("transactions", [])
    if not transactions:
        st.write("No transactions yet.")
        return

    current_balance = float(account.get("balance", 0.0))
    net_change = 0.0
    for tx in transactions:
        amt = float(tx.get("amount", 0.0))
        if tx.get("type") == "deposit":
            net_change += amt
        else:
            net_change -= amt
    opening_balance = current_balance - net_change

    rows = []
    running_balance = opening_balance

    for tx in transactions:
        ts = tx.get("timestamp", "")
        parts = ts.split(" ")
        date = parts[0] if len(parts) > 0 else ""
        time = parts[1] if len(parts) > 1 else ""
        tx_type_raw = tx.get("type", "")
        amount = float(tx.get("amount", 0.0))

        if tx_type_raw == "deposit":
            running_balance += amount
            tx_type = "Deposit"
            sign = "+"
        else:
            running_balance -= amount
            tx_type = "Withdraw"
            sign = "-"

        rows.append(
            {
                "Date": date,
                "Time": time,
                "Transaction Type": tx_type,
                "Amount (₹)": f"{sign}{format_currency(abs(amount))}",
                "Balance After (₹)": format_currency(running_balance),
            }
        )

    st.dataframe(rows, use_container_width=True)


def show_profile_page() -> None:
    render_app_header()
    st.subheader("Profile")
    user = get_current_user()
    if not user:
        st.error("User not found. Please log in again.")
        return

    account = get_selected_account(user)
    if not account:
        st.warning("No account selected. Please select an account first.")
        st.session_state["current_page"] = "account_select"
        st.rerun()
        return

    back_to_main_menu_button()

    edit_mode = st.session_state.get("profile_edit_mode", False)

    if not edit_mode:
        st.write("### Personal Information")
        st.write(f"**First name:** {user.get('first_name', '')}")
        st.write(f"**Last name:** {user.get('last_name', '')}")
        st.write(f"**Email:** {user.get('email', '')}")

        st.divider()

        st.write("### Bank / Account Details")
        st.write(f"**Bank name:** {account.get('bank_name', '')}")
        st.write(f"**Account ID / Number:** {account.get('account_id', '')}")
        st.write(f"**Account type:** {account.get('account_type', '')}")
        st.write(
            f"**Current balance:** {format_currency(float(account.get('balance', 0.0)))}"
        )
        st.write(f"**Account created at:** {user.get('created_at', '')}")

        st.divider()

        if st.button("Edit Profile", key="edit_profile_button"):
            st.session_state["profile_edit_mode"] = True
            st.rerun()
    else:
        st.write("### Edit Profile")
        first_name = st.text_input(
            "First name",
            value=user.get("first_name", ""),
            key="profile_edit_first_name",
        )
        last_name = st.text_input(
            "Last name",
            value=user.get("last_name", ""),
            key="profile_edit_last_name",
        )
        bank_name = st.text_input(
            "Bank name",
            value=account.get("bank_name", ""),
            key="profile_edit_bank_name",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes", key="profile_save_button", use_container_width=True):
                user["first_name"] = first_name
                user["last_name"] = last_name
                account["bank_name"] = bank_name
                save_current_user(user)
                st.session_state["profile_edit_mode"] = False
                st.success("Profile updated successfully.")
                st.rerun()
        with col2:
            if st.button("Cancel", key="profile_cancel_button", use_container_width=True):
                st.session_state["profile_edit_mode"] = False
                st.info("Edits canceled.")
                st.rerun()


def main() -> None:
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        st.session_state["current_page"] = "auth"
        st.session_state["logout_message"] = ""
        st.session_state["selected_account_index"] = 0

    if not st.session_state.get("logged_in"):
        st.session_state["current_page"] = "auth"
        show_login_create_forgot()
        return

    page = st.session_state.get("current_page", "account_select")

    if page == "account_select":
        show_account_selection()
    elif page == "main_menu":
        show_main_menu()
    elif page == "deposit":
        show_deposit_page()
    elif page == "withdraw":
        show_withdraw_page()
    elif page == "balance":
        show_balance_page()
    elif page == "history":
        show_history_page()
    elif page == "profile":
        show_profile_page()
    else:
        st.session_state["current_page"] = "account_select"
        show_account_selection()


if __name__ == "__main__":
    main()


