import logging
import os
import json
import shutil
import paramiko
import time
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from googlemaps import Client as GoogleMaps
from fastapi import FastAPI, HTTPException
import requests
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.0.13:3000", "http://localhost:3000", "https://mindhive-assessment.onrender.com", "https://mindhive-assessment-2.onrender.com"],  # Replace with ["http://192.168.0.16:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load environment variables
load_dotenv()

# SSH Configuration
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")

# AWS RDS Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
REACT_APP_GOOGLE_MAPS_API_KEY = os.getenv('REACT_APP_GOOGLE_MAPS_API_KEY')

# SQL Command to Create `outlets` Table
SQL_SETUP = """
CREATE TABLE outlets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,  -- Ensure name is unique
    address TEXT,
    phone VARCHAR(50),
    waze_link TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    services TEXT,  -- Added services column
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# PostgreSQL Command to Run on EC2
PSQL_COMMAND = f'PGPASSWORD="{DB_PASSWORD}" psql --host={DB_HOST} --port={DB_PORT} --dbname={DB_NAME} --username={DB_USER} -c "{SQL_SETUP}"'


# Initialize Google Maps Client
gmaps = GoogleMaps(key=REACT_APP_GOOGLE_MAPS_API_KEY)


def setup_ssh():
    """Connects to EC2 via SSH and runs PostgreSQL setup."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)

        print("✅ Connected to EC2 via SSH.")

        # Execute PostgreSQL setup via SSH
        print("🔄 Running PostgreSQL setup on EC2...")
        stdin, stdout, stderr = ssh.exec_command(PSQL_COMMAND)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if output:
            print(f"✅ SQL Output:\n{output}")
        if error:
            print(f"❌ SQL Error:\n{error}")

        return ssh
    except Exception as e:
        print(f"❌ SSH Connection Error: {e}")
        return None

def setup_driver():
    """Initializes Selenium WebDriver with headless Chromium for better compatibility."""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # ✅ Fixes memory issues on Render
    
    # Explicitly specify the Chrome binary location (try this if using Render.com)
    chrome_options.binary_location = "/usr/bin/google-chrome"  


    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)



def get_page_source(url):
    """Fetches page source using Selenium."""
    driver = setup_driver()
    driver.get(url)
    time.sleep(5)
    page_source = driver.page_source
    driver.quit()
    return page_source

def extract_outlets(html):
    """Extracts outlet details and assigns the correct services to each location."""
    soup = BeautifulSoup(html, "html.parser")
    outlets = []

    # Extract each outlet's data from JSON-LD scripts
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                outlets.extend(data)
            else:
                outlets.append(data)
        except json.JSONDecodeError:
            continue

    # Find all outlets' containers
    outlet_divs = soup.find_all("div", class_="addressBox")  # Adjusted to match the outlet block

    for i, outlet_div in enumerate(outlet_divs):
        # Find all service tooltips within this specific outlet
        service_icons = outlet_div.find_all("span", class_="ed-tooltiptext")
        services = [service.text.strip() for service in service_icons]

        # Assign the extracted services **only to the matching outlet**
        if i < len(outlets):
            outlets[i]["services"] = services

    return outlets


def save_to_excel(outlets, filename="outlets.xlsx"):
    """Saves outlet data to an Excel spreadsheet in the same folder."""
    if not outlets:
        print("❌ No outlets to save.")
        return

    data = []
    for outlet in outlets:
        data.append({
            "Name": outlet.get("name", "N/A"),
            "Address": outlet.get("address", "N/A"),
            "Phone": outlet.get("telephone", "N/A"),
            "Waze Link": outlet.get("url", "N/A"),
            "Latitude": outlet.get("geo", {}).get("latitude", "N/A"),
            "Longitude": outlet.get("geo", {}).get("longitude", "N/A"),
            "Services": ", ".join(outlet.get("services", []))  # Convert list to comma-separated string

        })

    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"✅ Data saved to {filename}")

def filter_kl_outlets(outlets):
    """Filters outlets in Kuala Lumpur."""
    return [
        outlet for outlet in outlets
        if "address" in outlet and "Kuala Lumpur" in outlet["address"]
    ]
