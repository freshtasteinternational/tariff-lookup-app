# Tariff Backend

This project contains a FastAPI backend with Selenium-powered endpoints for confirming HS codes (US, UK, Canada).

## Endpoints

- `/confirm_hs_us?hs_code=040410`  
- `/confirm_hs_canada?hs_code=040410&origin_country=France`  
- `/confirm_hs_uk?hs_code=040410`

## Deploying to Render

1. Push this repo to GitHub
2. Go to [https://dashboard.render.com](https://dashboard.render.com)
3. Create a new Web Service, link your GitHub repo
4. Set build type to Docker
5. Start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

Ensure your Render service has enough RAM (~512MB+) to run headless Chrome.
