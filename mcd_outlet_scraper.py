import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    """
    Initializes and configures the Selenium WebDriver.
    Returns:
        WebDriver object
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_page_source(url):
    """
    Fetches the page source of the given URL using Selenium.
    Args:
        url (str): The webpage URL to scrape.
    Returns:
        str: The HTML page source.
    """
    driver = setup_driver()
    driver.get(url)

    # Wait for JavaScript content to load
    time.sleep(5)

    page_source = driver.page_source
    driver.quit()
    return page_source


def extract_outlets(html):
    """
    Extracts McDonald's outlet details from JSON-LD <script> tags.
    Args:
        html (str): The HTML source of the page.
    Returns:
        list[dict]: A list of outlet data dictionaries.
    """
    soup = BeautifulSoup(html, "html.parser")
    outlets = []

    # Find all JSON-LD <script> tags and parse JSON data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                outlets.extend(data)
            else:
                outlets.append(data)
        except json.JSONDecodeError:
            continue  # Skip invalid JSON

    return outlets


def filter_kl_outlets(outlets):
    """
    Filters McDonald's outlets that are located in Kuala Lumpur.
    Args:
        outlets (list[dict]): The list of outlet data dictionaries.
    Returns:
        list[dict]: A list of Kuala Lumpur outlets.
    """
    return [
        outlet for outlet in outlets
        if "address" in outlet and "Kuala Lumpur" in outlet["address"]
    ]


def display_outlets(outlets):
    """
    Displays the list of McDonald's outlets in Kuala Lumpur.
    Args:
        outlets (list[dict]): The list of filtered Kuala Lumpur outlets.
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
        print("❌ No McDonald's outlets found in Kuala Lumpur. Check the website structure.")


def main():
    """
    Main function to scrape, filter, and display McDonald's outlets in Kuala Lumpur.
    """
    url = "https://www.mcdonalds.com.my/locate-us"
    html = get_page_source(url)
    outlets = extract_outlets(html)
    kl_outlets = filter_kl_outlets(outlets)
    display_outlets(kl_outlets)


if __name__ == "__main__":
    main()
