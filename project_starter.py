import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
import re
import json

# SET UP ENVIRONMENT AND MODEL
dotenv.load_dotenv()

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

client = AsyncOpenAI(max_retries=3, base_url="https://openai.vocareum.com/v1", api_key=os.getenv("UDACITY_OPENAI_API_KEY"))
model = OpenAIChatModel('gpt-5-nano', provider=OpenAIProvider(openai_client=client))

"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# ============================================================
# INVENTORY AGENT
# Manages all inventory-related tasks: checking stock levels,
# assessing reorder needs, and executing stock reordering.
# ============================================================

INVENTORY_SYSTEM_PROMPT = """You are the Inventory Management Agent for Munder Difflin Paper Company.
You are responsible for all inventory-related operations.

YOUR CAPABILITIES:
1. Check current stock levels for any item in the catalog
2. Assess whether items need reordering by comparing stock to minimum thresholds
3. Place stock orders to replenish inventory (after verifying cash availability)
4. Provide full inventory reports across all stocked items
5. Report on the company's financial position (cash, inventory value, top sellers)

WORKFLOW RULES:
- When asked about a specific item's stock: use check_stock_levels
- When asked if an item needs reordering: use check_reorder_status
- Before placing ANY stock order, you MUST:
  1. First call check_cash_balance_tool to verify funds are available
  2. Only then call place_stock_order if the cash balance covers the cost
- When asked for a full inventory overview: use get_full_inventory_report
- When asked about company finances: use get_company_financials

IMPORTANT CONSTRAINTS:
- Always use the EXACT item name from the catalog (e.g. 'A4 paper', not 'a4' or 'A4')
- Always pass the as_of_date parameter to every tool call
- Never place a stock order without first confirming sufficient cash balance
- If an item is not found in the catalog, report that clearly
- Report results with precise numbers: item names, quantities, costs, and dates
- When explicitly asked to respond in JSON format, do so
"""

inventory_agent = Agent(
    model,
    system_prompt=INVENTORY_SYSTEM_PROMPT,
)



@inventory_agent.tool_plain
def check_stock_levels(item_name: str, as_of_date: str) -> str:
    """Check the stock level for a given item as of a specific date.

    Args:
        item_name: The exact name of the item to check (e.g. 'A4 paper', 'Cardstock').
        as_of_date: The date to check stock as of, in ISO format (YYYY-MM-DD).

    Returns:
        A string describing the current stock level for the item.
    """
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])
    if current_stock > 0:
        return f"Item '{item_name}' has {current_stock} units in stock as of {as_of_date}."
    else:
        return f"Item '{item_name}' is OUT OF STOCK (0 units) as of {as_of_date}."


