"""
Unit tests for smartir_detector module
Tests SmartIR installation detection and code file management
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.smartir_detector import SmartIRDetector


class TestSmartIRDetectorInitialization:
    """Test SmartIRDetector initialization"""

    def test_init_default_path(self):
        """Test initialization with default config path"""
        detector = SmartIRDetector()
        assert detector.config_path == Path("/config")
        assert detector.smartir_path == Path("/config/custom_components/smartir")
        assert detector.codes_path == Path("/config/custom_components/smartir/codes")

    def test_init_custom_path(self):
        """Test initialization with custom config path"""
        detector = SmartIRDetector("/custom/config")
        assert detector.config_path == Path("/custom/config")
        assert detector.smartir_path == Path("/custom/config/custom_components/smartir")
        assert detector.codes_path == Path("/custom/config/custom_components/smartir/codes")


class TestSmartIRInstallationDetection:
    """Test SmartIR installation detection"""

    def test_is_installed_true(self):
        """Test detection when SmartIR is installed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            (smartir_path / "manifest.json").write_text('{"version": "1.0.0"}')
            
            detector = SmartIRDetector(str(config_path))
            assert detector.is_installed() is True

    def test_is_installed_false_no_directory(self):
        """Test detection when SmartIR directory doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            assert detector.is_installed() is False

    def test_is_installed_false_no_manifest(self):
        """Test detection when manifest.json is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            
            detector = SmartIRDetector(str(config_path))
            assert detector.is_installed() is False


class TestSmartIRVersion:
    """Test SmartIR version detection"""

    def test_get_version_success(self):
        """Test getting version when manifest exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            
            manifest = {"version": "1.17.9", "name": "SmartIR"}
            (smartir_path / "manifest.json").write_text(json.dumps(manifest))
            
            detector = SmartIRDetector(str(config_path))
            version = detector.get_version()
            assert version == "1.17.9"

    def test_get_version_no_manifest(self):
        """Test getting version when manifest doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            version = detector.get_version()
            assert version is None

    def test_get_version_invalid_json(self):
        """Test getting version with invalid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            (smartir_path / "manifest.json").write_text("invalid json")
            
            detector = SmartIRDetector(str(config_path))
            version = detector.get_version()
            assert version is None

    def test_get_version_no_version_field(self):
        """Test getting version when version field is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            
            manifest = {"name": "SmartIR"}
            (smartir_path / "manifest.json").write_text(json.dumps(manifest))
            
            detector = SmartIRDetector(str(config_path))
            version = detector.get_version()
            assert version is None


