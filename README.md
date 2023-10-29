# Sports Betting Data Scraper

# Overview
This Python script automates the process of scraping and processing sports betting data from a website. It utilizes Selenium and Chrome WebDriver for data extraction and provides options to handle "N/A" values and enable or disable headless mode for Chrome WebDriver.

# Prerequisites
Before using this script, ensure you have the following prerequisites installed:

- Python
- Selenium

1. Install requirements using pip:

```bash
pip install requirements.txt
```

2. Run the script as normal:
  - `python parse_veri_bet.py`



3. OPTIONAL: Run the script with optional arguments:
`-nna or --handle_na: Skip adding 'N/A' for missing values (optional).`
`--noheadless: Disable headless mode for Chrome WebDriver (optional).`
 - Example:

```bash
python parse_veri_bet.py -nna --noheadless
```

