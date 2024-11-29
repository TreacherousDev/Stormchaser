import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Base URL of the website
BASE_URL = "https://ncics.org/ibtracs/index.php"
BASE_URL_ALT = "https://ncics.org/ibtracs/"

BASIN_ABBREVIATIONS = {
    "Northern Atlantic": "na",
    "Eastern Pacific" : "ep",
    "Western Pacific": "wp",
    "Northern Indian": "ni",
    "Southern Indian": "si"
    # "Southern Pacific": "sp"
}

def fetch_year_page(year):
    """Fetch the page for the given year."""
    url = f"{BASE_URL}?name=YearBasin-{year}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page for year {year}: {response.status_code}")
        return None
    return response.text

def extract_links_from_second_table(html):
    """Extract and organize links for each typhoon basin."""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table', {'class': 'ishade', 'summary': 'Layout table.'})
    
    if len(tables) < 2:
        print("Less than two tables found on the page.")
        return None
    
    table = tables[1]
    
    headers = table.find('tr').find_all('td')
    basins = [header.text.strip() for header in headers]
    
    basin_links = {basin: [] for basin in basins}
    
    rows = table.find_all('tr')[1:]
    for row in rows:
        cells = row.find_all('td')
        for index, cell in enumerate(cells):
            links = cell.find_all('a', href=True)
            for link in links:
                basin_links[basins[index]].append(f"{BASE_URL_ALT}{link['href']}")
    
    return basin_links

