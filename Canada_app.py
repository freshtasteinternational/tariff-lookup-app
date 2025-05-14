import streamlit as st
from Canada_logic import (
    init_driver, get_available_countries, confirm_10_digit_hs_code,
    scrape_tariff, open_tariff_page, UNIT_NAMES
)

st.set_page_config(page_title="Canada Tariff Lookup", layout="centered")
st.title("Canada HS Code Tariff Lookup Tool")
st.markdown("Get MFN/FTA duty rates based on HS code and origin country.")

# --- Section 1: HS and Origin Input ---
st.header("1. Product Details")
hs_code_6 = st.text_input("Enter the 6-digit HS code:", max_chars=6)
origin_country = st.text_input("Enter the country of origin:")

if st.button("Start Lookup"):
    with st.spinner("Loading available countries..."):
        driver = init_driver(headless=True)
        countries = get_available_countries(driver)
        driver.quit()

    matched_country = next((c for c in countries if origin_country.lower() in c.lower()), None)
    if not matched_country:
        st.warning(f"'{origin_country}' not found. Defaulting to MFN (France).")
        dropdown_country = "France"
        country_code = "FR"
        force_mfn = True
    else:
        st.success(f"Matched country: {matched_country}")
        dropdown_country = matched_country
        country_code = matched_country[:2].upper()
        force_mfn = False

    st.markdown("**Now please go to [Tariff Finder](https://www.tariffinder.ca/en/getStarted)** and use the HS and country to find the full 10-digit code.")
    confirmed_hs_code = st.text_input("Then enter the full 10-digit HS code below:")

    if confirmed_hs_code:
        with st.spinner("Scraping tariff data..."):
            driver = init_driver(headless=True)
            driver = open_tariff_page(driver, confirmed_hs_code, country_code)
            tariff_rate, basis, tariff_type = scrape_tariff(driver, force_mfn)
            driver.quit()

        # --- Quantity or Value input based on tariff basis ---
        if basis != "value":
            friendly_basis = UNIT_NAMES.get(basis, basis + "s")
            quantity = st.number_input(f"Enter quantity in {friendly_basis}:", min_value=0.0)
            customs_value = 0.0
            duty = quantity * tariff_rate
        else:
            customs_value = st.number_input("Enter the customs value (CAD):", min_value=0.0)
            duty = customs_value * tariff_rate

        total = customs_value + duty

        # --- Display results ---
        st.subheader("Tariff Result")
        st.write(f"**HS Code:** {confirmed_hs_code}")
        st.write(f"**Origin Country:** {origin_country}")
        st.write(f"**Tariff Source:** {tariff_type}")
        st.write(f"**Tariff Basis:** {basis}")
        st.write(f"**Tariff Rate:** {tariff_rate * 100:.2f}%")
        if basis != "value":
            st.write(f"**Quantity:** {quantity} {friendly_basis}")
        st.write(f"**Customs Value (CAD):** ${customs_value:.2f}")
        st.write(f"**Duty Amount:** ${duty:.2f}")
        st.write(f"**Total Landed Cost:** ${total:.2f}")

