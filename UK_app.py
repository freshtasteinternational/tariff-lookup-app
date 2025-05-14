import streamlit as st
from UK_logic import (
    init_driver,
    open_uk_tariff_finder_and_search,
    get_user_confirmation,
    get_uk_tariff
)

st.set_page_config(page_title="UK HS Code Tariff Lookup", layout="centered")
st.title("UK Tariff Lookup Tool")
st.markdown("Estimate UK import tariffs using the HS code and country of origin.")

# --- Section 1: Inputs ---
st.header("1. Basic Inputs")
hs_code_6_digit = st.text_input("Enter the 6-digit HS code:", max_chars=6)
origin_country = st.text_input("Enter the country of origin (e.g., 'Estonia'):")
customs_value = st.number_input("Customs Value (GBP):", min_value=0.0, value=1000.0)
shipping_cost = st.number_input("Shipping Cost (GBP):", min_value=0.0, value=100.0)
insurance_cost = st.number_input("Insurance Cost (GBP):", min_value=0.0, value=50.0)

# --- Step 2: Confirmation & Launch ---
if st.button("Start Lookup"):
    with st.spinner("Opening UK Tariff Finder for HS code confirmation..."):
        driver = init_driver(headless=False)
        driver = open_uk_tariff_finder_and_search(hs_code_6_digit, driver)

    selected_code = st.text_input("Enter the correct 10-digit HS code after reviewing the UK Tariff Finder site:")

    if selected_code:
        driver.quit()  # Close visible browser
        with st.spinner("Retrieving UK tariff details in headless mode..."):
            driver2 = init_driver(headless=True)
            result = get_uk_tariff(selected_code, origin_country, customs_value, shipping_cost, insurance_cost, driver2)
            driver2.quit()

        if result:
            st.header("Tariff Summary")
            for k, v in result.items():
                st.write(f"**{k}:** {v}")
        else:
            st.warning("No tariff data could be retrieved.")
