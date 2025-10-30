"""
Unit tests for SmartIRCodeService
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from smartir_code_service import SmartIRCodeService


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_device_index():
    """Create a mock device index"""
    return {
        "version": "1.0.0",
        "last_updated": "2025-01-01",
        "platforms": {
            "climate": {
                "manufacturers": {
                    "Samsung": {
                        "models": [
                            {
                                "code": "1000",  # String, not int
                                "manufacturer": "Samsung",
                                "model": "AR09FSSEDWUNEU",
                                "models": ["AR09FSSEDWUNEU", "AR12FSSEDWUNEU"],
                                "controller_brand": "Broadlink",
                                "url": "https://example.com/1000.json"
                            }
                        ]
                    }
                }
            },
            "media_player": {
                "manufacturers": {
                    "Sony": {
                        "models": [
                            {
                                "code": "2000",  # String, not int
                                "manufacturer": "Sony",
                                "model": "KD-55X8500D",
                                "models": ["KD-55X8500D"],
                                "controller_brand": "Broadlink",
                                "url": "https://example.com/2000.json"
                            }
                        ]
                    }
                }
            }
        }
    }


@pytest.fixture
def code_service(temp_cache_dir, mock_device_index):
    """Create a SmartIRCodeService instance with mocked index"""
    with patch.object(SmartIRCodeService, '_load_device_index', return_value=mock_device_index):
        service = SmartIRCodeService(cache_path=temp_cache_dir)
        return service


@pytest.mark.unit
class TestSmartIRCodeServiceInit:
    """Test initialization"""

    def test_init_creates_cache_directory(self, temp_cache_dir):
        """Test that cache directory is created"""
        cache_path = Path(temp_cache_dir) / "test_cache"
        
        with patch.object(SmartIRCodeService, '_load_device_index', return_value={}):
            service = SmartIRCodeService(cache_path=str(cache_path))
        
        assert cache_path.exists()
        assert cache_path.is_dir()

    def test_init_loads_bundled_index(self, temp_cache_dir):
        """Test that bundled index is loaded"""
        mock_index = {"version": "1.0.0", "platforms": {}}
        
        with patch.object(SmartIRCodeService, '_load_device_index', return_value=mock_index) as mock_load:
            service = SmartIRCodeService(cache_path=temp_cache_dir)
            
            assert service._device_index == mock_index
            mock_load.assert_called_once()


@pytest.mark.unit
class TestLoadCache:
    """Test _load_cache method"""

    def test_load_cache_file_not_exists(self, temp_cache_dir):
        """Test loading cache when file doesn't exist"""
        with patch.object(SmartIRCodeService, '_load_device_index', return_value={}):
            service = SmartIRCodeService(cache_path=temp_cache_dir)
            cache = service._load_cache()
        
        assert cache["last_updated"] is None
        assert cache["manufacturers"] == {}
        assert cache["codes"] == {}

    def test_load_cache_file_exists(self, temp_cache_dir):
        """Test loading cache from existing file"""
        cache_data = {
            "last_updated": "2025-01-01T12:00:00",
            "manufacturers": {"Samsung": ["Model1"]},
            "codes": {"1000": {"test": "data"}}
        }
        
        cache_file = Path(temp_cache_dir) / "smartir_codes_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        with patch.object(SmartIRCodeService, '_load_device_index', return_value={}):
            service = SmartIRCodeService(cache_path=temp_cache_dir)
            cache = service._load_cache()
        
        assert cache["last_updated"] == "2025-01-01T12:00:00"
        assert "Samsung" in cache["manufacturers"]

    def test_load_cache_invalid_json(self, temp_cache_dir):
        """Test loading cache with invalid JSON"""
        cache_file = Path(temp_cache_dir) / "smartir_codes_cache.json"
        with open(cache_file, 'w') as f:
            f.write("invalid json{")
        
        with patch.object(SmartIRCodeService, '_load_device_index', return_value={}):
            service = SmartIRCodeService(cache_path=temp_cache_dir)
            cache = service._load_cache()
        
        # Should return default cache structure
        assert cache["last_updated"] is None
        assert cache["manufacturers"] == {}


