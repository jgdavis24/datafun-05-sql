"""src/datafun/app.py - Project script.

Author: Josiah Davis
Date: 2026-10

HOW TO RUN THIS FILE:

From the VS Code menu (with only this project open in VS Code),
click "Terminal" / New Terminal to
open an integrated Terminal in the root project folder.
Paste the following command and press ENTER or RETURN
to run this file as a script:

uv run python -m datafun.app

DOMAIN:

A small business with regions, stores, employees, and sales.

The data is stored in four related CSV files:

- one row per region
- one row per store
- one row per employee
- one row per sale

One region can have many stores.
One store can have many employees.
One store can have many sales.

CUSTOM PROBLEM:

Does staff experience relate to store sales?

Classmates in this module tested store size against sales and
employee count against sales. Both came back weakly correlated.
Average staff tenure is the obvious third variable and it has not
been tested, so this project runs it.

EXPLORE:

Sometimes the information needed for an analysis
is stored in more than one related table.

SQL is especially useful when tables share keys
and we want to analyze information across them.

A simple Python and SQL process is:

1. LOAD the related tables.
2. INSPECT the grain and keys.
3. CREATE a SQLite database.
4. LOAD the tables into SQLite.
5. QUERY across related tables with SQL.
6. VISUALIZE the query result with Python.
7. SUMMARIZE what you found.
8. DISPLAY the visualization.

DESIGN:

Use this file to declare the data-specific choices
and the reasoning behind them,
then orchestrate the work.

SQLite comes from the Python Standard Library.
Pandas loads tabular data into SQLite
and returns SQL query results as DataFrames.
Reusable visualization functions come from eda-vizkit.

The SQL stays here because the query is an
analytical decision specific to this project.
"""

# === DECLARE IMPORTS (BRING IN FREE CODE) ===

import logging
from pathlib import Path
import sqlite3
from typing import Final

from datafun_toolkit.logger import get_logger, log_header, log_path
from eda_vizkit import save_chart
import matplotlib.pyplot as plt
import pandas as pd

# === CONFIGURE LOGGER ONCE FOR THE APPLICATION ===

LOG: logging.Logger = get_logger("P05", level="DEBUG")

# === DECLARE GLOBAL CONSTANTS ===

# Some global variables are CONSTANT.
# They do NOT change while the program runs.
# By convention, constants use UPPERCASE_WITH_UNDERSCORES.
# Final indicates that the value should not be reassigned.

# === LOCATE THE DATA FILES ===

DATA_DIR: Final[Path] = Path("data") / "retail"

REGION_FILE: Final[Path] = DATA_DIR / "region.csv"
STORE_FILE: Final[Path] = DATA_DIR / "store.csv"
EMPLOYEE_FILE: Final[Path] = DATA_DIR / "employee.csv"
SALE_FILE: Final[Path] = DATA_DIR / "sale.csv"

# === LOCATE THE SQLITE DATABASE ===

DATABASE_FILE: Final[Path] = DATA_DIR / "business.sqlite"

# === LOCATE THE CHART OUTPUT ===

CHART_DIR: Final[Path] = Path("docs") / "images"
CHART_PATH: Final[Path] = CHART_DIR / "first-chart.png"
SCATTER_PATH: Final[Path] = CHART_DIR / "tenure-vs-sales.png"

# === DETERMINE WHAT ONE ROW REPRESENTS ===

REGION_GRAIN: Final[str] = "one business region"
STORE_GRAIN: Final[str] = "one store"
EMPLOYEE_GRAIN: Final[str] = "one employee"
SALE_GRAIN: Final[str] = "one sale transaction"

# === DESCRIBE THE TABLE RELATIONSHIPS ===

RELATIONSHIP_DECISION: Final[str] = r"""
The data is stored in four related tables.

One region can have many stores.
The stores table uses region_id to identify each store's region.

One store can have many employees.
The employees table uses store_id to identify each employee's store.

One store can have many sales.
The sales table also uses store_id.

That last point matters. Employees and sales both hang off store_id,
so joining all three tables at once multiplies rows. A store with 18
employees and 40 sales would return 720 rows, and every count and sum
computed from that would be wrong.

The fix is to aggregate each side separately first, then join the
summaries together on store_id.
"""

# === DEFINE THE ANALYTICAL QUESTION ===

CUSTOM_QUERY_DECISION: Final[str] = r"""
Does staff experience relate to store sales?

The employees table carries years_employed, so average tenure per
store is a straight average. The sales table carries sale_amount,
so total sales per store is a straight sum.

The result should have one row per store, with average tenure,
employee count, and total sales side by side.
"""

# === WRITE THE SQL QUERY ===

