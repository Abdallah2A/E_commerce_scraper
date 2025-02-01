# E-Commerce Scraper

A Python-based web scraping tool that extracts product data from Amazon Egypt and Jumia, featuring a user-friendly GUI for searching, filtering, and analyzing e-commerce products.

## Features

- **Dual Platform Support**: Scrape product data from both Amazon.eg and Jumia.com.eg
- **Rich Product Data Extraction**:
  - Prices & Discounts
  - Customer Ratings & Reviews
  - Product Specifications
  - Color/Size Variations
  - Brand Information
- **Interactive GUI**:
  - Search by product name
  - Sort by price/rating
  - Detailed product views
  - Direct product URL access
- **Data Export**: JSON format output
- **Anti-Blocking Measures**: Randomized headers via ScrapeOps

## Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/e-commerce-scraper.git
   cd e-commerce-scraper
   ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key**
    Create e_commerce_scraper/config.json:
    ```bash
    {
    "SCRAPE_OPS_API_KEY": "your_api_key_here"
    }
    ```

    Get free API key from ScrapeOps


## Usage

1. Launch Application

```bash
python scrapper_app.py
```

2. Basic Workflow

- Enter product name (e.g., "wireless headphones")
- Click "Scrape" button
- Results appear in 2-3 minutes
- Filter results using dropdown
- Click products for detailed views

3. Output Data

JSON file: scraped_data.json
Persistent until next scrape


## Project Structure
```bash
├── e_commerce_scraper/
│   ├── spiders/
│   │   ├── amazon_spider.py
│   │   └── jumia_spider.py
│   ├── config.json
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   └── settings.py
├── scrapper_app.py
├── requirements.txt
└── scrapy.cfg
```

## Dependencies

- Python 3.7+

- Scrapy

- CustomTkinter

- Pillow

- Requests

- ScrapeOps SDK

## Configuration

Edit config.json to include:

- ScrapeOps API key

- (Optional) Adjust request headers count

## Contributing

Contributions welcome! Please:

1. Fork repository

2. Create feature branch

3. Submit PR with detailed description

## Notes

Website structure changes may break scraping
