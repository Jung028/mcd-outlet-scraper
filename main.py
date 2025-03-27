from fastapi import FastAPI
import backend.mcd_outlet_scraper  # Import the scraper module

app = FastAPI()

@app.get("/run-script")
def run_script():
    """Endpoint to trigger the scraper script."""
    backend.mcd_outlet_scraper.main()
    return {"message": "Scraper executed successfully"}
