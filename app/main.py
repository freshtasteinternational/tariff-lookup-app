from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.us_scraper import confirm_10_digit_hs_code as confirm_us
from app.canada_scraper import confirm_10_digit_hs_code as confirm_canada, get_available_countries, init_driver as init_canada_driver
from app.uk_scraper import confirm_10_digit_hs_code as confirm_uk

app = FastAPI()

# CORS — allow your frontend origin (or "*" for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with ["https://your-frontend-domain"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/confirm_hs_us")
def confirm_hs_us(hs_code: str, confirmed_code: str):
    """
    Open the US HTS search, let the user review, then return their confirmed 10-digit code.
    """
    return {"confirmed_code": confirm_us(hs_code, confirmed_code)}

@app.get("/confirm_hs_canada")
def confirm_hs_canada(hs_code: str, origin_country: str, confirmed_code: str):
    """
    Scrape available origin countries, pick the best match,
    open the Canada tariff finder, and return the user's confirmed 10-digit code.
    """
    # Launch headless driver just to get the list
    driver = init_canada_driver(headless=True)
    available = get_available_countries(driver)
    driver.quit()

    match = next((c for c in available if origin_country.lower() in c.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Origin country '{origin_country}' not found")

    return {"confirmed_code": confirm_canada(hs_code, match)}

@app.get("/confirm_hs_uk")
def confirm_hs_uk(hs_code: str, confirmed_code: str):
    """
    Open the UK tariff finder, let the user review, then return their confirmed 10-digit code.
    """
    return {"confirmed_code": confirm_uk(hs_code, confirmed_code)}
