# Recipe Scraper Tests

This directory contains tests for the recipe scraper project.

## Running Tests

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=webscraper --cov-report=html
```

### Run Specific Test Files
```bash
pytest tests/test_items.py
pytest tests/test_spider.py
```

### Run Tests with Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

- `conftest.py` - Shared test fixtures
- `test_items.py` - Tests for the WebscraperItem class
- `test_spider.py` - Tests for the RecipeSpider class

## Adding New Tests

1. Create test files with the prefix `test_`
2. Use descriptive test function names starting with `test_`
3. Add appropriate markers for test categorization
4. Use fixtures from `conftest.py` for common test data

## Coverage

The tests are configured to generate coverage reports for the `webscraper` module. Coverage reports are generated in HTML format and can be viewed in a web browser. 