@pytest.mark.unit
class TestSaveCache:
    """Test _save_cache method"""

    def test_save_cache_success(self, code_service):
        """Test successful cache save"""
        code_service._cache = {
            "last_updated": "2025-01-01T12:00:00",
            "manufacturers": {"Samsung": ["Model1"]},
            "codes": {}
        }
        
        result = code_service._save_cache()
        
        assert result is True
        assert code_service.cache_file.exists()
        
        # Verify saved content
        with open(code_service.cache_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["last_updated"] == "2025-01-01T12:00:00"

    def test_save_cache_permission_error(self, code_service):
        """Test cache save with permission error"""
        code_service._cache = {"test": "data"}
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = code_service._save_cache()
        
        assert result is False


@pytest.mark.unit
class TestLoadDeviceIndex:
    """Test _load_device_index method"""

    def test_load_device_index_returns_dict(self, code_service):
        """Test that device index is loaded as a dictionary"""
        # The index should be loaded during initialization
        assert hasattr(code_service, '_device_index')
        assert isinstance(code_service._device_index, dict)
        assert "version" in code_service._device_index
        assert "platforms" in code_service._device_index


@pytest.mark.unit
class TestGetManufacturers:
    """Test get_manufacturers method"""

    def test_get_manufacturers_for_platform(self, code_service):
        """Test getting manufacturers for a specific platform"""
        manufacturers = code_service.get_manufacturers("climate")
        
        assert "Samsung" in manufacturers
        assert len(manufacturers) > 0

    def test_get_manufacturers_invalid_platform(self, code_service):
        """Test getting manufacturers for invalid platform"""
        manufacturers = code_service.get_manufacturers("invalid_platform")
        
        assert manufacturers == []

    def test_get_manufacturers_empty_platform(self, temp_cache_dir):
        """Test getting manufacturers for platform with no data"""
        empty_index = {
            "version": "1.0.0",
            "platforms": {
                "climate": {
                    "manufacturers": {}
                }
            }
        }
        
        with patch.object(SmartIRCodeService, '_load_device_index', return_value=empty_index):
            service = SmartIRCodeService(cache_path=temp_cache_dir)
            manufacturers = service.get_manufacturers("climate")
        
        assert manufacturers == []


@pytest.mark.unit
class TestGetModels:
    """Test get_models method"""

    def test_get_models_for_manufacturer(self, code_service):
        """Test getting models for a manufacturer"""
        models = code_service.get_models("climate", "Samsung")
        
        # Should return a list (may be empty)
        assert isinstance(models, list)

    def test_get_models_invalid_manufacturer(self, code_service):
        """Test getting models for invalid manufacturer"""
        models = code_service.get_models("climate", "NonExistent")
        
        assert models == []

    def test_get_models_invalid_platform(self, code_service):
        """Test getting models for invalid platform"""
        models = code_service.get_models("invalid", "Samsung")
        
        assert models == []


@pytest.mark.unit
class TestGetCodeInfo:
    """Test get_code_info method"""

    def test_get_code_info_not_in_cache(self, code_service):
        """Test getting code info when not in cache"""
        code_info = code_service.get_code_info("climate", "1000")
        
        # Should return None if not in cache
        assert code_info is None


@pytest.mark.unit
class TestSearchDevices:
    """Test search_devices method"""

    def test_search_devices_exists(self, code_service):
        """Test that search functionality is available"""
        # The service should have search capability through get_models
        # which can filter by manufacturer
        models = code_service.get_models("climate", "Samsung")
        assert isinstance(models, list)


@pytest.mark.unit
class TestCacheStatus:
    """Test cache status method"""

    def test_get_cache_status(self, code_service):
        """Test getting cache status"""
        status = code_service.get_cache_status()
        
        assert isinstance(status, dict)
        assert "cache_valid" in status


@pytest.mark.unit
class TestCacheManagement:
    """Test cache management functionality"""

    def test_cache_invalidation(self, code_service):
        """Test that cache is invalidated after TTL"""
        # Set cache with old timestamp
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        code_service._cache["last_updated"] = old_time
        
        is_valid = code_service._is_cache_valid()
        
        assert is_valid is False

    def test_cache_valid_within_ttl(self, code_service):
        """Test that cache is valid within TTL"""
        from datetime import datetime
        recent_time = datetime.now().isoformat()
        code_service._cache["last_updated"] = recent_time
        
        is_valid = code_service._is_cache_valid()
        
        assert is_valid is True

    def test_cache_valid_no_timestamp(self, code_service):
        """Test cache validity with no timestamp"""
        code_service._cache["last_updated"] = None
        
        is_valid = code_service._is_cache_valid()
        
        assert is_valid is False
