#!/usr/bin/env python3
"""
Unit tests for Controller Detector
Tests detection of controller types and capabilities
"""

import pytest
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))

from controller_detector import ControllerDetector


class TestControllerDetector:
    """Test controller type detection"""
    
    @pytest.fixture
    def detector(self):
        """Create a controller detector instance"""
        return ControllerDetector()
    
    def test_detect_broadlink_rm4_pro(self, detector):
        """Test detection of Broadlink RM4 Pro"""
        result = detector.detect_controller_type('remote.broadlink_rm4_pro')
        
        assert result['type'] == 'broadlink'
        assert result['confidence'] == 'high'
        assert result['supports_learning'] is True
        assert result['supports_deletion'] is True
        assert result['supports_sending'] is True
        assert result['name'] == 'Broadlink'
    
    def test_detect_broadlink_rm_mini(self, detector):
        """Test detection of Broadlink RM Mini"""
        result = detector.detect_controller_type('remote.rm_mini_living_room')
        
        assert result['type'] == 'broadlink'
        assert result['confidence'] == 'high'
        assert result['supports_learning'] is True
    
    def test_detect_xiaomi_remote(self, detector):
        """Test detection of Xiaomi IR remote"""
        result = detector.detect_controller_type('remote.xiaomi_ir_remote')
        
        assert result['type'] == 'xiaomi'
        assert result['confidence'] == 'high'
        assert result['supports_learning'] is False
        assert result['supports_deletion'] is False
        assert result['supports_sending'] is True
        assert result['name'] == 'Xiaomi/Aqara'
    
    def test_detect_aqara_remote(self, detector):
        """Test detection of Aqara remote"""
        result = detector.detect_controller_type('remote.aqara_hub_ir')
        
        assert result['type'] == 'xiaomi'
        assert result['confidence'] == 'high'
        assert result['supports_learning'] is False
    
    def test_detect_harmony_hub(self, detector):
        """Test detection of Harmony Hub"""
        result = detector.detect_controller_type('remote.harmony_hub')
        
        assert result['type'] == 'harmony'
        assert result['confidence'] == 'high'
        assert result['supports_learning'] is False
        assert result['supports_deletion'] is False
        assert result['supports_sending'] is True
        assert result['name'] == 'Harmony Hub'
    
    def test_detect_esphome_remote(self, detector):
        """Test detection of ESPHome IR blaster"""
        result = detector.detect_controller_type('remote.esphome_ir_blaster')
        
        assert result['type'] == 'esphome'
        assert result['confidence'] == 'medium'
        assert result['supports_learning'] is False  # Has own mechanism
        assert result['supports_deletion'] is False
        assert result['supports_sending'] is True
        assert result['name'] == 'ESPHome'
    
    def test_detect_unknown_remote(self, detector):
        """Test detection of unknown remote type"""
        result = detector.detect_controller_type('remote.custom_ir_blaster')
        
        assert result['type'] == 'unknown'
        assert result['confidence'] == 'low'
        assert result['supports_learning'] is False  # Assume no learning for safety
        assert result['supports_deletion'] is False
        assert result['supports_sending'] is True
        assert result['name'] == 'Generic Remote'
    
    def test_detect_empty_entity(self, detector):
        """Test detection with empty entity ID"""
        result = detector.detect_controller_type('')
        
        assert result['type'] == 'unknown'
        assert result['confidence'] == 'low'
    
    def test_detect_none_entity(self, detector):
        """Test detection with None entity ID"""
        result = detector.detect_controller_type(None)
        
        assert result['type'] == 'unknown'
        assert result['confidence'] == 'low'
    
    def test_supports_learning_broadlink(self, detector):
        """Test supports_learning helper for Broadlink"""
        assert detector.supports_learning('remote.broadlink_rm4_pro') is True
    
    def test_supports_learning_xiaomi(self, detector):
        """Test supports_learning helper for Xiaomi"""
        assert detector.supports_learning('remote.xiaomi_ir_remote') is False
    
    def test_supports_deletion_broadlink(self, detector):
        """Test supports_deletion helper for Broadlink"""
        assert detector.supports_deletion('remote.broadlink_rm4_pro') is True
    
    def test_supports_deletion_harmony(self, detector):
        """Test supports_deletion helper for Harmony Hub"""
        assert detector.supports_deletion('remote.harmony_hub') is False
    
    def test_get_capabilities_broadlink(self, detector):
        """Test get_capabilities for Broadlink"""
        caps = detector.get_capabilities('broadlink')
        
        assert caps['supports_learning'] is True
        assert caps['supports_deletion'] is True
        assert caps['supports_sending'] is True
        assert 'icon' in caps
        assert 'color' in caps
    
    def test_get_capabilities_xiaomi(self, detector):
        """Test get_capabilities for Xiaomi"""
        caps = detector.get_capabilities('xiaomi')
        
        assert caps['supports_learning'] is False
        assert caps['supports_deletion'] is False
        assert caps['supports_sending'] is True
    
    def test_all_types_have_required_fields(self, detector):
        """Test that all controller types have required fields"""
        required_fields = [
            'name', 'supports_learning', 'supports_deletion', 
            'supports_sending', 'icon', 'color', 'description'
        ]
        
        for controller_type in detector.CONTROLLER_TYPES:
            type_info = detector.CONTROLLER_TYPES[controller_type]
            for field in required_fields:
                assert field in type_info, f"{controller_type} missing {field}"
    
    def test_case_insensitive_detection(self, detector):
        """Test that detection is case-insensitive"""
        result1 = detector.detect_controller_type('remote.BROADLINK_RM4_PRO')
        result2 = detector.detect_controller_type('remote.Broadlink_RM4_Pro')
        result3 = detector.detect_controller_type('remote.broadlink_rm4_pro')
        
        assert result1['type'] == 'broadlink'
        assert result2['type'] == 'broadlink'
        assert result3['type'] == 'broadlink'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
