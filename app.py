import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

st.set_page_config("Financify", page_icon=":tada:", layout="wide")

# Create the SQLite database using SQLAlchemy
engine = create_engine('sqlite:///data.db', echo=True)
Base = declarative_base()

# Define your SQLAlchemy data model with Date (without time)
class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    category = Column(String(255))
    type = Column(String(255))
    amount = Column(Float)
    date = Column(Date, default=datetime.now)

class Budget(Base):
    __tablename__ = 'budget'
    id = Column(Integer, primary_key=True)
    category = Column(String(255))
    budget_amount = Column(Float)
    period = Column(String(20))  # e.g., monthly, weekly

# Create and initialize the database
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def insert_data(category, transaction_type, amount):
    session = Session()
    financial_data = Data(category=category, type=transaction_type, amount=amount)
    session.add(financial_data)
    session.commit()
    session.close()

def calculate_balance():
    session = Session()
    total_income = sum(transaction.amount for transaction in session.query(Data).filter_by(type='Income').all())
    total_expenses = sum(transaction.amount for transaction in session.query(Data).filter_by(type='Expense').all())
    balance = total_income - total_expenses
    session.close()
    return balance

def fetch_transactions():
    session = Session()
    transactions = session.query(Data.type, Data.amount, Data.date, Data.category).all()
    session.close()
    transactions_df = pd.DataFrame(transactions, columns=["Type", "Amount", "Date", "Category"])
    return transactions_df

# Function to send an email
def send_email(receiver_email, subject, message, attachment_path=None):
    sender_email = 'zayedalmalick@gmail.com'
    sender_password = 'swtc zcsp abow jmtu'
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    
    if attachment_path:
        with open(attachment_path, "rb") as file:
            part = MIMEApplication(file.read(), Name="report.csv")
        part['Content-Disposition'] = f'attachment; filename="{attachment_path}"'
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        st.success("Email sent successfully")
    except Exception as e:
        st.error(f"Email could not be sent: {str(e)}")

def check_budget_details(category, period):
    session = Session()
    today = datetime.now()
    total_expenses = sum(transaction.amount for transaction in session.query(Data).filter_by(type='Expense', category=category).all())

    budget_entry = session.query(Budget).filter_by(category=category, period=period).first()
    
    if not budget_entry:
        return {
            "status": "Budget not set",
            "remaining_budget": None,
            "budget_period": None,
            "budget_duration": None
        }
    
    budget_amount = budget_entry.budget_amount
    budget_period = period
    
    if period == "Monthly":
        last_day_of_month = datetime(today.year, today.month, 1).replace(day=1, month=today.month % 12 + 1) - timedelta(days=1)
        remaining_days = (last_day_of_month - today).days
        budget_duration = f"{remaining_days} days left in the month"
    elif period == "Weekly":
        remaining_days = 7 - today.weekday()
        budget_duration = f"{remaining_days} days left in the week"

    remaining_budget = budget_amount - total_expenses
    status = "On budget" if total_expenses <= budget_amount else "Exceeded budget"
    
    session.close()
    
    return {
        "status": status,
        "remaining_budget": remaining_budget,
        "budget_period": budget_period,
        "budget_duration": budget_duration
    }
def display_budget_overview():
    st.subheader("Budget Overview")
    budget_categories = ["Rent", "Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare", "Education", "Other"]
    for category in budget_categories:
        st.header(category)  # Display the category as a header

        st.subheader("Monthly Budget")
        budget_info_monthly = check_budget_details(category, "Monthly")
        if budget_info_monthly['remaining_budget'] is not None:
            st.write(f"- Status: {budget_info_monthly['status']}")
            st.write(f"- Remaining Budget: ₹{budget_info_monthly['remaining_budget']:.2f}")
            st.write(f"- Budget Period: {budget_info_monthly['budget_period']}")
            st.write(f"- Budget Duration: {budget_info_monthly['budget_duration']}")

        st.subheader("Weekly Budget")
        budget_info_weekly = check_budget_details(category, "Weekly")
        if budget_info_weekly['remaining_budget'] is not None:
            st.write(f"- Status: {budget_info_weekly['status']}")
            st.write(f"- Remaining Budget: ₹{budget_info_weekly['remaining_budget']:.2f}")
            st.write(f"- Budget Period: {budget_info_weekly['budget_period']}")
            st.write(f"- Budget Duration: {budget_info_weekly['budget_duration']}")

