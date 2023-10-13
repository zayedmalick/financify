import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Data  # Replace 'your_project_file' with your actual project file

# Create the SQLite database connection using SQLAlchemy
engine = create_engine('sqlite:///data.db')
Session = sessionmaker(bind=engine)
session = Session()

# Define categories for income and expenses
income_categories = ["Salary", "Freelance", "Investment", "Gifts", "Other"]
expense_categories = ["Rent", "Groceries", "Utilities", "Transportation", "Entertainment", "Healthcare", "Education", "Other"]

# Generate one month of random financial data
start_date = datetime.now() - timedelta(days=30)
end_date = datetime.now()

while start_date <= end_date:
    category = random.choice(income_categories + expense_categories)
    transaction_type = "Income" if category in income_categories else "Expense"
    amount = round(random.uniform(100, 10000), 2)  # Random amount in INR

    financial_data = Data(category=category, type=transaction_type, amount=amount, date=start_date)
    session.add(financial_data)

    # Move to the next day
    start_date += timedelta(days=1)

session.commit()
session.close()
