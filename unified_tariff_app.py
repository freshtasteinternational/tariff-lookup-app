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
st.markdown("Use this tool to estimate import duties for Canada, the UK, and the US.")

# --- Step 1: Basic Info ---
st.header("Step 1: Enter Basic Product Information")
hs_code_6 = st.text_input("Enter the 6-digit HS code:")
origin_country = st.text_input("Enter the country of origin:")
destination_country = st.selectbox("Select destination country:", ["Canada", "United Kingdom", "United States"])

# --- Step 2: Show confirmation button and show external page link ---
if hs_code_6 and origin_country and destination_country:
    if st.button("Confirm full HS code and enter remaining data"):
        st.session_state.show_detail = True

        st.markdown("#### Open the relevant tariff search page to confirm your full HS code:")

        if destination_country == "United Kingdom":
            st.markdown(f"[UK Tariff Lookup](https://www.trade-tariff.service.gov.uk/headings/{hs_code_6})")

        elif destination_country == "Canada":
            st.markdown(f"[Canada Tariff Finder](https://www.tariffinder.ca/en/search#/tariff/{hs_code_6})")

        elif destination_country == "United States":
            st.markdown(f"[US HTS Lookup](https://hts.usitc.gov/search?query={hs_code_6})")

# --- Step 3: Detailed Input + Country Logic ---
if st.session_state.get("show_detail", False):
    st.header("Step 2: Final Product Details")
    confirmed_code = st.text_input("Enter the full 8- or 10-digit HS code:")
    customs_value = st.number_input("Enter the customs value (local currency):", min_value=0.0, value=1000.0)
    quantity = st.text_input("Enter quantity (if applicable):")

    if destination_country == "Canada":
        if st.button("Calculate Canada Tariff"):
            driver = init_canada_driver(headless=True)
            countries = get_available_countries(driver)
            driver.quit()

            matched_country = next((c for c in countries if origin_country.lower() in c.lower()), None)
            if not matched_country:
                st.warning(f"'{origin_country}' not found. Defaulting to MFN (France).")
                country_code = "FR"
                force_mfn = True
            else:
                country_code = matched_country[:2].upper()
                force_mfn = False

            driver = init_canada_driver(headless=True)
            driver = open_tariff_page(driver, confirmed_code, country_code)
            rate, basis, label, _ = scrape_tariff(driver, force_mfn)
            driver.quit()

            if basis != "value":
                friendly_basis = CANADA_UNITS.get(basis, basis + "s")
                try:
                    qty = float(quantity)
                    duty = qty * rate
                except:
                    st.error("Invalid quantity input.")
                    duty = 0.0
            else:
                duty = customs_value * rate

            total = customs_value + duty
            st.subheader("Tariff Result")
            st.write(f"**HS Code:** {confirmed_code}")
            st.write(f"**Tariff Rate:** {rate*100:.2f}%")
            st.write(f"**Duty:** ${duty:.2f}")
            st.write(f"**Total Landed Cost:** ${total:.2f}")

    elif destination_country == "United Kingdom":
        if st.button("Calculate UK Tariff"):
            driver = init_uk_driver(headless=True)
            result = get_uk_tariff(confirmed_code, origin_country, customs_value, 100, 50, driver)
            driver.quit()

            if result:
                st.subheader("Tariff Result")
                for k, v in result.items():
                    st.write(f"**{k}:** {v}")
            else:
                st.warning("No tariff data found for the UK.")

    elif destination_country == "United States":
        if st.button("Calculate US Tariff"):
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
