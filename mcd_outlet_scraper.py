import json
import time
import psycopg2
import paramiko
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# SSH Configuration
SSH_HOST = "ec2-3-27-228-44.ap-southeast-2.compute.amazonaws.com"
SSH_USER = "ec2-user"
SSH_KEY_PATH = "C:/Users/AdamLim/Downloads/ec2-database-connect.pem"

# AWS RDS Database Configuration
DB_HOST = "database-test1.cpgsc4aw269b.ap-southeast-2.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Remember121314"
DB_PORT = "5432"

# create connection. 
conn = psycopg2.connect(
    dbname=DB_NAME,  # Correct: should be DB_NAME, not DB_HOST
    user=DB_USER,    # Correct user
    password=DB_PASSWORD,  # Correct password
    host=DB_HOST,    # Correct host
    port=DB_PORT     # Correct port (should be an integer or string, NOT a hostname)
)

# execute postgresql command,

def setup_ssh():
    """
    Connects to EC2 via SSH and sets up PostgreSQL before running database operations.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)
        print("✅ Successfully connected to EC2 via SSH.")

        # Ensure PostgreSQL is installed
        commands = [
            "sudo dnf update -y",
            "sudo dnf install -y postgresql15",
        ]

        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode(), stderr.read().decode())

        return ssh  # Return SSH session to keep it open
    except Exception as e:
        print(f"❌ SSH Connection Error: {e}")
        return None

def setup_database():
    """
    Connects to PostgreSQL and creates the required table.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outlets (
                id SERIAL PRIMARY KEY,
                name TEXT,
                address TEXT,
                phone TEXT,
                waze_link TEXT,
                latitude FLOAT,
                longitude FLOAT
            );
        """)
        conn.commit()
        print("✅ PostgreSQL table setup complete.")
        return conn, cursor
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None, None

def setup_driver():
    """
    Initializes and configures the Selenium WebDriver.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_page_source(url):
    """
    Fetches the page source of the given URL using Selenium.
    """
    driver = setup_driver()
    driver.get(url)
    time.sleep(5)  # Allow JavaScript to load
    page_source = driver.page_source
    driver.quit()
    return page_source

def extract_outlets(html):
    """
    Extracts McDonald's outlet details from JSON-LD <script> tags.
    """
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
    """
    Filters McDonald's outlets in Kuala Lumpur.
    """
    return [
        outlet for outlet in outlets
        if "address" in outlet and "Kuala Lumpur" in outlet["address"]
    ]

def save_to_database(cursor, conn, outlets):
    """
    Saves McDonald's outlet data to PostgreSQL.
    """
    if not cursor or not conn:
        print("❌ Cannot insert data: Database connection not established.")
        return

    try:
        for outlet in outlets:
            cursor.execute("""
                INSERT INTO outlets (name, address, phone, waze_link, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (
                outlet.get('name', 'N/A'),
                outlet.get('address', 'N/A'),
                outlet.get('telephone', 'N/A'),
                outlet.get('url', 'N/A'),
                outlet.get('geo', {}).get('latitude', None),
                outlet.get('geo', {}).get('longitude', None)
            ))

        conn.commit()
        print("✅ Data successfully saved to PostgreSQL.")
    except Exception as e:
        print(f"❌ Database Insertion Error: {e}")

def display_outlets(outlets):
    """
    Displays the list of McDonald's outlets in Kuala Lumpur.
    """
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
        print("❌ No McDonald's outlets found in Kuala Lumpur.")

def main():
    """
    Main function to setup SSH, scrape, filter, display, and store McDonald's outlets in Kuala Lumpur.
    """
    ssh = setup_ssh()  # Connect to EC2 and setup PostgreSQL
    if ssh:
        conn, cursor = setup_database()  # Connect to PostgreSQL and setup table

        url = "https://www.mcdonalds.com.my/locate-us"
        html = get_page_source(url)
        outlets = extract_outlets(html)
        kl_outlets = filter_kl_outlets(outlets)

        display_outlets(kl_outlets)
        save_to_database(cursor, conn, kl_outlets)  # Save data before closing connection

        # Close database connection
        if conn:
            cursor.close()
            conn.close()
            print("✅ Database connection closed.")

        # Close SSH connection
        ssh.close()
        print("✅ SSH connection closed.")

if __name__ == "__main__":
    main()