class TestSupportedPlatforms:
    """Test supported platforms detection"""

    def test_get_supported_platforms_multiple(self):
        """Test getting multiple supported platforms"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            codes_path = config_path / "custom_components" / "smartir" / "codes"
            
            # Create platform directories
            (codes_path / "climate").mkdir(parents=True)
            (codes_path / "media_player").mkdir(parents=True)
            (codes_path / "fan").mkdir(parents=True)
            
            detector = SmartIRDetector(str(config_path))
            platforms = detector.get_supported_platforms()
            
            assert sorted(platforms) == ["climate", "fan", "media_player"]

    def test_get_supported_platforms_empty(self):
        """Test getting platforms when codes directory doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            platforms = detector.get_supported_platforms()
            assert platforms == []

    def test_get_supported_platforms_ignores_files(self):
        """Test that files in codes directory are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            codes_path = config_path / "custom_components" / "smartir" / "codes"
            codes_path.mkdir(parents=True)
            
            # Create directories and files
            (codes_path / "climate").mkdir()
            (codes_path / "readme.txt").write_text("test")
            
            detector = SmartIRDetector(str(config_path))
            platforms = detector.get_supported_platforms()
            
            assert platforms == ["climate"]


class TestDeviceCodes:
    """Test device code retrieval"""

    def test_get_device_codes_success(self):
        """Test getting device codes for a platform"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create code files
            code1 = {
                "manufacturer": "Daikin",
                "supportedModels": ["FTXS25CVMA"],
                "supportedController": "Broadlink"
            }
            (climate_path / "1000.json").write_text(json.dumps(code1))
            
            code2 = {
                "manufacturer": "Samsung",
                "supportedModels": ["AR12FSSSBWKNEU"],
                "supportedController": "Broadlink"
            }
            (climate_path / "1001.json").write_text(json.dumps(code2))
            
            detector = SmartIRDetector(str(config_path))
            codes = detector.get_device_codes("climate")
            
            assert len(codes) == 2
            assert codes[0]["code"] == 1000
            assert codes[0]["manufacturer"] == "Daikin"
            assert codes[1]["code"] == 1001
            assert codes[1]["manufacturer"] == "Samsung"

    def test_get_device_codes_no_platform(self):
        """Test getting codes for non-existent platform"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            codes = detector.get_device_codes("climate")
            assert codes == []

    def test_get_device_codes_invalid_json(self):
        """Test getting codes with invalid JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create valid and invalid files
            (climate_path / "1000.json").write_text('{"manufacturer": "Daikin"}')
            (climate_path / "1001.json").write_text("invalid json")
            
            detector = SmartIRDetector(str(config_path))
            codes = detector.get_device_codes("climate")
            
            # Should only return valid code
            assert len(codes) == 1
            assert codes[0]["code"] == 1000

    def test_get_device_codes_invalid_filename(self):
        """Test getting codes with non-numeric filename"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create files with invalid names
            (climate_path / "invalid.json").write_text('{"manufacturer": "Test"}')
            (climate_path / "1000.json").write_text('{"manufacturer": "Daikin"}')
            
            detector = SmartIRDetector(str(config_path))
            codes = detector.get_device_codes("climate")
            
            # Should only return valid code
            assert len(codes) == 1
            assert codes[0]["code"] == 1000

    def test_get_device_codes_sorted(self):
        """Test that device codes are sorted by code number"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create codes in random order
            for code in [1050, 1000, 1025]:
                data = {"manufacturer": f"Manufacturer{code}"}
                (climate_path / f"{code}.json").write_text(json.dumps(data))
            
            detector = SmartIRDetector(str(config_path))
            codes = detector.get_device_codes("climate")
            
            assert [c["code"] for c in codes] == [1000, 1025, 1050]


class TestCustomCodeGeneration:
    """Test custom code number generation"""

    def test_find_next_custom_code_no_existing(self):
        """Test finding next custom code with no existing codes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            next_code = detector.find_next_custom_code("climate")
            assert next_code == 10000

    def test_find_next_custom_code_with_existing(self):
        """Test finding next custom code with existing codes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create custom codes
            (climate_path / "10000.json").write_text('{}')
            (climate_path / "10001.json").write_text('{}')
            (climate_path / "10005.json").write_text('{}')
            
            detector = SmartIRDetector(str(config_path))
            next_code = detector.find_next_custom_code("climate")
            assert next_code == 10006

    def test_find_next_custom_code_ignores_standard_codes(self):
        """Test that standard codes (<10000) are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create standard and custom codes
            (climate_path / "1000.json").write_text('{}')
            (climate_path / "1001.json").write_text('{}')
            (climate_path / "10000.json").write_text('{}')
            
            detector = SmartIRDetector(str(config_path))
            next_code = detector.find_next_custom_code("climate")
            assert next_code == 10001

    def test_find_next_custom_code_invalid_filenames(self):
        """Test finding next code with invalid filenames"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Create files with invalid names
            (climate_path / "invalid.json").write_text('{}')
            (climate_path / "test.json").write_text('{}')
            
            detector = SmartIRDetector(str(config_path))
            next_code = detector.find_next_custom_code("climate")
            assert next_code == 10000


class TestSmartIRStatus:
    """Test SmartIR status retrieval"""

    def test_get_status_not_installed(self):
        """Test status when SmartIR is not installed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            status = detector.get_status()
            
            assert status["installed"] is False
            assert status["version"] is None
            assert status["platforms"] == []
            assert status["device_counts"] == {}
            assert "recommendation" in status
            assert "Install" in status["recommendation"]["message"]

    def test_get_status_installed(self):
        """Test status when SmartIR is installed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            smartir_path = config_path / "custom_components" / "smartir"
            smartir_path.mkdir(parents=True)
            
            # Create manifest
            manifest = {"version": "1.17.9"}
            (smartir_path / "manifest.json").write_text(json.dumps(manifest))
            
            # Create platforms with codes
            codes_path = smartir_path / "codes"
            climate_path = codes_path / "climate"
            climate_path.mkdir(parents=True)
            (climate_path / "1000.json").write_text('{"manufacturer": "Daikin"}')
            (climate_path / "1001.json").write_text('{"manufacturer": "Samsung"}')
            
            detector = SmartIRDetector(str(config_path))
            status = detector.get_status()
            
            assert status["installed"] is True
            assert status["version"] == "1.17.9"
            assert "climate" in status["platforms"]
            assert status["device_counts"]["climate"] == 2
            assert "create" in status["recommendation"]["message"].lower()


