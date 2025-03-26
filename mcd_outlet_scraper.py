import os
import json
import time
import paramiko
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

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

# SQL Command to Create `outlets` Table
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS outlets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(50),
    waze_link TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# PostgreSQL Command to Run on EC2
PSQL_COMMAND = f'PGPASSWORD="{DB_PASSWORD}" psql --host={DB_HOST} --port={DB_PORT} --dbname={DB_NAME} --username={DB_USER} -c "{SQL_SETUP}"'

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
    """Initializes Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
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
    """Extracts outlet details from JSON-LD <script> tags."""
    soup = BeautifulSoup(html, "html.parser")
    outlets = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                outlets.extend(data)
            else:
                outlets.append(data)
        except json.JSONDecodeError:
            continue
    return outlets

def filter_kl_outlets(outlets):
    """Filters outlets in Kuala Lumpur."""
    return [
        outlet for outlet in outlets
        if "address" in outlet and "Kuala Lumpur" in outlet["address"]
    ]
def save_to_database(outlets):
    """Saves outlet data to the PostgreSQL database via SSH."""
    if not outlets:
        print("❌ No outlets to save.")
        return

    # Start SQL transaction
    sql_commands = ["BEGIN;"]

    for outlet in outlets:
        name = outlet.get('name', 'N/A').replace("'", "''")
        address = outlet.get('address', 'N/A').replace("'", "''")
        phone = outlet.get('telephone', 'N/A').replace("'", "''")
        waze_link = outlet.get('url', 'N/A').replace("'", "''")
        latitude = outlet.get('geo', {}).get('latitude', 'NULL')
        longitude = outlet.get('geo', {}).get('longitude', 'NULL')

        sql_command = f"""
        INSERT INTO outlets (name, address, phone, waze_link, latitude, longitude)
        VALUES ('{name}', '{address}', '{phone}', '{waze_link}', {latitude}, {longitude})
        ON CONFLICT (name) DO UPDATE 
        SET address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            waze_link = EXCLUDED.waze_link,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude;
        """
        sql_commands.append(sql_command)

    # Commit transaction
    sql_commands.append("COMMIT;")

    full_sql_command = " ".join(sql_commands)

    # Execute the SQL command over SSH
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

def display_outlets(outlets):
    """Displays outlets in Kuala Lumpur."""
    print("\n=== McDonald's Outlets in Kuala Lumpur ===")
    if outlets:
        for outlet in outlets:
            print(f"🏢 Name: {outlet.get('name', 'N/A')}")
            print(f"📍 Address: {outlet.get('address', 'N/A')}")
            print(f"📞 Phone: {outlet.get('telephone', 'N/A')}")
            print(f"🌍 Waze Link: {outlet.get('url', 'N/A')}")
            print(f"📌 Coordinates: {outlet.get('geo', {}).get('latitude', 'N/A')}, {outlet.get('geo', {}).get('longitude', 'N/A')}")
            print("-" * 50)
    else:
        print("❌ No outlets found in Kuala Lumpur.")

def main():
    """Main function to connect, scrape, filter, display, and store outlets."""
    ssh = setup_ssh()
    if ssh:
        url = "https://www.mcdonalds.com.my/locate-us"
        html = get_page_source(url)
        outlets = extract_outlets(html)
        kl_outlets = filter_kl_outlets(outlets)
        display_outlets(kl_outlets)
        save_to_database(kl_outlets)
        print("✅ Database commands executed.")
        ssh.close()
        print("✅ SSH connection closed.")

if __name__ == "__main__":
    main()
