import pytest
from webscraper.items import WebscraperItem


class TestWebscraperItem:
    """Test cases for WebscraperItem."""
    
    def test_webscraper_item_creation(self):
        """Test that WebscraperItem can be created with required fields."""
        item = WebscraperItem()
        assert item is not None
        
    def test_webscraper_item_fields(self):
        """Test that WebscraperItem has the expected fields."""
        item = WebscraperItem()
        # Check if item has the expected fields
        assert hasattr(item, 'fields')
        
    def test_webscraper_item_required_fields(self):
        """Test that WebscraperItem has all required fields for a recipe."""
        item = WebscraperItem()
        expected_fields = [
            'url', 'title', 'ingredients', 'time', 'dietary_labels',
            'fitness_relevance', 'difficulty', 'instructions', 'ratings'
        ]
        
        for field in expected_fields:
            assert field in item.fields


if __name__ == "__main__":
    pytest.main([__file__]) 