import requests
import os
import sys
import json
from datetime import datetime
from bs4 import BeautifulSoup

# Base URL for the website
BASE_URL = os.getenv("BASE_URL", "http://agora.ex.nii.ac.jp")

# Path to the "data" folder
DATA_FOLDER = "data"

# def get_resource_path(relative_path):
#     """Get the absolute path to the resource file, works both in development and PyInstaller bundle."""
#     if getattr(sys, 'frozen', False):
#         # If running in a bundled PyInstaller app
#         base_path = sys._MEIPASS
#     else:
#         # If running in development mode
#         base_path = os.path.dirname(os.path.abspath(__file__))
    
#     return os.path.join(base_path, relative_path)

# def ensure_data_folder():
#     """Ensure that the data folder exists next to the 'scripts' folder."""
#     # Get the base directory of the 'data' folder relative to the project root
#     data_path = get_resource_path('data')

#     # Ensure the 'data' folder exists, create it if it doesn't
#     if not os.path.exists(data_path):
#         os.makedirs(data_path)

    # return data_path

def fetch_main_page(year="2024"):
    """Fetch the main typhoon page for the given year."""
    main_url = f"{BASE_URL}/digital-typhoon/year/wnp/{year}.html.en"
    response = requests.get(main_url)
    if response.status_code != 200:
        print(f"Failed to retrieve main webpage: {response.status_code}")
        return None
    return response.text

def get_typhoon_links(page_html):
    """Extract typhoon summary links from the main page HTML."""
    soup = BeautifulSoup(page_html, 'html.parser')
    links = [a_tag["href"] for a_tag in soup.find_all("a", href=True) if "/digital-typhoon/summary/wnp/s" in a_tag["href"]]
    return links

def fetch_typhoon_details(link):
    """Fetch detailed typhoon track information from a given link."""
    full_url = BASE_URL + link
    print(f"Visiting {full_url}...")
    response = requests.get(full_url)
    if response.status_code != 200:
        print(f"Failed to retrieve {full_url}: {response.status_code}")
        return None
    return response.text

def extract_typhoon_track(detail_page_html):
    """Extract detailed track data from the typhoon's track page."""
    soup = BeautifulSoup(detail_page_html, 'html.parser')
    typhoon_name = soup.find("div", class_="TYNAME").text.strip().lstrip().replace("Typhoon", "", 1).lstrip()

    # Find the link to the detailed track information
    detail_link_tag = soup.find("a", string="Detailed Track Information")
    if not detail_link_tag:
        print(f"No 'Detailed Track Information' link found for {typhoon_name}")
        return None

    detail_link = detail_link_tag["href"]
    detail_full_url = BASE_URL + detail_link
    print(f"Found Detailed Track Information at {detail_full_url}")

    # Fetch the detailed track data
    detail_response = requests.get(detail_full_url)
    if detail_response.status_code != 200:
        print(f"Failed to retrieve {detail_full_url}: {detail_response.status_code}")
        return None

    # Parse the detailed track page
    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
    track_table = detail_soup.find("table", class_="TRACKINFO")
    if not track_table:
        print(f"No TRACKINFO table found")
        return None

    # Parse table headers
    headers = [header.text.strip() for header in track_table.find_all("th")]
    typhoon_track = []

    for tr in track_table.find_all("tr")[1:]:  # Skip header row
        cells = tr.find_all("td")
        row = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
        
        # Construct the time string
        time_str = f"{row['Year']}-{row['Month']}-{row['Day']} {row['Hour']}:00"

        lat = float(row['Lat.'])
        long = float(row['Long.'])
        wind_speed = int(row['Wind (kt)'])
        pressure = int(row['Pressure (hPa)'])

        # Convert wind speed from knots to km/h
        wind_speed_kmh = int(wind_speed * 1.852) 

        # Determine the typhoon class based on the Saffir-Simpson scale
        if wind_speed_kmh < 64:  # Below Tropical Storm
            typhoon_class = 0  
        elif 64 <= wind_speed_kmh < 118:  # Tropical Storm
            typhoon_class = 1
        elif 118 <= wind_speed_kmh < 154:  # Category 1
            typhoon_class = 2
        elif 154 <= wind_speed_kmh < 178:  # Category 2
            typhoon_class = 3
        elif 178 <= wind_speed_kmh < 209:  # Category 3
            typhoon_class = 4
        elif 209 <= wind_speed_kmh < 252:  # Category 4
            typhoon_class = 5
        else:  # Category 5
            typhoon_class = 5

        # Assign modified wind speed for visualization purposes
        modified_wind_speed = str(wind_speed_kmh) if wind_speed_kmh >= 64 else "< 64"

        # Append to the typhoon track list
        typhoon_track.append({
            "time": time_str,
            "lat": lat,
            "long": long,
            "class": typhoon_class,
            "speed": modified_wind_speed,
            "pressure": pressure
        })

    if typhoon_track:
        return {"name": typhoon_name, "path": typhoon_track}
    return None

def load_cache(year, folder_path="data"):
    """Load cached data for the specified year if it exists."""
    cache_file = os.path.join(folder_path, f"typhoon_data_{year}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            try:
                data = json.load(file)
                print(f"Loaded data from cache: {cache_file}")
                return data
            except json.JSONDecodeError:
                print(f"Error loading cache file {cache_file}. Scraping new data.")
                return None
    return None

def save_cache(data, year, folder_path="data"):
    """Save the scraped data to a year-specific cache file."""
    cache_file = os.path.join(folder_path, f"typhoon_data_{year}.json")
    with open(cache_file, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data cached to file: {cache_file}")

def scrape_typhoon_data(year=None):
    """Main function to scrape all typhoon data for the specified year, using cache if available."""
    if year is None:
        year = datetime.now().year  # Default to current year if not provided

    cached_data = load_cache(year)
    if cached_data:
        return cached_data  # Return cached data if available

    # Otherwise, scrape the data
    main_page_html = fetch_main_page(str(year))
    if main_page_html is None:
        return []

    typhoon_data = []
    links = get_typhoon_links(main_page_html)

    for link in links:
        detail_page_html = fetch_typhoon_details(link)
        if detail_page_html is None:
            continue

        typhoon_info = extract_typhoon_track(detail_page_html)
        if typhoon_info:
            typhoon_data.append(typhoon_info)

    # Cache the newly scraped data
    if typhoon_data:
        save_cache(typhoon_data, year)

    return typhoon_data