def save_to_database(outlets):
    """Saves outlet data and services to the PostgreSQL database via SSH."""
    if not outlets:
        print("❌ No outlets to save.")
        return

    sql_commands = ["BEGIN;"]

    for outlet in outlets:
        name = outlet.get('name', 'N/A').replace("'", "''")
        address = outlet.get('address', 'N/A').replace("'", "''")
        phone = outlet.get('telephone', 'N/A').replace("'", "''")
        waze_link = outlet.get('url', 'N/A').replace("'", "''")

        coordinates = geocode_address(outlet.get('address', ''))
        latitude = coordinates["latitude"] if coordinates["latitude"] is not None else "NULL"
        longitude = coordinates["longitude"] if coordinates["longitude"] is not None else "NULL"

        # Convert list of services to a string
        services = ", ".join(outlet.get("services", [])).replace("'", "''")

        sql_command = f"""
        INSERT INTO outlets (name, address, phone, waze_link, latitude, longitude, services)
        VALUES ('{name}', '{address}', '{phone}', '{waze_link}', {latitude}, {longitude}, '{services}')
        ON CONFLICT (name) DO UPDATE 
        SET address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            waze_link = EXCLUDED.waze_link,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            services = EXCLUDED.services;
        """
        sql_commands.append(sql_command)

    sql_commands.append("COMMIT;")
    full_sql_command = " ".join(sql_commands)

    ssh = setup_ssh()
    if ssh:
        try:
            print("🔄 Executing SQL commands on EC2...")
            stdin, stdout, stderr = ssh.exec_command(f'PGPASSWORD="{DB_PASSWORD}" psql --host={DB_HOST} --port={DB_PORT} --dbname={DB_NAME} --username={DB_USER} -c "{full_sql_command}"')

            output = stdout.read().decode()
            error = stderr.read().decode()

            if output:
                print(f"✅ SQL Output:\n{output}")
            if error:
                print(f"❌ SQL Error:\n{error}")
        except Exception as e:
            print(f"❌ Database Insertion Error: {e}")
        finally:
            ssh.close()
            print("✅ SSH connection closed.")





def geocode_address(address):
    """Retrieves latitude and longitude for a given address using Google Maps API."""
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return {"latitude": location["lat"], "longitude": location["lng"]}
        else:
            print(f"❌ Geocoding failed: No results for {address}")
            return {"latitude": None, "longitude": None}
    except Exception as e:
        print(f"❌ Geocoding error for {address}: {e}")
        return {"latitude": None, "longitude": None}


def enrich_outlets_with_coordinates(outlets):
    """Adds latitude and longitude to outlets using Google Maps API."""
    for outlet in outlets:
        if "geo" not in outlet or not outlet["geo"]:
            latitude, longitude = geocode_address(outlet.get("address", ""))
            if latitude and longitude:
                outlet["geo"] = {"latitude": latitude, "longitude": longitude}
    return outlets


def display_outlets(outlets):
    """Displays outlets in Kuala Lumpur along with services."""
    print("\n=== McDonald's Outlets in Kuala Lumpur ===")
    if outlets:
        for outlet in outlets:
            print(f"🏢 Name: {outlet.get('name', 'N/A')}")
            print(f"📍 Address: {outlet.get('address', 'N/A')}")
            print(f"📞 Phone: {outlet.get('telephone', 'N/A')}")
            print(f"🌍 Waze Link: {outlet.get('url', 'N/A')}")
            print(f"📌 Coordinates: {outlet.get('geo', {}).get('latitude', 'N/A')}, {outlet.get('geo', {}).get('longitude', 'N/A')}")
            print(f"🎉 Services: {', '.join(outlet.get('services', []))}")
            print("-" * 50)
    else:
        print("❌ No outlets found in Kuala Lumpur.")


@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI McDonald's Outlet Scraper!"}


@app.get("/scrape/")
def scrape_mcdonalds():
    try :
        """Scrapes McDonald's outlets and returns a JSON response."""
        url = "https://www.mcdonalds.com.my/locate-us"
        html = get_page_source(url)
        outlets = extract_outlets(html)
        kl_outlets = filter_kl_outlets(outlets)
        kl_outlets = enrich_outlets_with_coordinates(kl_outlets)

        return {"outlets": kl_outlets}
    except Exception as e:
        logging.error(f"Error in /scrape endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    




# Set up Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
# Initialize the Gemini model
model = genai.GenerativeModel("gemini-1.5-flash-latest")
# Load CSV data into a Pandas DataFrame
csv_file = "chat-data-outlets.csv"
df = pd.read_csv(csv_file, delimiter=",", quotechar='"', on_bad_lines="skip")

@app.get("/chat/{query}")
async def chat(query: str):
    """Answer user's query based on the outlets.csv file using Gemini API."""
    try:
        # Convert DataFrame to a structured text format for querying
        outlet_data = df.to_dict(orient="records")
        context = "Here is a list of McDonald's outlets with their details: " + str(outlet_data)

        # Generate a response from Gemini
        response = model.generate_content(f"{context}\n\nUser query: {query}")
        
        # Return the generated response
        return {"answer": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def main():
    """Main function to connect, scrape, filter, display, and store outlets."""
    ssh = setup_ssh()
    if ssh:
        url = "https://www.mcdonalds.com.my/locate-us"
        html = get_page_source(url)
        outlets = extract_outlets(html)
        kl_outlets = filter_kl_outlets(outlets)
        kl_outlets = enrich_outlets_with_coordinates(kl_outlets)  # Add coordinates using Google Maps APIz
        display_outlets(kl_outlets)
        save_to_database(kl_outlets)
        save_to_excel(kl_outlets)  # Save data to Excel
        print("✅ Database and Excel export completed.")
        print("✅ Database commands executed.")
        ssh.close()
        print("✅ SSH connection closed.")

if __name__ == "__main__":
    main()