@inventory_agent.tool_plain
def check_reorder_status(item_name: str, as_of_date: str) -> str:
    """Check whether a given item needs to be reordered based on current stock vs minimum stock level.

    Args:
        item_name: The exact name of the item to check (e.g. 'A4 paper', 'Cardstock').
        as_of_date: The date to check stock as of, in ISO format (YYYY-MM-DD).

    Returns:
        A string indicating whether the item needs reordering with stock details.
    """
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])

    inventory_df = pd.read_sql(
        "SELECT min_stock_level, unit_price FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )

    if inventory_df.empty:
        return f"Item '{item_name}' is not found in the inventory catalog."

    min_stock_level = int(inventory_df["min_stock_level"].iloc[0])
    unit_price = float(inventory_df["unit_price"].iloc[0])

    if current_stock < min_stock_level:
        suggested_qty = (min_stock_level - current_stock) + 50
        cost = suggested_qty * unit_price
        delivery_date = get_supplier_delivery_date(as_of_date, suggested_qty)
        return (
            f"REORDER NEEDED: '{item_name}' has {current_stock} units, "
            f"below minimum of {min_stock_level}. "
            f"Suggested reorder: {suggested_qty} units at ${cost:.2f} "
            f"(${unit_price:.2f}/unit). Estimated delivery by {delivery_date}."
        )
    else:
        buffer = current_stock - min_stock_level
        return (
            f"NO REORDER NEEDED: '{item_name}' has {current_stock} units, "
            f"{buffer} units above minimum of {min_stock_level}."
        )


@inventory_agent.tool_plain
def place_stock_order(item_name: str, quantity: int, order_date: str) -> str:
    """Place a stock order to replenish inventory for a given item.

    Args:
        item_name: The exact name of the item to reorder.
        quantity: The number of units to order (positive integer).
        order_date: The date the order is placed, in ISO format (YYYY-MM-DD).

    Returns:
        A confirmation string or error message.
    """
    if quantity <= 0:
        return f"ERROR: Quantity must be positive. Received: {quantity}."

    # Look up unit price
    inventory_df = pd.read_sql(
        "SELECT unit_price FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )

    if inventory_df.empty:
        matching = [p for p in paper_supplies if p["item_name"] == item_name]
        if not matching:
            return f"ERROR: Item '{item_name}' not found in the product catalog."
        unit_price = matching[0]["unit_price"]
    else:
        unit_price = float(inventory_df["unit_price"].iloc[0])

    total_cost = quantity * unit_price

    # Check cash balance
    cash_balance = get_cash_balance(order_date)
    if total_cost > cash_balance:
        return (
            f"ERROR: Insufficient funds. Order cost ${total_cost:.2f} "
            f"exceeds cash balance ${cash_balance:.2f}."
        )

    # Record the transaction
    transaction_id = create_transaction(
        item_name=item_name,
        transaction_type="stock_orders",
        quantity=quantity,
        price=total_cost,
        date=order_date,
    )

    delivery_date = get_supplier_delivery_date(order_date, quantity)
    stock_df = get_stock_level(item_name, order_date)
    new_stock = int(stock_df["current_stock"].iloc[0])

    return (
        f"ORDER PLACED: {quantity} units of '{item_name}' at ${unit_price:.2f}/unit "
        f"(total: ${total_cost:.2f}). Transaction ID: {transaction_id}. "
        f"Delivery by {delivery_date}. New stock: {new_stock} units."
    )


@inventory_agent.tool_plain
def get_full_inventory_report(as_of_date: str) -> str:
    """Get a report of all items currently in inventory with their stock levels.

    Args:
        as_of_date: The date for the report, in ISO format (YYYY-MM-DD).

    Returns:
        A formatted string listing all inventory items and their stock levels.
    """
    inventory_dict = get_all_inventory(as_of_date)
    if not inventory_dict:
        return "No inventory found."
    lines = [f"  {name}: {stock} units" for name, stock in sorted(inventory_dict.items())]
    return f"Inventory as of {as_of_date}:\n" + "\n".join(lines)


@inventory_agent.tool_plain
def check_cash_balance_tool(as_of_date: str) -> str:
    """Check the current cash balance of the company.

    Args:
        as_of_date: The date to check the balance on, in ISO format (YYYY-MM-DD).

    Returns:
        A string stating the current cash balance.
    """
    balance = get_cash_balance(as_of_date)
    return f"Cash balance as of {as_of_date}: ${balance:.2f}"


@inventory_agent.tool_plain
def get_company_financials(as_of_date: str) -> str:
    """Get a complete financial report including cash, inventory value, and top sellers.

    Args:
        as_of_date: The date for the report, in ISO format (YYYY-MM-DD).

    Returns:
        A formatted financial summary string.
    """
    report = generate_financial_report(as_of_date)
    inventory_items = sorted(report["inventory_summary"], key=lambda x: x["value"], reverse=True)
    top_inventory = inventory_items[:10]
    inventory_lines = "\n".join(
        f"  - {item['item_name']}: {item['stock']} units @ ${item['unit_price']:.2f} = ${item['value']:.2f}"
        for item in top_inventory
    )
    top_sellers_lines = "\n".join(
        f"  - {p['item_name']}: {p['total_units']:.0f} units sold, ${p['total_revenue']:.2f} revenue"
        for p in report["top_selling_products"]
        if p.get("item_name") is not None and p.get("total_units") is not None
    ) if report["top_selling_products"] else "  - No sales recorded yet."
    if not top_sellers_lines:
        top_sellers_lines = "  - No sales recorded yet."

    return (
        f"=== FINANCIAL REPORT as of {report['as_of_date']} ===\n"
        f"Cash Balance: ${report['cash_balance']:.2f}\n"
        f"Inventory Value: ${report['inventory_value']:.2f}\n"
        f"Total Assets: ${report['total_assets']:.2f}\n"
        f"\nTop Inventory (by value):\n{inventory_lines}\n"
        f"\nTop Selling Products:\n{top_sellers_lines}"
    )


# ============================================================
# QUOTING AGENT
# Generates quotes for customers using historical data,
# applies bulk discounts and sales commission.
# ============================================================

QUOTING_SYSTEM_PROMPT = """You are the Quoting Agent for Munder Difflin Paper Company.
You generate accurate, itemized price quotes for customer requests.

YOUR CAPABILITIES:
1. Look up current pricing, stock availability, and delivery estimates for any item
2. Search historical quotes to find similar past orders and inform discount decisions
3. Calculate final prices with bulk discounts, sales commission, and loyalty discounts

WORKFLOW (follow for EVERY item in a request):
1. Call get_pricing_and_availability for each item to get base price, current stock, and delivery ETA
2. Call quote_history_tool with the customer's request to check for relevant past quotes
3. Based on quote history, decide on a loyalty discount rate (0.0 to 0.03):
   - No relevant history found: use 0.0 (no loyalty discount)
   - Customer has ordered similar items before: use 0.01 (1%)
   - Customer is a frequent buyer with large past orders: use 0.02-0.03 (2-3%)
4. Call apply_commission_and_discount with the item details and chosen discount rate

PRICING RULES:
- Bulk discounts (applied automatically by the tool):
  * 1-99 units: no bulk discount
  * 100-499 units: 5% bulk discount
  * 500-999 units: 10% bulk discount
  * 1000+ units: 15% bulk discount
- Sales commission: 5% is always added to the price after bulk discount
- Loyalty discount: 0-3% off the post-bulk price, based on customer history

OUTPUT FORMAT:
- Provide a clear, itemized quote for each item requested
- Include: item name, quantity, unit price, any discounts applied, final price
- Include stock availability status (sufficient/insufficient) and estimated delivery date
- If multiple items are requested, provide individual breakdowns plus a grand total
- Be professional and customer-friendly in your response
"""

quoting_agent = Agent(
    model,
    system_prompt=QUOTING_SYSTEM_PROMPT,
)



@quoting_agent.tool_plain
def get_pricing_and_availability(item_name: str, quantity: int, as_of_date: str) -> str:
    """Get current price, availability, and delivery estimate for an item.

    Args:
        item_name: The exact name of the item to check.
        quantity: The number of units being requested.
        as_of_date: The date to check, in ISO format (YYYY-MM-DD).

    Returns:
        A string with pricing, availability, and delivery information.
    """
    inventory_df = pd.read_sql(
        "SELECT unit_price FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )
    if inventory_df.empty:
        # Check paper_supplies as fallback
        matching = [p for p in paper_supplies if p["item_name"] == item_name]
        if not matching:
            return f"Item '{item_name}' not found in catalog."
        unit_price = matching[0]["unit_price"]
    else:
        unit_price = float(inventory_df["unit_price"].iloc[0])

    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])
    total_price = unit_price * quantity
    delivery_date = get_supplier_delivery_date(as_of_date, quantity)
    stock_status = "sufficient" if current_stock >= quantity else "insufficient"

    return (
        f"Item: {item_name}, Unit Price: ${unit_price:.2f}, "
        f"Total for {quantity} units: ${total_price:.2f}. "
        f"Current Stock: {current_stock} units ({stock_status}). "
        f"Estimated delivery: {delivery_date}."
    )


@quoting_agent.tool_plain
def quote_history_tool(customer_request: str) -> str:
    """Search past quotes based on a customer's request to inform discount decisions.

    Args:
        customer_request: The customer's request text to search for in quote history.

    Returns:
        A string with matching historical quotes or a message if none found.
    """
    # Extract search terms from the request
    words = re.findall(r'[a-zA-Z]+', customer_request.lower())
    # Filter to meaningful terms (skip common words)
    stop_words = {'the', 'a', 'an', 'for', 'of', 'and', 'to', 'in', 'on', 'at', 'i', 'we', 'need', 'want', 'please', 'would', 'like', 'order', 'request', 'date'}
    search_terms = [w for w in words if w not in stop_words and len(w) > 2][:5]

    if not search_terms:
        search_terms = words[:3]

    quotes = search_quote_history(search_terms)
    if not quotes:
        return "No similar past quotes found."
    return pd.DataFrame(quotes).to_string()


@quoting_agent.tool_plain
def apply_commission_and_discount(item_name: str, quantity: int, base_total: float, discount_rate: float) -> str:
    """Apply sales commission and loyalty discount to calculate final price.

    Args:
        item_name: The name of the item.
        quantity: Number of units.
        base_total: The base total price before commission and discounts.
        discount_rate: Loyalty discount rate as decimal (0.0 to 0.03).

    Returns:
        A string with the final quoted price including breakdown.
    """
    # Apply bulk discount
    if quantity >= 1000:
        bulk_discount = 0.15
    elif quantity >= 500:
        bulk_discount = 0.10
    elif quantity >= 100:
        bulk_discount = 0.05
    else:
        bulk_discount = 0.0

    bulk_discount_amount = base_total * bulk_discount
    price_after_bulk = base_total - bulk_discount_amount

    # Apply 5% sales commission
    commission = price_after_bulk * 0.05
    price_after_commission = price_after_bulk + commission

    # Apply loyalty discount
    loyalty_discount_amount = price_after_bulk * discount_rate
    final_price = price_after_commission - loyalty_discount_amount

    breakdown = f"Item: {item_name} ({quantity} units)\n"
    breakdown += f"  Base price: ${base_total:.2f}\n"
    if bulk_discount > 0:
        breakdown += f"  Bulk discount ({bulk_discount*100:.0f}%): -${bulk_discount_amount:.2f}\n"
    breakdown += f"  Sales commission (5%): +${commission:.2f}\n"
    if discount_rate > 0:
        breakdown += f"  Loyalty discount ({discount_rate*100:.1f}%): -${loyalty_discount_amount:.2f}\n"
    breakdown += f"  FINAL PRICE: ${final_price:.2f}"

    return breakdown


# ============================================================
# ORDERING AGENT
# Finalizes customer orders by creating sales transactions.
# ============================================================

ORDERING_SYSTEM_PROMPT = """You are the Ordering Agent for Munder Difflin Paper Company.
You are responsible for finalizing customer orders by creating sales transactions in the database.

YOUR CAPABILITIES:
1. Verify that sufficient stock is available to fulfill an order
2. Create sales transactions to complete customer purchases

WORKFLOW (follow for EVERY order):
1. Call check_stock_for_order to verify the item has enough stock for the requested quantity
2. Based on the result:
   - If STOCK SUFFICIENT: call finalize_order with the item name, quantity, price, and date
   - If STOCK INSUFFICIENT: do NOT attempt to finalize. Report clearly that the order
     cannot be fulfilled and state how many units are available vs. how many were requested.

CRITICAL RULES:
- NEVER finalize an order if stock is insufficient — this would corrupt the database
- Always use the EXACT item name as provided (e.g. 'A4 paper', 'Cardstock')
- Always pass the correct date in ISO format (YYYY-MM-DD)
- The price parameter in finalize_order is the TOTAL price for the order (not per-unit)
- After a successful order, report the transaction ID and remaining stock level
- If multiple items are requested, process each one individually
- If any item cannot be fulfilled, still attempt to fulfill the others that have stock

OUTPUT FORMAT:
- For successful orders: confirm item, quantity, total price, transaction ID, remaining stock
- For failed orders: state the item, requested quantity, available stock, and reason for failure
- Be concise and factual in your responses
"""

ordering_agent = Agent(
    model,
    system_prompt=ORDERING_SYSTEM_PROMPT,
)



@ordering_agent.tool_plain
def check_stock_for_order(item_name: str, quantity: int, as_of_date: str) -> str:
    """Check if sufficient stock is available to fulfill an order.

    Args:
        item_name: The exact name of the item.
        quantity: The number of units needed.
        as_of_date: The date to check, in ISO format (YYYY-MM-DD).

    Returns:
        A string indicating whether stock is sufficient for the order.
    """
    stock_df = get_stock_level(item_name, as_of_date)
    current_stock = int(stock_df["current_stock"].iloc[0])

    if current_stock >= quantity:
        return (
            f"STOCK SUFFICIENT: '{item_name}' has {current_stock} units available. "
            f"Order for {quantity} units can be fulfilled."
        )
    else:
        shortfall = quantity - current_stock
        return (
            f"STOCK INSUFFICIENT: '{item_name}' has only {current_stock} units, "
            f"but {quantity} are needed. Shortfall: {shortfall} units."
        )


@ordering_agent.tool_plain
def finalize_order(item_name: str, quantity: int, price: float, date: str) -> str:
    """Finalize a customer order by creating a sales transaction.

    Args:
        item_name: The exact name of the item being ordered.
        quantity: The number of units being ordered.
        price: The total price of the order.
        date: The date of the order, in ISO format (YYYY-MM-DD).

    Returns:
        A confirmation string with transaction ID or an error message.
    """
    # Verify stock one more time
    stock_df = get_stock_level(item_name, date)
    current_stock = int(stock_df["current_stock"].iloc[0])

    if current_stock < quantity:
        return (
            f"ERROR: Cannot finalize order. '{item_name}' has only {current_stock} units "
            f"but {quantity} are needed."
        )

    try:
        transaction_id = create_transaction(item_name, "sales", quantity, price, date)
        new_stock_df = get_stock_level(item_name, date)
        new_stock = int(new_stock_df["current_stock"].iloc[0])
        return (
            f"ORDER FINALIZED: {quantity} units of '{item_name}' sold for ${price:.2f}. "
            f"Transaction ID: {transaction_id}. Remaining stock: {new_stock} units."
        )
    except Exception as e:
        return f"ERROR finalizing order: {e}"


# ============================================================
# ORCHESTRATOR AGENT
# Coordinates between inventory, quoting, and ordering agents
# to handle end-to-end customer requests.
# ============================================================

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent for Munder Difflin Paper Company.
You are the primary point of contact for all customer inquiries. Your job is to coordinate
between specialized agents to fulfill customer requests end-to-end.

YOUR ROLE:
- Receive customer requests for paper products and supplies
- Use the handle_customer_request tool to process every request
- Present results to the customer in a clear, professional manner

WORKFLOW:
For every customer message, you MUST call handle_customer_request with:
1. user_request: the full text of what the customer asked for
2. as_of_date: the date mentioned in the request (in YYYY-MM-DD format)

The tool internally coordinates:
- Step 1: Quoting Agent generates an itemized quote with pricing and availability
- Step 2: Inventory Agent checks stock levels and reorders if needed
- Step 3: Ordering Agent finalizes sales for items with sufficient stock

RESPONSE RULES:
- Present the final result in clear, customer-friendly language
- Include relevant details: items, quantities, prices, delivery dates
- If an order was successful, confirm it with the transaction details
- If an order could not be fulfilled, explain why (out of stock, insufficient funds, etc.)
- If a discount was applied, mention it to the customer
- DO NOT reveal internal system details, raw error messages, or profit margins
- DO NOT mention agent names, tool names, or technical implementation details
- Keep responses professional, concise, and helpful
"""

orchestrator_agent = Agent(
    model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
)


def _normalize_item_names(user_request: str) -> str:
    """Find item names in user request and normalize them to catalog names."""
    pattern = re.compile(
        r'(\d[\d,]*\s+(?:sheets? of|reams? of|packets? of|of|)?\s*)([a-zA-Z0-9\s\(\)\'\"-]+?)(?=\n|,|\s+and\s+|\.|$)',
        re.IGNORECASE
    )
    return pattern.sub(lambda m: m.group(0), user_request)


@orchestrator_agent.tool_plain
def handle_customer_request(user_request: str, as_of_date: str) -> str:
    """Handle a customer's end-to-end request by coordinating quoting, inventory, and ordering.

    Args:
        user_request: The full text of the customer's request.
        as_of_date: The date for the request, in ISO format (YYYY-MM-DD).

    Returns:
        A string summarizing the outcome of the request.
    """
    normalized_request = _normalize_item_names(user_request)

    def _run_with_retry(agent, prompt, retries=3):
        for attempt in range(retries):
            try:
                result = agent.run_sync(prompt)
                return result.output
            except Exception as e:
                if attempt < retries - 1:
                    print(f"    Retry {attempt+1}/{retries} - {type(e).__name__}")
                    time.sleep(2)
                else:
                    return f"[Agent error after {retries} attempts: {type(e).__name__}]"

    # Step 1: Get a quote from the quoting agent
    quote_prompt = (
        f"Provide a detailed quote for the following request as of {as_of_date}: "
        f"{normalized_request}. "
        f"Include item name, quantity, total price, estimated delivery date, "
        f"current stock level, and whether stock is sufficient."
    )
    quote_text = _run_with_retry(quoting_agent, quote_prompt)

    # Step 2: Check inventory and determine if we can fulfill
    inventory_prompt = (
        f"Check stock levels for items in this request as of {as_of_date}: {normalized_request}. "
        f"For each item, report if stock is sufficient for the requested quantity. "
        f"If any item needs reordering, check if we have funds and place the order."
    )
    inventory_text = _run_with_retry(inventory_agent, inventory_prompt)

    # Step 3: Attempt to finalize orders for items with sufficient stock
    order_prompt = (
        f"Based on the following inventory status, finalize orders for items that have "
        f"sufficient stock as of {as_of_date}. Request: {normalized_request}. "
        f"Inventory status: {inventory_text}. "
        f"Quote details: {quote_text}."
    )
    order_text = _run_with_retry(ordering_agent, order_prompt)

    return (
        f"QUOTE:\n{quote_text}\n\n"
        f"INVENTORY STATUS:\n{inventory_text}\n\n"
        f"ORDER RESULT:\n{order_text}"
    )


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():

    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        # Use the orchestrator agent to handle the request (with retry for transient API errors)
        response = None
        for attempt in range(3):
            try:
                result = orchestrator_agent.run_sync(request_with_date)
                response = result.output
                break
            except Exception as e:
                if attempt < 2:
                    print(f"  Retry {attempt+1}/3 - {type(e).__name__}: {e}")
                    time.sleep(3)
                else:
                    response = f"[Failed after 3 attempts: {type(e).__name__}]"
                    print(f"  FAILED: {response}")

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
