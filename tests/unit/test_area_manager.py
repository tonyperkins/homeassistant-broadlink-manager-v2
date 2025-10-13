"""
Unit tests for AreaManager
"""

import pytest


@pytest.mark.unit
class TestAreaManager:
    """Test AreaManager functionality"""
    
    def test_initialization(self, area_manager):
        """Test AreaManager initializes correctly"""
        assert area_manager.storage_path.exists()
        assert area_manager.areas_file.exists()
    
    def test_create_area(self, area_manager, sample_area_data):
        """Test creating a new area"""
        result = area_manager.create_area('master_bedroom', sample_area_data)
        
        assert result is True
        area = area_manager.get_area('master_bedroom')
        assert area is not None
        assert area['name'] == sample_area_data['name']
        assert area['area_id'] == 'master_bedroom'
    
    def test_create_duplicate_area(self, area_manager, sample_area_data):
        """Test that creating a duplicate area fails"""
        area_manager.create_area('master_bedroom', sample_area_data)
        result = area_manager.create_area('master_bedroom', sample_area_data)
        
        assert result is False
    
    def test_get_area(self, area_manager, sample_area_data):
        """Test retrieving an area"""
        area_manager.create_area('master_bedroom', sample_area_data)
        area = area_manager.get_area('master_bedroom')
        
        assert area is not None
        assert area['area_id'] == 'master_bedroom'
    
    def test_get_all_areas(self, area_manager, sample_area_data):
        """Test retrieving all areas"""
        area_manager.create_area('master_bedroom', sample_area_data)
        area_manager.create_area('living_room', sample_area_data)
        
        areas = area_manager.get_all_areas()
        assert len(areas) == 2
        assert 'master_bedroom' in areas
        assert 'living_room' in areas
    
    def test_update_area(self, area_manager, sample_area_data):
        """Test updating area metadata"""
        area_manager.create_area('master_bedroom', sample_area_data)
        
        updates = {'name': 'Primary Bedroom', 'floor': 'second'}
        result = area_manager.update_area('master_bedroom', updates)
        
        assert result is True
        area = area_manager.get_area('master_bedroom')
        assert area['name'] == 'Primary Bedroom'
        assert area['floor'] == 'second'
    
    def test_delete_area(self, area_manager, sample_area_data):
        """Test deleting an area"""
        area_manager.create_area('master_bedroom', sample_area_data)
        result = area_manager.delete_area('master_bedroom')
        
        assert result is True
        area = area_manager.get_area('master_bedroom')
        assert area is None
    
    def test_generate_area_id(self, area_manager):
        """Test area ID generation"""
        area_id = area_manager.generate_area_id('Master Bedroom')
        assert area_id == 'master_bedroom'
        
        # Test with special characters
        area_id = area_manager.generate_area_id('Living/Dining Room')
        assert area_id == 'living_dining_room'
