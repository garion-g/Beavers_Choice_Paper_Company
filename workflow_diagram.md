# Munder Difflin Multi-Agent System - Workflow Diagram

```mermaid
flowchart TD
    %% External Input
    Customer([Customer Inquiry]) -->|"text request + date"| OrchestratorAgent

    %% Orchestrator Agent
    subgraph OrchestratorAgent["Orchestrator Agent (pydantic-ai)"]
        direction TB
        O1[_normalize_item_names]
        O2[handle_customer_request]
        O1 --> O2
    end

    %% Delegation - Sequential Steps
    OrchestratorAgent -->|"Step 1: Get Quote"| QuotingAgent
    OrchestratorAgent -->|"Step 2: Check & Reorder Stock"| InventoryAgent
    OrchestratorAgent -->|"Step 3: Finalize Order"| OrderingAgent

    %% Inventory Agent
    subgraph InventoryAgent["Inventory Agent"]
        direction TB
        I1[check_stock_levels]
        I2[check_reorder_status]
        I3[check_cash_balance_tool]
        I4[place_stock_order]
        I5[get_full_inventory_report]
        I6[get_company_financials]
        I1 --> I2
        I2 -->|"Reorder needed"| I3
        I3 -->|"Funds available"| I4
    end

    %% Quoting Agent
    subgraph QuotingAgent["Quoting Agent"]
        direction TB
        Q1[get_pricing_and_availability]
        Q2[quote_history_tool]
        Q3[apply_commission_and_discount]
        Q1 --> Q2 --> Q3
    end

    %% Ordering Agent
    subgraph OrderingAgent["Ordering Agent"]
        direction TB
        R1[check_stock_for_order]
        R2[finalize_order]
        R1 -->|"Stock sufficient"| R2
    end

    %% Database Layer
    subgraph DB["SQLite Database (munder_difflin.db)"]
        direction LR
        T1[(transactions)]
        T2[(inventory)]
        T3[(quotes)]
        T4[(quote_requests)]
    end

    %% Utility Functions Layer
    subgraph Utils["Utility Functions"]
        direction TB
        U1[get_stock_level]
        U2[get_all_inventory]
        U3[create_transaction]
        U4[get_cash_balance]
        U5[get_supplier_delivery_date]
        U6[generate_financial_report]
        U7[search_quote_history]
    end

    %% Inventory Agent -> Utils
    I1 -->|"item_name, date"| U1
    I2 -->|"item_name, date"| U1
    I4 -->|"item, qty, price, date"| U3
    I4 -->|"date, qty"| U5
    I3 -->|"date"| U4
    I5 -->|"date"| U2
    I6 -->|"date"| U6

    %% Quoting Agent -> Utils
    Q1 -->|"item_name, date"| U1
    Q1 -->|"date, qty"| U5
    Q2 -->|"search terms"| U7

    %% Ordering Agent -> Utils
    R1 -->|"item_name, date"| U1
    R2 -->|"item, qty, price, date"| U3

    %% Utils -> DB
    U1 -.->|"read"| T1
    U2 -.->|"read"| T1
    U3 -.->|"write"| T1
    U4 -.->|"read"| T1
    U6 -.->|"read"| T1
    U6 -.->|"read"| T2
    U7 -.->|"read"| T3
    U7 -.->|"read"| T4

    %% Responses back to Orchestrator
    QuotingAgent -->|"quote with pricing"| OrchestratorAgent
    InventoryAgent -->|"stock status & reorder result"| OrchestratorAgent
    OrderingAgent -->|"order confirmation"| OrchestratorAgent

    %% Final output
    OrchestratorAgent -->|"formatted response"| Customer
```

## Agent Architecture

| Agent | Framework | Tools | Role |
|-------|-----------|-------|------|
| **Orchestrator Agent** | pydantic-ai | `handle_customer_request` | Receives customer inquiries, normalizes item names, coordinates specialist agents sequentially |
| **Inventory Agent** | pydantic-ai | `check_stock_levels`, `check_reorder_status`, `place_stock_order`, `get_full_inventory_report`, `check_cash_balance_tool`, `get_company_financials` | Manages stock levels, assesses reorder needs, places stock orders, reports financials |
| **Quoting Agent** | pydantic-ai | `get_pricing_and_availability`, `quote_history_tool`, `apply_commission_and_discount` | Generates quotes with bulk discounts (5-15%), loyalty discounts (0-3%), and 5% sales commission |
| **Ordering Agent** | pydantic-ai | `check_stock_for_order`, `finalize_order` | Verifies stock availability and creates sales transactions |

## Data Flow Summary

1. **Customer Inquiry** arrives as text with a request date
2. **Orchestrator** normalizes item names and calls `handle_customer_request`
3. **Quoting Agent** generates an itemized quote (pricing, stock status, delivery ETA)
4. **Inventory Agent** checks stock, reorders if needed (verifying cash balance first)
5. **Ordering Agent** finalizes sales for items with sufficient stock
6. **Results** are compiled and returned to the customer

## Sequence of Operations (handle_customer_request)

```
Customer Request
    |
    v
[Orchestrator] _normalize_item_names(request)
    |
    |--- Step 1 ---> [Quoting Agent].run_sync(quote_prompt)
    |                    |-> get_pricing_and_availability (price, stock, delivery)
    |                    |-> quote_history_tool (past quotes for discount decisions)
    |                    |-> apply_commission_and_discount (bulk + loyalty + commission)
    |                    |<- returns: itemized quote
    |
    |--- Step 2 ---> [Inventory Agent].run_sync(inventory_prompt)
    |                    |-> check_stock_levels (current stock)
    |                    |-> check_reorder_status (below minimum?)
    |                    |-> check_cash_balance_tool (funds available?)
    |                    |-> place_stock_order (replenish if needed)
    |                    |<- returns: stock status + reorder results
    |
    |--- Step 3 ---> [Ordering Agent].run_sync(order_prompt)
    |                    |-> check_stock_for_order (verify availability)
    |                    |-> finalize_order (create sales transaction)
    |                    |<- returns: order confirmation + transaction ID
    |
    v
Compiled Response -> Customer
```

## Discount Structure

| Order Size | Bulk Discount |
|-----------|---------------|
| 1-99 units | 0% |
| 100-499 units | 5% |
| 500-999 units | 10% |
| 1000+ units | 15% |

- **Sales Commission**: 5% added to all quotes
- **Loyalty Discount**: 0-3% based on quote history

## Delivery Timeline

| Order Quantity | Lead Time |
|--------------|-----------|
| 1-10 units | Same day |
| 11-100 units | 1 day |
| 101-1000 units | 4 days |
| 1000+ units | 7 days |
