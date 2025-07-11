"""
Shared test fixtures for recipe scraper tests.
"""
import pytest
from scrapy.http import Request, Response
from webscraper.spiders.recipe_spider import RecipeSpider
from webscraper.items import WebscraperItem


@pytest.fixture
def spider():
    """Create a basic RecipeSpider instance for testing."""
    return RecipeSpider()


@pytest.fixture
def spider_with_domain():
    """Create a RecipeSpider instance with a domain for testing."""
    return RecipeSpider(domain='example.com')


@pytest.fixture
def sample_recipe_item():
    """Create a sample WebscraperItem with test data."""
    item = WebscraperItem()
    item['url'] = 'https://example.com/recipes/test-recipe'
    item['title'] = 'Test Recipe'
    item['ingredients'] = ['2 cups flour', '1 cup water', '1 tsp salt']
    item['time'] = {'prep': 15, 'cook': 30, 'total': 45}
    item['dietary_labels'] = ['vegetarian', 'gluten-free']
    item['fitness_relevance'] = 'Calories: 250, Protein: 8g'
    item['difficulty'] = 'Easy'
    item['instructions'] = 'Mix ingredients. Bake at 350F for 30 minutes.'
    item['ratings'] = '4.5/5 (10 ratings)'
    return item


@pytest.fixture
def mock_response():
    """Create a mock Scrapy response for testing."""
    url = 'https://example.com/recipes/test-recipe'
    body = '''
    <html>
        <head><title>Test Recipe</title></head>
        <body>
            <h1>Test Recipe</h1>
            <div class="ingredients">
                <ul>
                    <li>2 cups flour</li>
                    <li>1 cup water</li>
                </ul>
            </div>
        </body>
    </html>
    '''
    return Response(url=url, body=body.encode('utf-8')) 