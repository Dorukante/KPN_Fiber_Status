# KPN Fiber Status — Netherlands Address Visualization

A Python and Flask application that retrieves real Dutch addresses from the **PDOK Locatieserver**, checks fiber availability through the **KPN Glasvezelnetwerk** website using Playwright, and visualizes the results on an interactive map.

## Features

- Retrieve 90 addresses from nine Dutch cities using the PDOK API.
- Validate postcodes, remove duplicates, and extract geographic coordinates.
- Check fiber availability using Playwright browser automation.
- Save results to CSV files.
- Visualize addresses on an interactive map of the Netherlands.
- Filter addresses by city and fiber status.

## Technologies

- **Python, Pandas, Requests** — Data collection and processing
- **Playwright, Chromium** — KPN fiber availability lookup
- **Flask** — Backend and JSON API
- **HTML, Bootstrap, JavaScript** — Dashboard
- **Leaflet, OpenStreetMap** — Geographic visualization

## Installation

Install the required Python libraries from the command line:

```powershell
python -m pip install flask pandas requests playwright
python -m playwright install chromium
```

## Project Structure

```text
project/
├── main.py
├── generate_adresses.py
├── fetch_fiber_status.py
├── Template/
│   ├── Main.html
│   └── Geovis.js
└── Data/
    ├── addresses.csv
    └── fiber_status.csv
```

## How It Works

**1. Address Generation**

The application retrieves up to 100 address records per city from the PDOK Locatieserver API, validates them, removes duplicates, and randomly selects 10 addresses per city.

**2. Fiber Availability Lookup**

Playwright opens the KPN website, enters the postcode, house number, and optional addition, and retrieves the displayed fiber availability message. The returned address is verified before the status is assigned.

**3. Geographic Visualization**

Flask serves the CSV data as JSON through `/api/fiber-status`. Leaflet displays the addresses on an interactive map with city and status filters.

## How to Run

**1. Generate addresses**

```powershell
python generate_adresses.py
```

**2. Retrieve fiber statuses**

```powershell
python fetch_fiber_status.py
```

**3. Start the Flask application**

```powershell
python main.py
```

Open the dashboard at **http://127.0.0.1:8000/**.

## Fiber Status Classification

**Design Choice:** I chose to classify KPN fiber availability into five categories based on predefined phrases displayed on the KPN website:

- **Active:** Fiber is available at the address.
- **Planned:** Fiber installation is planned or expected.
- **Currently Installing:** KPN indicates that fiber installation is underway in the neighborhood, but not necessarily completed at the address.
- **Not Available:** Fiber is currently unavailable or a connection cannot be established.
- **Unknown:** The response cannot be reliably classified, including unsuccessful lookups or address mismatches.

This simplifies the interpretation, comparison, and geographic visualization of KPN's responses. These categories are application-defined rather than official KPN API statuses, and some phrases may be ambiguous. Additionally, the addresses were sampled from nine geographically distributed Dutch cities to provide geographic variety, rather than to estimate nationwide fiber coverage.
## Sources

- [PDOK Locatieserver](https://www.pdok.nl/pdok-locatieserver)
- [KPN Glasvezelnetwerk](https://www.kpn.com/glasvezelnetwerk)
- [Playwright](https://playwright.dev/python/docs/library)
- [Leaflet](https://leafletjs.com/)