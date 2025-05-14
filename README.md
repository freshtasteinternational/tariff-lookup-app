# tariff-lookup-app

This multi-country tariff estimator allows you to calculate customs duties for Canada, UK, and US based on 10-digit HS codes.

## How it works

1. Enter a 6-digit HS code, country of destination and of origin.
2. Follow the link to confirm the 10-digit code.
3. Enter other necessary data (values, quantity, etc.).
4. Get duty results.

## Run locally

```bash
streamlit run Canada_app.py
streamlit run UK_app.py
streamlit run US_app.py
