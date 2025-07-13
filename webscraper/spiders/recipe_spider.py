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

        # Recursively follow internal links, but be more flexible about what we follow
        all_links = response.css('a::attr(href)').getall()
        self.logger.info(f"Found {len(all_links)} links on {response.url}")
        
        for href in all_links:
            next_url = urljoin(response.url, href)
            
            if self.is_internal_link(next_url):
                # Follow recipe pages and recipe-related pages
                if self.is_valid_recipe_url(next_url) or self.is_recipe_related_url(next_url):
                    self.logger.info(f"Following recipe link: {next_url}")
                    yield scrapy.Request(next_url, callback=self.parse)

    def is_valid_recipe_url(self, url):
        """Return True if the URL is a valid recipe page (not a category, collection, etc.)"""
        from urllib.parse import urlparse
        import re
        parsed = urlparse(url)
        path = parsed.path

        # Explicitly exclude index/category pages like /recipes/ or /recipe/
        if path.rstrip('/') in ['/recipes', '/recipe']:
            return False
        
        # Skip obvious non-recipe pages
        skip_patterns = [
            '/recipes/category/', '/recipes/collection/', '/recipes/tag/',  # Category/collection pages
            '/recipe/category/', '/recipe/collection/', '/recipe/tag/',
            '/category/', '/categories/',
            '/collection/', '/collections/',
            '/tag/', '/tags/',
            '/author/', '/authors/',
            '/search', '/about', '/contact', '/privacy', '/terms',
            '/sitemap', '/rss', '/feed',
            '/wp-admin', '/wp-content', '/wp-includes',  # WordPress admin
            '/admin', '/login', '/register',
            '/cart', '/checkout', '/account',  # E-commerce
            '/blog/', '/news/', '/article/',
            '/video/', '/podcast/', '/webinar/',
            '/event/', '/competition/', '/contest/',
            '/gallery/', '/photo/', '/image/',
            '/quiz/', '/poll/', '/survey/',
            '/faq/', '/help/', '/support/',
            '/api/', '/json/', '/xml/',
            '/sitemap', '/robots.txt',
            '/favicon.ico', '/apple-touch-icon',
            '/manifest.json', '/service-worker.js'
        ]
        
        for pattern in skip_patterns:
            if pattern in path.lower():
                return False
        
        # Recipe URL patterns - more flexible to handle different sites
        recipe_patterns = [
            # RecipeTin Eats style: /recipe-name/
            r"^/[a-z0-9-]+/$",
            # Traditional: /recipes/recipe-name
            r"^/recipes/[a-z0-9-]+$",
            # Alternative: /recipe/recipe-name
            r"^/recipe/[a-z0-9-]+$",
            # With language prefix: /en/recipes/recipe-name
            r"^/[a-z]{2}/recipes/[a-z0-9-]+$",
            # With year/month: /2023/12/recipe-name
            r"^/\d{4}/\d{1,2}/[a-z0-9-]+$",
            # With category: /main-dishes/recipe-name
            r"^/[a-z-]+/[a-z0-9-]+$"
        ]
        
        for pattern in recipe_patterns:
            if re.match(pattern, path):
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
        # Handle www subdomain variations
        domain = parsed.netloc
        allowed_domain = self.allowed_domains[0]
        
        # Remove www. prefix for comparison
        if domain.startswith('www.'):
            domain = domain[4:]
        if allowed_domain.startswith('www.'):
            allowed_domain = allowed_domain[4:]
            
        return domain == allowed_domain

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
        
        # Check if this is RecipeTin Eats (has WPRM plugin)
        wprm_elements = soup.select('.wprm-recipe-ingredient, .wprm-recipe-instruction')
        if wprm_elements:
            # Use RecipeTin Eats specific parsing
            item = self.parse_recipetineats_html(soup, item)
        else:
            # Try to extract recipe data from embedded JSON first
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
                # Fallback to generic HTML parsing
                item = self.parse_generic_html(soup, item)
        
        return item
    
    def parse_generic_html(self, soup, item):
        """Parse generic HTML structure for recipe data"""
        
        # Extract ingredients
        ingredients = []
        ingredient_selectors = [
            '.ingredients li',
            '.recipe-ingredients li',
            '.ingredient-list li',
            '[class*="ingredient"] li',
            'ul li'  # Fallback to any list items
        ]
        
        for selector in ingredient_selectors:
            ingredient_elements = soup.select(selector)
            for elem in ingredient_elements:
                ingredient_text = elem.get_text(strip=True)
                if ingredient_text and len(ingredient_text) > 5:
                    ingredients.append(ingredient_text)
            if ingredients:
                break
        
        item['ingredients'] = ingredients
        
        # Extract instructions
        instructions = []
        instruction_selectors = [
            '.instructions li',
            '.recipe-instructions li',
            '.method li',
            '.steps li',
            '[class*="instruction"] li',
            'ol li'  # Fallback to ordered lists
        ]
        
        for selector in instruction_selectors:
            instruction_elements = soup.select(selector)
            for elem in instruction_elements:
                instruction_text = elem.get_text(strip=True)
                if instruction_text and len(instruction_text) > 10:
                    instructions.append(instruction_text)
            if instructions:
                break
        
        item['instructions'] = '\n'.join(instructions)
        
        # Extract cooking times
        time_data = {}
        time_selectors = [
            '.prep-time',
            '.cook-time',
            '.total-time',
            '.recipe-time',
            '[class*="time"]'
        ]
        
        for selector in time_selectors:
            time_elements = soup.select(selector)
            for elem in time_elements:
                text = elem.get_text(strip=True).lower()
                if 'prep' in text:
                    time_data['prep'] = self.extract_time_minutes(text)
                elif 'cook' in text:
                    time_data['cook'] = self.extract_time_minutes(text)
                elif 'total' in text:
                    time_data['total'] = self.extract_time_minutes(text)
        
        item['time'] = time_data
        
        # Extract dietary labels
        dietary_labels = []
        dietary_selectors = [
            '.dietary-labels',
            '.recipe-tags',
            '.tags',
            '[class*="diet"]',
            '[class*="tag"]'
        ]
        
        for selector in dietary_selectors:
            dietary_elements = soup.select(selector)
            for elem in dietary_elements:
                labels = elem.get_text(strip=True).split(',')
                for label in labels:
                    clean_label = label.strip()
                    if clean_label:
                        dietary_labels.append(clean_label)
        
        item['dietary_labels'] = dietary_labels
        
        # Extract difficulty level
        difficulty = ''
        difficulty_selectors = [
            '.difficulty',
            '.skill-level',
            '[class*="difficulty"]',
            '[class*="skill"]'
        ]
        
        for selector in difficulty_selectors:
            difficulty_elem = soup.select_one(selector)
            if difficulty_elem:
                difficulty = difficulty_elem.get_text(strip=True)
                break
        
        item['difficulty'] = difficulty
        
        # Extract ratings
        ratings = ''
        rating_selectors = [
            '.rating',
            '.stars',
            '[class*="rating"]'
        ]
        
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                ratings = rating_elem.get_text(strip=True)
                break
        
        item['ratings'] = ratings
        
        # Extract nutrition info
        nutrition_info = []
        nutrition_selectors = [
            '.nutrition',
            '.nutrition-info',
            '[class*="nutrition"]'
        ]
        
        for selector in nutrition_selectors:
            nutrition_elements = soup.select(selector)
            for elem in nutrition_elements:
                nutrition_text = elem.get_text(strip=True)
                if nutrition_text:
                    nutrition_info.append(nutrition_text)
        
        item['fitness_relevance'] = ', '.join(nutrition_info)
        
        return item
    
    def parse_recipetineats_html(self, soup, item):
        """Parse RecipeTin Eats HTML structure"""
        
        # Extract ingredients - RecipeTin Eats uses WPRM plugin
        ingredients = []
        ingredient_elements = soup.select('.wprm-recipe-ingredient')
        for elem in ingredient_elements:
            ingredient_text = elem.get_text(strip=True)
            if ingredient_text and len(ingredient_text) > 5:  # Filter out empty or very short text
                ingredients.append(ingredient_text)
        
        # Fallback to other selectors if WPRM not found
        if not ingredients:
            ingredient_selectors = [
                '[class*="ingredient"] li',
                '.ingredients li',
                '.recipe-ingredients li'
            ]
            for selector in ingredient_selectors:
                ingredient_elements = soup.select(selector)
                for elem in ingredient_elements:
                    ingredient_text = elem.get_text(strip=True)
                    if ingredient_text and len(ingredient_text) > 5:
                        ingredients.append(ingredient_text)
                if ingredients:
                    break
        
        item['ingredients'] = ingredients
        
        # Extract instructions - RecipeTin Eats uses WPRM plugin
        instructions = []
        instruction_elements = soup.select('.wprm-recipe-instruction')
        for elem in instruction_elements:
            instruction_text = elem.get_text(strip=True)
            if instruction_text and len(instruction_text) > 10:  # Filter out very short text
                instructions.append(instruction_text)
        
        # Fallback to other selectors if WPRM not found
        if not instructions:
            instruction_selectors = [
                '[class*="instruction"] li',
                '.instructions li',
                '.recipe-instructions li',
                'ol li'  # Ordered lists for steps
            ]
            for selector in instruction_selectors:
                instruction_elements = soup.select(selector)
                for elem in instruction_elements:
                    instruction_text = elem.get_text(strip=True)
                    if instruction_text and len(instruction_text) > 10:
                        instructions.append(instruction_text)
                if instructions:
                    break
        
        item['instructions'] = '\n'.join(instructions)
        
        # Extract cooking times - RecipeTin Eats format
        time_data = {}
        time_elements = soup.select('[class*="time"]')
        for elem in time_elements:
            text = elem.get_text(strip=True).lower()
            if 'prep' in text:
                time_data['prep'] = self.extract_time_minutes(text)
            elif 'cook' in text:
                time_data['cook'] = self.extract_time_minutes(text)
            elif 'total' in text:
                time_data['total'] = self.extract_time_minutes(text)
        
        item['time'] = time_data
        
        # Extract dietary labels and tags
        dietary_labels = []
        
        # Look for recipe tags/categories
        tag_selectors = [
            '.wprm-recipe-tag',
            '.recipe-tags',
            '.tags',
            '[class*="tag"]'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag_text = elem.get_text(strip=True)
                if tag_text and len(tag_text) > 2:
                    dietary_labels.append(tag_text)
        
        item['dietary_labels'] = dietary_labels
        
        # Extract difficulty level
        difficulty = ''
        difficulty_selectors = [
            '.wprm-recipe-difficulty',
            '.difficulty',
            '.skill-level'
        ]
        
        for selector in difficulty_selectors:
            difficulty_elem = soup.select_one(selector)
            if difficulty_elem:
                difficulty = difficulty_elem.get_text(strip=True)
                break
        
        item['difficulty'] = difficulty
        
        # Extract ratings
        ratings = ''
        rating_selectors = [
            '.wprm-recipe-rating',
            '.rating',
            '.stars'
        ]
        
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                ratings = rating_elem.get_text(strip=True)
                break
        
        item['ratings'] = ratings
        
        # Extract nutrition info
        nutrition_info = []
        nutrition_selectors = [
            '.wprm-recipe-nutrition',
            '.nutrition',
            '.nutrition-info'
        ]
        
        for selector in nutrition_selectors:
            nutrition_elements = soup.select(selector)
            for elem in nutrition_elements:
                nutrition_text = elem.get_text(strip=True)
                if nutrition_text:
                    nutrition_info.append(nutrition_text)
        
        item['fitness_relevance'] = ', '.join(nutrition_info)
        
        return item
    
    def extract_time_minutes(self, text):
        """Extract time in minutes from text"""
        import re
        # Look for patterns like "15 minutes", "1 hour", "1h 30m", etc.
        time_patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*hours?',
            r'(\d+)h\s*(\d+)m',
            r'(\d+)\s*hrs?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'h' in pattern and len(match.groups()) > 1:
                    # Handle "1h 30m" format
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    return hours * 60 + minutes
                else:
                    # Handle single time unit
                    value = int(match.group(1))
                    if 'hour' in pattern or 'hr' in pattern:
                        return value * 60
                    else:
                        return value
        
        return 0 