def scrape_fourth_table(link):
    """Scrape the fourth table from the given link."""
    response = requests.get(link)
    if response.status_code != 200:
        print(f"Failed to retrieve page: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    
    if len(tables) < 4:
        print("Less than four tables found on the page.")
        return None

    table = tables[3]
    rows = table.find_all('tr')
    table_data = []
    
    for row in rows[2:]:
        cells = row.find_all(['td', 'th'])
        row_data = [cell.text.strip() for cell in cells]
        table_data.append(row_data)
    
    return table_data

def scrape_typhoon_links(year):
    """Main function to scrape typhoon links for each basin for a given year."""
    page_html = fetch_year_page(year)
    if page_html is None:
        return None
    basin_links = extract_links_from_second_table(page_html)
    return basin_links

def add_missing_dates_and_empty_cells(data):
    """Add missing dates and fill empty cells by referencing the row above, or N / A for the first row."""
    last_date = None
    last_row = None

    # Ensure the first row is filled with "N / A" for empty cells
    if data:
        data[0] = ['N / A' if not cell else cell for cell in data[0]]

    for row in data:  # Iterate directly over rows instead of using enumerate
        datetime_cell = row[1]
        
        # Handle missing dates
        if " " in datetime_cell:
            last_date = datetime_cell.split()[0]
        else:
            row[1] = f"{last_date} {datetime_cell}" if last_date else datetime_cell

        # Fill empty cells by referencing the previous row
        for i, cell in enumerate(row):
            if cell == "N / A":
                row[i] = None
            elif not cell and last_row:  # Fill with value from the last row
                row[i] = last_row[i]

        last_row = row  # Update the last_row reference

    return data


def get_typhoon_name_from_link(link):
    """Extract the typhoon name from the first link's page."""
    response = requests.get(link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        name_element = soup.find('h1')
        if name_element:
            return name_element.get_text(strip=True)
    return None

def save_cache(data, year, basin_name, folder_path="data"):
    """Save the scraped data to a basin and year-specific cache file."""

    basin_abbr = BASIN_ABBREVIATIONS.get(basin_name, "unknown")
    if basin_abbr == "unknown":
        print(f"Warning: No abbreviation found for basin '{basin_name}'. Using 'unknown'.")
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Format the filename using basin abbreviation and year
    cache_file = os.path.join(folder_path, f"{basin_abbr}_{year}_data.json")
    
    with open(cache_file, "w") as file:
        json.dump(data, file, indent=4)
    
    print(f"Data cached to file: {cache_file}")


def load_cache(year, basin_name, folder_path="data"):
    """Load cached data for the specified basin and year if it exists."""

    basin_abbr = BASIN_ABBREVIATIONS.get(basin_name, "unknown")
    if basin_abbr == "unknown":
        print(f"Warning: No abbreviation found for basin '{basin_name}'. Using 'unknown'.")
    
    # Construct the cache file path
    cache_file = os.path.join(folder_path, f"{basin_abbr}_{year}_data.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            try:
                data = json.load(file)
                print(f"Loaded data from cache: {cache_file}")
                return data
            except json.JSONDecodeError:
                print(f"Error loading cache file {cache_file}. Scraping new data.")
                return None
    else:
        print(f"Cache file not found: {cache_file}")
    return None


def save_data_as_json(year, basin_name, folder_path="data"):
    """Save typhoon data from all links in a single JSON file."""
    links_by_basin = scrape_typhoon_links(year)
    if not links_by_basin:
        print("No data available for the specified year.")
        return None

    basin_name = basin_name.strip()
    if basin_name not in links_by_basin:
        print(f"Basin '{basin_name}' not found. Available basins are:")
        for basin in links_by_basin.keys():
            print(f" - {basin}")
        return None

    print(f"Links for {basin_name} in {year}:")
    for link in links_by_basin[basin_name]:
        print(link)

    if not links_by_basin[basin_name]:
        print(f"No links available for basin '{basin_name}'.")
        return None

    all_typhoon_data = []

    for link in links_by_basin[basin_name]:
        print(f"\nFetching typhoon name from {link}...")
        typhoon_name = get_typhoon_name_from_link(link)
        
        if not typhoon_name:
            print(f"Failed to extract typhoon name for {link}. Skipping.")
            continue
        
        # Split the string into words
        composite_name = typhoon_name.split()

        # Get the second-to-last word
        if len(composite_name) >= 2:
            typhoon_name = composite_name[-2]
        else:
            typhoon_name = "UNKNOWN"

        print(f"Fetching data from {link}...")
        fourth_table_data = scrape_fourth_table(link)
        
        if not fourth_table_data:
            print(f"Failed to extract data from the fourth table for {link}. Skipping.")
            continue

        processed_data = add_missing_dates_and_empty_cells(fourth_table_data)

        typhoon_data = {
            "name": typhoon_name,
            "path": []
        }

        for row in processed_data:
            time = row[1]
            if time:
                try:
                    time_obj = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                    time = time_obj.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass

            lat = row[3] if row[3] != "N / A" else None
            long = row[4] if row[4] != "N / A" else None
            speed = row[5] if row[5] != "N / A" else None
            pressure = row[6] if row[6] != "N / A" else None

            if speed:
                speed = int(speed)
                if speed < 34:
                    typhoon_class = "0"
                elif 34 <= speed <= 63:
                    typhoon_class = "1"
                elif 64 <= speed <= 82:
                    typhoon_class = "2"
                elif 83 <= speed <= 95:
                    typhoon_class = "3"
                elif 96 <= speed <= 112:
                    typhoon_class = "4"
                elif speed >= 113:
                    typhoon_class = "5"
            else:
                typhoon_class = "0"

            typhoon_data["path"].append({
                "time": time,
                "lat": float(lat) if lat else None,
                "long": float(long) if long else None,
                "speed": str(speed) if speed else "< 35",
                "pressure": str(pressure) if pressure else "> 1008",
                "class": int(typhoon_class)
            })

        if processed_data:
            try:
                start_time = datetime.strptime(processed_data[0][1], "%Y-%m-%d %H:%M:%S")
                start_time = start_time.replace(second=0)
                typhoon_data["start_time"] = int(start_time.timestamp())
            except ValueError:
                typhoon_data["start_time"] = None

        all_typhoon_data.append(typhoon_data)

    save_cache(all_typhoon_data, year, basin_name, folder_path)
    return all_typhoon_data

def scrape_typhoon_data(year, basin_name, folder_path="data"):
    """Main function to either return existing data or scrape and return new data."""
    data = load_cache(year, basin_name, folder_path)
    if data:
        return data
    else:
        print(f"Cache not found. Scraping data for {basin_name} in {year}.")
        return save_data_as_json(year, basin_name, folder_path)

# Example usage:
if __name__ == "__main__":
    year = 2015
    basin = "Western Pacific"
    data = scrape_typhoon_data(year, basin)
    if data:
        print(f"Fetched and cached {len(data)} typhoons.")
    else:
        print("No data available.")
