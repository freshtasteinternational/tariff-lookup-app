from fastapi import FastAPI, Query
from app.us_scraper import confirm_10_digit_hs_code as confirm_us
from app.canada_scraper import confirm_10_digit_hs_code as confirm_canada, get_available_countries
from app.uk_scraper import confirm_10_digit_hs_code as confirm_uk

app = FastAPI()

@app.get("/confirm_hs_us")
def confirm_hs_us(hs_code: str):
    return {"confirmed_code": confirm_us(hs_code)}

@app.get("/confirm_hs_canada")
def confirm_hs_canada(hs_code: str, origin_country: str):
    available = get_available_countries()
    match = next((c for c in available if origin_country.lower() in c.lower()), None)
    if match:
        return {"confirmed_code": confirm_canada(hs_code, match)}
    return {"error": f"{origin_country} not found"}

@app.get("/confirm_hs_uk")
def confirm_hs_uk(hs_code: str):
    return {"confirmed_code": confirm_uk(hs_code)}
