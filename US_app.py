import streamlit as st
from US_logic import (
    open_hts_search_page,
    scrape_rows,
    find_best_match,
    parse_tariff_info,
    find_special_rate,
    interpret_duty,
    split_confirmed_code
)

st.set_page_config(page_title="US HS Code Tariff Lookup", layout="centered")
st.title("US Tariff Lookup Tool")
st.markdown("Estimate US import tariffs using the HS code and country of origin.")

# --- Section 1: Inputs ---
st.header("1. Basic Inputs")
hs_code_6_digit = st.text_input("Enter the 6-digit HS code:", max_chars=6)
origin_country = st.text_input("Enter the country of origin (e.g., 'Mexico'):")
customs_value = st.number_input("Customs Value (USD):", min_value=0.0, value=1000.0)

if st.button("Start Lookup"):
    if not hs_code_6_digit or not origin_country:
        st.warning("Please enter both HS code and country of origin.")
    else:
        with st.spinner("Opening HTS Search Page for HS code confirmation..."):
            driver = open_hts_search_page(hs_code_6_digit)
            rows = scrape_rows(driver)

        st.markdown("**Now please visit [HTS Search](https://hts.usitc.gov/search?query="" + hs_code_6_digit + ") to confirm the full 8- or 10-digit code.**")
        confirmed_code = st.text_input("Then enter the full 8- or 10-digit HS code below:")

        if confirmed_code:
            heading_code, stat_suffix = split_confirmed_code(confirmed_code)
            idx = find_best_match(driver, confirmed_code, rows)

            if idx is not None:
                with st.spinner("Retrieving tariff data..."):
                    description, general, special, country_mapping = parse_tariff_info(driver, idx)
                    special_rate = find_special_rate(special, country_mapping, origin_country)
                    applicable_rate = special_rate if special_rate else general
                    duty = interpret_duty(driver, applicable_rate, customs_value)
                    driver.quit()

                total_cost = customs_value + duty

                st.subheader("Tariff Result")
                st.write(f"**HS Code:** {confirmed_code}")
                st.write(f"**Origin Country:** {origin_country}")
                st.write(f"**Applicable Rate Used:** {applicable_rate}")
                st.write(f"**Customs Value (USD):** ${customs_value:.2f}")
                st.write(f"**Duty Amount:** ${duty:.2f}")
                st.write(f"**Total Landed Cost:** ${total_cost:.2f}")
            else:
                st.error("No matching HS code found.")