CUSTOM_SQL_QUERY: Final[str] = """
WITH employee_summary AS (
    SELECT
        store_id,
        COUNT(employee_id) AS employee_count,
        ROUND(AVG(years_employed), 2) AS avg_tenure_years
    FROM employees
    GROUP BY store_id
),
sales_summary AS (
    SELECT
        store_id,
        COUNT(sale_id) AS transaction_count,
        ROUND(SUM(sale_amount), 2) AS total_sales,
        ROUND(AVG(sale_amount), 2) AS avg_sale_amount
    FROM sales
    GROUP BY store_id
)
SELECT
    s.store_name,
    r.region_name,
    e.employee_count,
    e.avg_tenure_years,
    sa.transaction_count,
    sa.avg_sale_amount,
    sa.total_sales
FROM stores AS s
JOIN regions AS r
    ON s.region_id = r.region_id
JOIN employee_summary AS e
    ON s.store_id = e.store_id
JOIN sales_summary AS sa
    ON s.store_id = sa.store_id
ORDER BY
    e.avg_tenure_years DESC;
"""

# === CHOOSE A VISUALIZATION ===

CUSTOM_CHART_DECISION: Final[str] = r"""
The question is whether two numeric values move together,
so a scatter plot is the right choice rather than a bar chart.

Average tenure goes on the x axis and total sales on the y axis,
with one point per store. If experience drives sales the points
should trend upward.

A bar chart of tenure by store is also produced, since that shows
how much the stores actually differ before looking at any
relationship.
"""


# === DEFINE THE MAIN FUNCTION ===


