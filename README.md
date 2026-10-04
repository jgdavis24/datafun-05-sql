# datafun-05-sql

[![Workflow Guide](https://img.shields.io/badge/Pro--Guide-pro--analytics--02-green)](https://denisecase.github.io/pro-analytics-02/workflow-b-apply-example-project/)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![uv managed](https://img.shields.io/badge/uv-managed-DE5FE9)](https://docs.astral.sh/uv/)
[![ty type checked](https://img.shields.io/badge/ty-type_checked-2F80ED)](https://docs.astral.sh/ty/)
[![marimo](https://img.shields.io/badge/marimo-reactive_notebook-FF6B6B)](https://docs.marimo.io/)
[![SQLite](https://img.shields.io/badge/SQLite-database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Zensical docs](https://img.shields.io/badge/Zensical-docs-purple)](https://zensical.org/)
[![MIT](https://img.shields.io/badge/license-see%20LICENSE-yellow.svg)](./LICENSE)

> Does staff experience relate to store sales? A SQL and Python analysis of
> four related retail tables, and a look at why the answer is probably no.

## The Question

Classmates working this dataset tested two things against store sales. Store
square footage came back at r = 0.185. Employee headcount came back at
r = 0.335. Both weak.

Average staff tenure is the obvious third variable and nobody had run it. The
employees table carries `years_employed`, so it is a straight average per
store.

## Results

Tenure and total sales correlate at **r = -0.287**. Negative, which runs
opposite to the hypothesis.

| Store | Avg tenure | Transactions | Total sales |
|---|---|---|---|
| Bayou Crossing | 7.60 | 7 | $787 |
| Peachtree Center | 7.41 | 8 | $1,585 |
| ... | | | |
| Canyon Center | 4.23 | 10 | $1,666 |
| Harbor Point | 4.00 | 12 | $2,388 |

The longest-tenured store had the lowest sales. The shortest-tenured store had
the highest.

![Staff tenure vs total sales](docs/images/tenure-vs-sales.png)

The scatter is a cloud. That matters more than the correlation coefficient
does.

## Why That Result Is Not The Finding

Reading -0.287 as "experience hurts sales" would be wrong, for two reasons.

First, n = 15 stores. A correlation this weak sits inside what random
variation produces at that sample size.

Second, something else explains total sales much better:

| Variable | r vs total sales |
|---|---|
| Transaction count | **0.742** |
| Average sale amount | **0.649** |
| Employee count | 0.335 |
| Average tenure | -0.287 |

Transaction count and average sale amount are independent of each other
(r = -0.009), so they are two separate drivers rather than one restated twice.
Together they account for most of the variation, and tenure is left explaining
noise.

Bayou Crossing shows it plainly. 7 transactions and the lowest total. Harbor
Point had 12 and the highest.

## The Transferable Part

Store size, headcount, and tenure are all attributes of the store.

Transaction count is a component of the thing being explained. Total sales is
transactions multiplied by average ticket, so of course it tracks them.

Correlating a total against store attributes will usually lose to correlating
it against its own components. Worth checking the decomposition before
reaching for an explanatory variable.

## The SQL

Employees and sales both hang off `store_id`. Joining them together in one
pass multiplies rows: a store with 18 employees and 40 sales returns 720 rows,
and every count and sum computed from that is wrong.

Each side is aggregated separately first, then the summaries are joined.

```sql
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
```

## Data

Four related CSV files in `data/retail`:

- `region.csv` - one row per region
- `store.csv` - one row per store, with square footage and type
- `employee.csv` - one row per employee, with role and years employed
- `sale.csv` - one row per sale transaction, with amount and payment type

15 stores across 5 regions. Pandas loads the CSVs into SQLite, SQL does the
joining and aggregation, and the result comes back to pandas as a DataFrame
for charting.

## Skills Demonstrated

- Multi-table SQL with CTEs and aggregate-then-join to avoid row multiplication
- Correlation analysis and reading a weak result honestly
- Loading related CSVs into SQLite with pandas
- Charting query results with matplotlib
- Structured logging to a persistent project log
- src-layout Python packaging managed with uv
- Ruff formatting and linting, ty type checking
- CI/CD through GitHub Actions with hosted documentation

## Produced Artifacts

- [**Reactive App (marimo)**](https://jgdavis24.github.io/datafun-05-sql/app/)
  - run the analysis interactively in a browser

- [**Reactive Notebook (marimo)**](./src/datafun/notebook.py)
  - view the Python source used to create the reactive app

## Run It Yourself

```shell
git clone https://github.com/jgdavis24/datafun-05-sql
cd datafun-05-sql
code .
```

Then in a VS Code terminal:

```shell
uv sync
uv run python -m datafun.app
```

Two chart windows open. Close both to let the script finish. A `project.log`
appears in the root folder and the terminal prints:

```shell
===================================
END main() - Executed successfully!
===================================
```

<details>
<summary>Show full command reference</summary>

```shell
uv self update
uv python pin 3.14
uv python install
uv lock --upgrade
uv sync

uv run pre-commit install
uv run pre-commit autoupdate

git add -A
uv run pre-commit run --all-files
# repeat if changes were made by pre-commit tasks
git add -A
uv run pre-commit run --all-files

# run the Python module
uv run python -m datafun.app

# run marimo nb as a reactive app
# press Ctrl + C in the terminal to exit
uv run marimo run src/datafun/notebook.py

# Or: run marimo nb as a notebook
uv run marimo edit src/datafun/notebook.py

# do chores
uv run ruff format .
uv run ruff check . --fix
uv run ty check
uv run python -m pytest
uv run python -m zensical build

# save progress as you work
git add -A
git commit -m "your message here"
# repeat if changes were made (try the UP ARROW)
git add -A
git commit -m "your message here"

git push -u origin main
```

</details>

## Notes on Tooling

Run **both** ruff commands before pushing. `ruff format` and `ruff check` are
different tools and passing one does not mean passing the other. On this
project format changed a file while check passed clean, so running only check
would have left CI red.

If VS Code does not use the project's `.venv`, open the Command Palette
(`Ctrl+Shift+P`) and run **Python: Select Interpreter**, then pick the
interpreter from this project's `.venv` folder.

## Documentation

- [Documentation](https://jgdavis24.github.io/datafun-05-sql/)

## Citation

- [CITATION.cff](./CITATION.cff)

## License

This project is licensed under the [MIT License](./LICENSE).
