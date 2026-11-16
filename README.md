# smartpay-purchase-cards

A notebook for GSA SmartPay's monthly charge-card statistics: spend, transactions and card counts by agency and card type, October 2008 onward. Open `smartpay_purchase_cards.ipynb`.

The notebook downloads GSA's "Stats Tool" spreadsheet from https://smartpay.gsa.gov/about/statistics/ when it runs; the data isn't stored here. The spreadsheet has no breakdown by transaction size or merchant, so it can't isolate micro-purchases.

    uv run --with jupyter --with pandas --with openpyxl --with matplotlib jupyter lab smartpay_purchase_cards.ipynb

`build_notebook.py` writes the notebook.
