import pytest
from scrapy.http import Request, Response
from webscraper.spiders.recipe_spider import RecipeSpider


class TestRecipeSpider:
    """Test cases for RecipeSpider."""
    
    def test_spider_initialization(self):
        """Test that RecipeSpider can be initialized."""
        spider = RecipeSpider()
        assert spider.name == 'recipe_spider'
        assert hasattr(spider, 'allowed_domains')
        assert hasattr(spider, 'start_urls')
        
    def test_spider_with_domain(self):
        """Test that RecipeSpider can be initialized with a domain."""
        domain = 'example.com'
        spider = RecipeSpider(domain=domain)
        assert spider.allowed_domains == [domain]
        assert spider.start_urls == [f'https://{domain}/recipes']
        
    def test_is_valid_recipe_url(self):
        """Test URL validation for recipe pages."""
        spider = RecipeSpider()
        
        # Valid recipe URLs
        valid_urls = [
            'https://example.com/recipes/chicken-pasta',
            'https://example.com/recipes/beef-stew',
            'https://example.com/recipes/vegetarian-curry'
        ]
        
        for url in valid_urls:
            assert spider.is_valid_recipe_url(url), f"URL should be valid: {url}"
            
        # Invalid recipe URLs
        invalid_urls = [
            'https://example.com/recipes/',
            'https://example.com/recipes/category/main-dishes',
            'https://example.com/recipes/collection/quick-meals',
            'https://example.com/recipes/beef-stew/ingredients'
        ]
        
        for url in invalid_urls:
            assert not spider.is_valid_recipe_url(url), f"URL should be invalid: {url}"
            
    def test_is_recipe_related_url(self):
        """Test URL filtering for recipe-related pages."""
        spider = RecipeSpider()
        
        # Recipe-related URLs
        recipe_urls = [
            'https://example.com/recipes/',
            'https://example.com/recipe/chicken-pasta',
            'https://example.com/healthy-recipes/',
            'https://example.com/vegetarian-recipes/'
        ]
        
        for url in recipe_urls:
            assert spider.is_recipe_related_url(url), f"URL should be recipe-related: {url}"
            
        # Non-recipe URLs
        non_recipe_urls = [
            'https://example.com/about',
            'https://example.com/contact',
            'https://example.com/news/article'
        ]
        
        for url in non_recipe_urls:
            assert not spider.is_recipe_related_url(url), f"URL should not be recipe-related: {url}"
            
    def test_is_internal_link(self):
        """Test internal link detection."""
        domain = 'example.com'
        spider = RecipeSpider(domain=domain)
        
        # Internal links
        internal_urls = [
            'https://example.com/recipes/chicken-pasta',
            'https://example.com/about',
            'https://example.com/contact'
        ]
        
        for url in internal_urls:
            assert spider.is_internal_link(url), f"URL should be internal: {url}"
            
        # External links
        external_urls = [
            'https://othersite.com/recipes/chicken-pasta',
            'https://google.com',
            'https://facebook.com'
        ]
        
        for url in external_urls:
            assert not spider.is_internal_link(url), f"URL should be external: {url}"


if __name__ == "__main__":
    pytest.main([__file__]) 