class TestCodeFileValidation:
    """Test code file validation"""

    def test_validate_code_file_success(self):
        """Test validating a valid code file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            code_data = {
                "manufacturer": "Daikin",
                "supportedModels": ["FTXS25CVMA"],
                "supportedController": "Broadlink",
                "commandsEncoding": "Base64",
                "commands": {"off": "test_code"}
            }
            (climate_path / "1000.json").write_text(json.dumps(code_data))
            
            detector = SmartIRDetector(str(config_path))
            result = detector.validate_code_file("climate", 1000)
            
            assert result["valid"] is True
            assert result["exists"] is True
            assert result["error"] is None
            assert result["data"]["manufacturer"] == "Daikin"

    def test_validate_code_file_not_found(self):
        """Test validating non-existent code file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = SmartIRDetector(tmpdir)
            result = detector.validate_code_file("climate", 1000)
            
            assert result["valid"] is False
            assert result["exists"] is False
            assert "not found" in result["error"]

    def test_validate_code_file_missing_fields(self):
        """Test validating code file with missing required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            # Missing 'commands' field
            code_data = {
                "manufacturer": "Daikin",
                "supportedController": "Broadlink",
                "commandsEncoding": "Base64"
            }
            (climate_path / "1000.json").write_text(json.dumps(code_data))
            
            detector = SmartIRDetector(str(config_path))
            result = detector.validate_code_file("climate", 1000)
            
            assert result["valid"] is False
            assert result["exists"] is True
            assert "Missing required fields" in result["error"]

    def test_validate_code_file_invalid_json(self):
        """Test validating code file with invalid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "codes" / "climate"
            climate_path.mkdir(parents=True)
            
            (climate_path / "1000.json").write_text("invalid json")
            
            detector = SmartIRDetector(str(config_path))
            result = detector.validate_code_file("climate", 1000)
            
            assert result["valid"] is False
            assert result["exists"] is True
            assert "Invalid JSON" in result["error"]


class TestCodeFileWriting:
    """Test code file writing"""

    def test_write_code_file_success(self):
        """Test writing a new code file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            
            code_data = {
                "manufacturer": "Custom",
                "supportedController": "Broadlink",
                "commandsEncoding": "Base64",
                "commands": {"off": "test"}
            }
            
            detector = SmartIRDetector(str(config_path))
            result = detector.write_code_file("climate", 10000, code_data)
            
            assert result["success"] is True
            assert result["error"] is None
            assert "10000.json" in result["file"]
            
            # Verify file was created
            code_file = Path(result["file"])
            assert code_file.exists()
            
            # Verify content
            with open(code_file) as f:
                saved_data = json.load(f)
            assert saved_data["manufacturer"] == "Custom"

    def test_write_code_file_already_exists(self):
        """Test that writing fails if file already exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            climate_path = config_path / "custom_components" / "smartir" / "custom_codes" / "climate"
            climate_path.mkdir(parents=True)
            (climate_path / "10000.json").write_text('{}')
            
            detector = SmartIRDetector(str(config_path))
            result = detector.write_code_file("climate", 10000, {})
            
            assert result["success"] is False
            assert "already exists" in result["error"]

    def test_write_code_file_creates_directory(self):
        """Test that writing creates platform directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir)
            
            detector = SmartIRDetector(str(config_path))
            result = detector.write_code_file("climate", 10000, {"test": "data"})
            
            assert result["success"] is True
            
            # Verify directory was created in custom_codes
            climate_path = config_path / "custom_components" / "smartir" / "custom_codes" / "climate"
            assert climate_path.exists()


class TestInstallInstructions:
    """Test installation instructions"""

    def test_get_install_instructions(self):
        """Test getting installation instructions"""
        detector = SmartIRDetector()
        instructions = detector.get_install_instructions()
        
        assert "title" in instructions
        assert "methods" in instructions
        assert len(instructions["methods"]) >= 2
        assert "HACS" in instructions["methods"][0]["name"]
        assert "Manual" in instructions["methods"][1]["name"]
        assert "links" in instructions
        assert "github" in instructions["links"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