def main() -> None:
    """Entry point when running this file as a Python script.

    This is where the instructions begin.

    Arguments: None.
    Returns: None.
    """
    log_header(LOG, "P05 - PYTHON AND SQL")

    LOG.info("===================================")
    LOG.info("START main()")
    LOG.info("===================================")

    LOG.info("-------------------------------")
    LOG.info("01. LOAD the related tables.")
    LOG.info("-------------------------------")

    log_path(LOG, "regions file", path=REGION_FILE)
    log_path(LOG, "stores file", path=STORE_FILE)
    log_path(LOG, "employees file", path=EMPLOYEE_FILE)
    log_path(LOG, "sales file", path=SALE_FILE)

    regions_df: pd.DataFrame = pd.read_csv(REGION_FILE)
    stores_df: pd.DataFrame = pd.read_csv(STORE_FILE)
    employees_df: pd.DataFrame = pd.read_csv(EMPLOYEE_FILE)
    sales_df: pd.DataFrame = pd.read_csv(SALE_FILE)

    LOG.info("Related tables loaded successfully.")

    LOG.info("-------------------------------")
    LOG.info("02. INSPECT the grain and keys.")
    LOG.info("-------------------------------")

    LOG.info(f"Regions grain: {REGION_GRAIN}")
    LOG.info(f"Stores grain: {STORE_GRAIN}")
    LOG.info(f"Employees grain: {EMPLOYEE_GRAIN}")
    LOG.info(f"Sales grain: {SALE_GRAIN}")

    LOG.info(f"Regions columns: {regions_df.columns.tolist()}")
    LOG.info(f"Stores columns: {stores_df.columns.tolist()}")
    LOG.info(f"Employees columns: {employees_df.columns.tolist()}")
    LOG.info(f"Sales columns: {sales_df.columns.tolist()}")

    LOG.info(RELATIONSHIP_DECISION)

    LOG.info("-------------------------------")
    LOG.info("03. CREATE a SQLite database.")
    LOG.info("-------------------------------")

    log_path(LOG, "SQLite database", path=DATABASE_FILE)

    connection: sqlite3.Connection = sqlite3.connect(DATABASE_FILE)

    LOG.info("SQLite database connection created.")

    LOG.info("-------------------------------")
    LOG.info("04. LOAD the tables into SQLite.")
    LOG.info("-------------------------------")

    regions_df.to_sql(
        "regions",
        connection,
        if_exists="replace",
        index=False,
    )

    stores_df.to_sql(
        "stores",
        connection,
        if_exists="replace",
        index=False,
    )

    employees_df.to_sql(
        "employees",
        connection,
        if_exists="replace",
        index=False,
    )

    sales_df.to_sql(
        "sales",
        connection,
        if_exists="replace",
        index=False,
    )

    LOG.info("Related tables loaded into SQLite.")

    LOG.info("-------------------------------")
    LOG.info("05. QUERY across related tables with SQL.")
    LOG.info("-------------------------------")

    LOG.info(CUSTOM_QUERY_DECISION)
    LOG.info(f"\nSQL query:\n{CUSTOM_SQL_QUERY}")

    result_df: pd.DataFrame = pd.read_sql_query(
        CUSTOM_SQL_QUERY,
        connection,
    )

    LOG.info(f"\nQuery result:\n{result_df}")

    # === CUSTOM: MEASURE THE RELATIONSHIPS ===

    # Compare every candidate explanation against total sales,
    # not just the one the question started with.

    tenure_corr: float = result_df["avg_tenure_years"].corr(result_df["total_sales"])
    headcount_corr: float = result_df["employee_count"].corr(result_df["total_sales"])
    transaction_corr: float = result_df["transaction_count"].corr(
        result_df["total_sales"]
    )
    ticket_corr: float = result_df["avg_sale_amount"].corr(result_df["total_sales"])
    volume_vs_ticket_corr: float = result_df["transaction_count"].corr(
        result_df["avg_sale_amount"]
    )

    LOG.info("Correlations against total sales:")
    LOG.info(f"  transaction count:   {transaction_corr:.3f}")
    LOG.info(f"  average sale amount: {ticket_corr:.3f}")
    LOG.info(f"  employee count:      {headcount_corr:.3f}")
    LOG.info(f"  average tenure:      {tenure_corr:.3f}")
    LOG.info(f"Transaction count vs average sale amount: {volume_vs_ticket_corr:.3f}")

    LOG.info("-------------------------------")
    LOG.info("06. VISUALIZE the query result with Python.")
    LOG.info("-------------------------------")

    LOG.info(CUSTOM_CHART_DECISION)

    tenure_ax = result_df.plot.bar(
        x="store_name",
        y="avg_tenure_years",
        legend=False,
    )

    # CUSTOM: The analyst can customize the returned Matplotlib Axes object.
    tenure_ax.set_title("Average Staff Tenure by Store")
    tenure_ax.set_xlabel("Store")
    tenure_ax.set_ylabel("Average Years Employed")

    CHART_DIR.mkdir(parents=True, exist_ok=True)

    save_chart(
        tenure_ax,
        CHART_PATH,
    )

    scatter_ax = result_df.plot.scatter(
        x="avg_tenure_years",
        y="total_sales",
    )

    scatter_ax.set_title(f"Staff Tenure vs Total Sales (r = {tenure_corr:.3f})")
    scatter_ax.set_xlabel("Average Years Employed")
    scatter_ax.set_ylabel("Total Sales ($)")

    save_chart(
        scatter_ax,
        SCATTER_PATH,
    )

    LOG.info(f"Charts saved at {CHART_PATH} and {SCATTER_PATH}.")

    LOG.info("-------------------------------")
    LOG.info("07. SUMMARIZE what you found.")
    LOG.info("-------------------------------")

    # Run this app first.
    # Review the SQL result and visualization.
    # Then record your CUSTOM observations
    # in a simple multi-line raw string.

    LOG.info(r"""CUSTOM OBSERVATIONS:
    Average staff tenure and total sales correlate at r = -0.287.
    That is negative, which runs opposite to the hypothesis. The
    store with the longest-tenured staff (Bayou Crossing, 7.60 years)
    had the lowest sales at $787. The store with the shortest tenure
    (Harbor Point, 4.00 years) had the highest at $2,388.

    I do not think this means experience hurts sales.

    Two things argue against reading it that way. First, n = 15
    stores, so a correlation this weak sits well inside what random
    variation produces. Second, something else explains total sales
    much better:

        transaction count vs total sales    r =  0.742
        average sale amount vs total sales  r =  0.649
        employee count vs total sales       r =  0.335
        average tenure vs total sales       r = -0.287

    Transaction count and average sale amount are independent of each
    other (r = -0.009), so they are two separate drivers. Together
    they account for most of the variation in total sales, and tenure
    is left explaining noise.

    Bayou Crossing shows it plainly. 7 transactions and the lowest
    total. Harbor Point had 12 and the highest. The gap in sales is
    mostly a gap in how many sales happened.

    As a cross-check, my employee count figure of 0.335 matches what
    a classmate reported for the same comparison on this dataset,
    calculated independently.

    The useful conclusion is about which variable to reach for. Store
    size, headcount, and tenure are all attributes of the store.
    Transaction count is a component of the thing being explained.
    Correlating a total against store attributes will usually lose to
    correlating it against its own components.
    """)

    LOG.info("-------------------------------")
    LOG.info("08. DISPLAY the visualization.")
    LOG.info("-------------------------------")

    LOG.info("In a script, call plt.show() at the end to display all charts.")
    LOG.info("Close all chart windows (with the close button) to continue.")

    plt.show()

    connection.close()

    LOG.info("===================================")
    LOG.info("END main() - Executed successfully!")
    LOG.info("===================================")


# === CONDITIONAL EXECUTION GUARD ===

# WHY: This is standard Python "boilerplate" - we copy and paste it
# into every Python script. It is a "conditional execution" guard,
# meaning: if this file is being run as a script, then execute the code
# in the main() function.

if __name__ == "__main__":
    main()
