# unified app.py

import streamlit as st
from Canada_logic import (
    init_driver as init_canada_driver,
    get_available_countries,
    open_tariff_page,
    scrape_tariff,
    UNIT_NAMES as CANADA_UNITS
)
from UK_logic import (
    init_driver as init_uk_driver,
    open_uk_tariff_finder_and_search,
    get_uk_tariff
)
from US_logic import (
    split_confirmed_code,
    get_us_tariff
)

st.set_page_config(page_title="Tariff Lookup App", layout="centered")
st.title("Multi-Country Tariff Lookup")
st.markdown("Use this tool to estimate import duties for Canada, the UK, and the US based on HS code and country of origin.")

# --- Select Country ---
st.header("1. Select Destination Country")
country = st.selectbox("Destination Country:", ["Canada", "United Kingdom", "United States"])

# --- Shared Inputs ---
st.header("2. Product Details")
hs_code_6 = st.text_input("Enter the 6-digit HS code:", max_chars=6)
confirmed_code = st.text_input("Enter the full 8- or 10-digit HS code after confirmation:")
origin_country = st.text_input("Enter the country of origin:")
customs_value = st.number_input("Enter the customs value (local currency):", min_value=0.0, value=1000.0)

# --- Canada Workflow ---
if country == "Canada":
    if st.button("Lookup Tariff"):
        driver = init_canada_driver(headless=True)
        countries = get_available_countries(driver)
        driver.quit()

        matched_country = next((c for c in countries if origin_country.lower() in c.lower()), None)
        if not matched_country:
            st.warning(f"'{origin_country}' not found. Defaulting to MFN (France).")
            dropdown_country = "France"
            country_code = "FR"
            force_mfn = True
        else:
            dropdown_country = matched_country
            country_code = matched_country[:2].upper()
            force_mfn = False

        if confirmed_code:
            driver = init_canada_driver(headless=True)
            driver = open_tariff_page(driver, confirmed_code, country_code)
            rate, basis, label, _ = scrape_tariff(driver, force_mfn)
            driver.quit()

            if basis != "value":
                friendly_basis = CANADA_UNITS.get(basis, basis + "s")
                quantity = st.number_input(f"Enter quantity in {friendly_basis}:", min_value=0.0)
                duty = quantity * rate
            else:
                duty = customs_value * rate

            total = customs_value + duty
            st.subheader("Tariff Result")
            st.write(f"**HS Code:** {confirmed_code}")
            st.write(f"**Origin Country:** {origin_country}")
            st.write(f"**Tariff Rate:** {rate*100:.2f}%")
            st.write(f"**Duty:** ${duty:.2f}")
            st.write(f"**Total Landed Cost:** ${total:.2f}")

# --- UK Workflow ---
elif country == "United Kingdom":
    if st.button("Lookup Tariff"):
        driver = init_uk_driver(headless=False)
        open_uk_tariff_finder_and_search(hs_code_6, driver)

    if confirmed_code:
        with st.spinner("Retrieving UK tariff data..."):
            driver = init_uk_driver(headless=True)
            result = get_uk_tariff(confirmed_code, origin_country, customs_value, 100, 50, driver)
            driver.quit()

        if result:
            st.subheader("Tariff Result")
            for k, v in result.items():
                st.write(f"**{k}:** {v}")
        else:
            st.warning("No tariff data found for the UK.")

# --- US Workflow ---
elif country == "United States":
    if st.button("Lookup Tariff"):
        if confirmed_code:
            quantity = st.text_input("Enter quantity (only if applicable to duty rate):")
            with st.spinner("Retrieving US tariff data..."):
                description, rate, duty = get_us_tariff(confirmed_code, origin_country, customs_value, quantity)
            if rate:
                total = customs_value + duty
                st.subheader("Tariff Result")
                st.write(f"**HS Code:** {confirmed_code}")
                st.write(f"**Description:** {description}")
                st.write(f"**Tariff Rate:** {rate}")
                st.write(f"**Duty:** ${duty:.2f}")
                st.write(f"**Total Landed Cost:** ${total:.2f}")
            else:
                st.warning("No tariff data found for the US.")
        else:
            st.warning("Please enter a full 8- or 10-digit HS code.")

