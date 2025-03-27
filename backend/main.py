from fastapi import FastAPI
import mcd_outlet_scraper  # Import the scraper module

app = FastAPI()

@app.get("/run-script")
def run_script():
    """Endpoint to trigger the scraper script."""
    mcd_outlet_scraper.main()
    return {"message": "Scraper executed successfully"}
