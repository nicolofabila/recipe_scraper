import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from webscraper.items import WebscraperItem

class RecipeSpider(scrapy.Spider):
    name = 'recipe_spider'
    allowed_domains = []  # Set dynamically from start_urls
    start_urls = []

    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Bypass robots.txt for academic/personal use
        'DOWNLOAD_DELAY': 0.5,    # Faster crawling
        'USER_AGENT': 'Mozilla/5.0 (compatible; RecipeScraper/1.0)',
        'CONCURRENT_REQUESTS': 8,  # More concurrent requests
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    }

    def __init__(self, domain=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if domain:
            self.allowed_domains = [domain]
            # Start from recipes page for better recipe discovery
            self.start_urls = [f'https://{domain}/recipes']
        self.visited_urls = set()

    def parse(self, response):
        url = response.url
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        # Only parse valid recipe pages
        if self.is_valid_recipe_url(url):
            yield self.parse_recipe(response)

        # Recursively follow internal links, but only valid recipe URLs
        for href in response.css('a::attr(href)').getall():
            next_url = urljoin(response.url, href)
            if self.is_internal_link(next_url) and self.is_valid_recipe_url(next_url):
                yield scrapy.Request(next_url, callback=self.parse)

    def is_valid_recipe_url(self, url):
        """Return True if the URL is a valid recipe page (not a category, collection, etc.)"""
        from urllib.parse import urlparse
        import re
        parsed = urlparse(url)
        path = parsed.path
        # Match /recipes/<slug> only (no further slashes after the slug)
        # e.g. /recipes/crispy-red-mullet-rice-with-saffron-aioli-lemon-olive-salsa
        if re.fullmatch(r"/recipes/[^/]+", path):
            return True
        return False

    def is_recipe_related_url(self, url):
        """Only follow links that are likely to lead to recipe pages"""
        url_lower = url.lower()
        
        # Only follow URLs that contain /recipes/ or are recipe-related
        recipe_patterns = [
            '/recipes/',
            '/recipe/',
            '/healthy-recipes/',
            '/quick-recipes/',
            '/easy-recipes/',
            '/vegetarian-recipes/',
            '/vegan-recipes/',
            '/gluten-free-recipes/'
        ]
        
        for pattern in recipe_patterns:
            if pattern in url_lower:
                return True
                
        return False

    def is_internal_link(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.allowed_domains[0]

    def is_recipe_page(self, response):
        # Generic recipe page detection
        url = response.url.lower()
        
        # Skip non-recipe content
        skip_patterns = [
            '/article/', '/news/', '/feature/', '/blog/', '/magazine/',
            '/competition/', '/event/', '/video/', '/podcast/',
            '/collection/', '/gallery/', '/quiz/', '/poll/'
        ]
        
        for pattern in skip_patterns:
            if pattern in url:
                return False
        
        # Recipe-specific patterns
        recipe_patterns = [
            '/recipe/', '/recipes/', '/recipe-collection/',
            '/healthy-recipes/', '/quick-recipes/', '/easy-recipes/'
        ]
        
        for pattern in recipe_patterns:
            if pattern in url:
                return True
        
        # Check for recipe schema.org markup
        content_type = response.headers.get('content-type', b'').decode('utf-8', errors='ignore')
        if 'application/ld+json' in content_type:
            return True
            
        # Check for recipe-specific CSS classes or IDs
        recipe_indicators = response.css('[class*="recipe"], [id*="recipe"]')
        if recipe_indicators:
            return True
            
        return False

    def parse_recipe(self, response):
        # Generic recipe parsing
        soup = BeautifulSoup(response.text, 'lxml')
        item = WebscraperItem()
        item['url'] = response.url
        item['title'] = soup.title.string if soup.title else ''
        
        # Extract recipe data from embedded JSON
        try:
            # Find the JSON data in the page
            script_tag = soup.find('script', {'id': '__POST_CONTENT__'})
            if script_tag and hasattr(script_tag, 'string') and script_tag.string:
                import json
                recipe_data = json.loads(str(script_tag.string))
                
                # Extract ingredients
                ingredients = []
                if 'ingredients' in recipe_data and recipe_data['ingredients']:
                    for ingredient_group in recipe_data['ingredients']:
                        for ingredient in ingredient_group.get('ingredients', []):
                            quantity = ingredient.get('quantityText', '')
                            ingredient_text = ingredient.get('ingredientText', '')
                            note = ingredient.get('note', '')
                            full_ingredient = f"{quantity} {ingredient_text}".strip()
                            if note:
                                full_ingredient += f" ({note})"
                            ingredients.append(full_ingredient)
                item['ingredients'] = ingredients
                
                # Extract cooking times
                time_data = {}
                if 'cookAndPrepTime' in recipe_data:
                    time_info = recipe_data['cookAndPrepTime']
                    time_data['prep'] = time_info.get('preparationMax', 0) // 60  # Convert seconds to minutes
                    time_data['cook'] = time_info.get('cookingMax', 0) // 60
                    time_data['total'] = time_info.get('total', 0) // 60
                item['time'] = time_data
                
                # Extract dietary labels
                dietary_labels = []
                if 'diet' in recipe_data:
                    for diet in recipe_data['diet']:
                        dietary_labels.append(diet.get('display', ''))
                item['dietary_labels'] = dietary_labels
                
                # Extract difficulty level
                if 'skillLevel' in recipe_data:
                    item['difficulty'] = recipe_data['skillLevel']
                
                # Extract instructions
                instructions = []
                if 'methodSteps' in recipe_data:
                    for step in recipe_data['methodSteps']:
                        if step.get('content'):
                            for content in step['content']:
                                if content.get('type') == 'html' and content.get('data', {}).get('value'):
                                    # Clean HTML tags from instructions
                                    import re
                                    clean_text = re.sub(r'<[^>]+>', '', content['data']['value'])
                                    instructions.append(clean_text.strip())
                item['instructions'] = '\n'.join(instructions)
                
                # Extract ratings
                if 'userRatings' in recipe_data:
                    ratings = recipe_data['userRatings']
                    item['ratings'] = f"{ratings.get('avg', 0)}/5 ({ratings.get('total', 0)} ratings)"
                
                # Extract fitness relevance (from nutrition info)
                fitness_info = []
                if 'nutritions' in recipe_data:
                    for nutrition in recipe_data['nutritions']:
                        label = nutrition.get('label', '')
                        value = nutrition.get('value', '')
                        unit = nutrition.get('unit', '')
                        if label and value:
                            fitness_info.append(f"{label}: {value}{unit}")
                item['fitness_relevance'] = ', '.join(fitness_info)
                
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # Fallback to basic extraction if JSON parsing fails
            item['ingredients'] = []
            item['time'] = {}
            item['dietary_labels'] = []
            item['fitness_relevance'] = ''
            item['difficulty'] = ''
            item['instructions'] = ''
            item['ratings'] = ''
        
        return item 