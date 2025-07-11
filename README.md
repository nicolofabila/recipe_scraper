# Recipe Scraper

A Python web scraper built with Scrapy that crawls recipe websites and extracts structured recipe data. Can be adapted for various recipe sites by modifying the parsing logic.

## Features

- **Full-site crawling** - Recursively follows internal links to discover recipe pages
- **Smart filtering** - Only scrapes actual recipe pages, skips categories and collections
- **Structured data extraction** - Captures ingredients, instructions, cooking times, dietary info, and ratings
- **Efficient crawling** - Uses concurrent requests and auto-throttling for optimal performance

## What it extracts

- Recipe title and URL
- Complete ingredient lists with quantities
- Step-by-step cooking instructions
- Prep, cook, and total times
- Dietary labels (vegan, gluten-free, etc.)
- Difficulty level
- User ratings and reviews
- Nutrition information

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper:
   ```bash
   scrapy crawl recipe_spider -a domain=example.com -o output/recipes.json
   ```

## Output

Results are saved as JSON files with one recipe per line. Each recipe includes all extracted fields in a structured format ready for database import or further processing.

## Configuration

The scraper can be customized by modifying:
- `DOWNLOAD_DELAY` - Time between requests
- `CONCURRENT_REQUESTS` - Number of simultaneous requests
- URL filtering patterns in `is_valid_recipe_url()`
- Recipe parsing logic in `parse_recipe()`

## License

MIT License