def send_budget_email_notifications():
    st.subheader("Send Budget Email Notifications")
    receiver_email = st.text_input("Recipient's Email")
    if st.button("Send Budget Email Notifications"):
        if receiver_email:
            budget_categories = ["Rent", "Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare", "Education", "Other"]
            email_subject = "Budget Status Notification"
            email_message = ""

            for category in budget_categories:
                monthly_budget_info = check_budget_details(category, "Monthly")
                weekly_budget_info = check_budget_details(category, "Weekly")

                if monthly_budget_info['remaining_budget'] is not None:
                    email_message += f"Category: {category}\n\n"
                    email_message += "Monthly Budget:\n"
                    email_message += f"- Status: {monthly_budget_info['status']}\n"
                    email_message += f"- Remaining Budget: ₹{monthly_budget_info['remaining_budget']:.2f}\n"
                    email_message += f"- Budget Period: {monthly_budget_info['budget_period']}\n"
                    email_message += f"- Budget Duration: {monthly_budget_info['budget_duration']}\n\n"

                if weekly_budget_info['remaining_budget'] is not None:
                    email_message += "Weekly Budget:\n"
                    email_message += f"- Status: {weekly_budget_info['status']}\n"
                    email_message += f"- Remaining Budget: ₹{weekly_budget_info['remaining_budget']:.2f}\n"
                    email_message += f"- Budget Period: {weekly_budget_info['budget_period']}\n"
                    email_message += f"- Budget Duration: {weekly_budget_info['budget_duration']}\n\n"

            send_email(receiver_email, email_subject, email_message)

with st.container():
    st.header("Financify")
    st.subheader("A Personal Finance Manager Made in Python :computer:")
    st.write("---")

with st.expander("Dashboard", expanded=False):
    st.subheader("Dashboard")
    balance = calculate_balance()
    st.write(f"Current Balance: ₹{balance:,.2f}")
    
# Create predefined lists of categories
income_categories = ["Salary", "Freelance", "Investment", "Gifts", "Other"]
expense_categories = ["Rent", "Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare", "Education", "Other"]

with st.expander("Income", expanded=False):
    st.subheader("Income") 
    category = st.selectbox("Category", income_categories)
    amount = st.number_input("Income Amount", min_value=1)
    if st.button("Add Income"):
        insert_data(category, "Income", amount)
        st.success(f"Income of ₹{amount:.2f} added for {category}")

with st.expander("Expense", expanded=False):
    st.subheader("Expense") 
    category = st.selectbox("Category", expense_categories)
    amount = st.number_input("Expense Amount", min_value=1)
    if st.button("Add Expense"):
        insert_data(category, "Expense", amount)
        st.success(f"Expense of ₹{amount:.2f} added for {category}")

with st.expander("Set Budget", expanded=False):
    st.subheader("Set Budget")
    budget_categories = ["Rent", "Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare", "Education", "Other"]
    category = st.selectbox("Budget Category", budget_categories)
    budget_amount = st.number_input("Budget Amount", min_value=0.01)
    period = st.radio("Budget Period", ["Monthly", "Weekly"])
    
    if st.button("Set Budget"):
        session = Session()
        existing_budget = session.query(Budget).filter_by(category=category, period=period).first()
        
        if existing_budget:
            # Update the existing budget
            existing_budget.budget_amount = budget_amount
        else:
            # Create a new budget entry
            new_budget = Budget(category=category, budget_amount=budget_amount, period=period)
            session.add(new_budget)
        
        session.commit()
        session.close()
        st.success(f"Budget for {category} ({period}) set to ₹{budget_amount:,.2f}")


with st.expander("Budget Details", expanded=False):
    display_budget_overview()

# Add a button in the Reports section to send reports to email
with st.expander("Reports", expanded=False):
    st.subheader("Reports")
    transactions_df = fetch_transactions()

    # Line chart
    line_chart = px.line(transactions_df, x='Date', y='Amount', color='Category', title='Income and Expenses Over Time')
    st.plotly_chart(line_chart)

    # Scatter plot
    scatter_plot = px.scatter(transactions_df, x='Date', y='Amount', color='Category', title='Income and Expenses Scatter Plot')
    st.plotly_chart(scatter_plot)

    # Table report for both income and expenses
    st.subheader("Income Report")
    income_df = transactions_df[transactions_df['Type'] == 'Income']
    st.dataframe(income_df)

    st.subheader("Expense Report")
    expense_df = transactions_df[transactions_df['Type'] == 'Expense']
    st.dataframe(expense_df)

    st.write("---")

st.sidebar.title("Settings")
with st.sidebar:
    send_budget_email_notifications()
