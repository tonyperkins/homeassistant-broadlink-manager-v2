#!/usr/bin/env python3
"""
Unit tests for MigrationManager
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from app.migration_manager import MigrationManager
from app.storage_manager import StorageManager
from app.entity_detector import EntityDetector
from app.device_manager import DeviceManager


@pytest.fixture
def temp_storage_path():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / ".storage"
        storage_path.mkdir(parents=True, exist_ok=True)
        yield storage_path


@pytest.fixture
def temp_broadlink_manager_path():
    """Create temporary broadlink manager directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager_path = Path(tmpdir) / "broadlink_manager"
        manager_path.mkdir(parents=True, exist_ok=True)
        yield manager_path


@pytest.fixture
def storage_manager(temp_broadlink_manager_path):
    """Create StorageManager instance"""
    return StorageManager(str(temp_broadlink_manager_path))


@pytest.fixture
def device_manager(temp_broadlink_manager_path):
    """Create DeviceManager instance"""
    return DeviceManager(str(temp_broadlink_manager_path))


@pytest.fixture
def entity_detector():
    """Create EntityDetector instance"""
    return EntityDetector()


@pytest.fixture
def migration_manager(storage_manager, entity_detector, device_manager, temp_storage_path):
    """Create MigrationManager instance"""
    return MigrationManager(
        storage_manager, entity_detector, device_manager, temp_storage_path
    )


class TestMigrationManagerInitialization:
    """Test MigrationManager initialization"""

    def test_initialization(self, migration_manager, storage_manager, entity_detector, device_manager, temp_storage_path):
        """Test that MigrationManager initializes correctly"""
        assert migration_manager.storage == storage_manager
        assert migration_manager.detector == entity_detector
        assert migration_manager.device_manager == device_manager
        assert migration_manager.storage_path == temp_storage_path


class TestMigrationDeviceCreation:
    """Test that migration creates devices in devices.json"""

    @pytest.mark.asyncio
    async def test_migration_creates_devices_in_devices_json(
        self, migration_manager, temp_storage_path, device_manager
    ):
        """Test that migration creates devices in devices.json"""
        # Create mock Broadlink storage file with commands
        storage_file = temp_storage_path / "broadlink_remote_test123_codes"
        commands_data = {
            "data": {
                "Living Room TV": {
                    "power": "base64_encoded_ir_code_here",
                    "volume_up": "base64_encoded_ir_code_here",
                    "volume_down": "base64_encoded_ir_code_here",
                }
            }
        }
        
        with open(storage_file, "w") as f:
            json.dump(commands_data, f)

        # Mock Broadlink devices
        broadlink_devices = [
            {
                "unique_id": "test123",
                "entity_id": "remote.living_room",
                "name": "Living Room Remote",
                "area_name": "Living Room",
                "area_id": "living_room",
            }
        ]

        # Run migration
        result = await migration_manager.check_and_migrate(broadlink_devices)

        # Verify migration was needed and successful
        assert result.get("needed") == True
        assert result.get("success") == True
        assert result.get("scenario") == "existing_broadlink_user"

        # Verify devices were created in devices.json
        all_devices = device_manager.get_all_devices()
        assert len(all_devices) > 0, "No devices created in devices.json"

        # Check that at least one device was created
        device_found = False
        for device_id, device_data in all_devices.items():
            if "living" in device_id.lower() or "tv" in device_id.lower():
                device_found = True
                # Verify device has required fields
                assert "device_type" in device_data
                assert device_data["device_type"] == "broadlink"
                assert "commands" in device_data
                assert len(device_data["commands"]) > 0
                break

        assert device_found, "Expected device not found in devices.json"

    @pytest.mark.asyncio
    async def test_migration_skips_when_no_commands(
        self, migration_manager, temp_storage_path, device_manager
    ):
        """Test that migration skips when no commands are found"""
        # No storage files created - simulating first-time user

        broadlink_devices = [
            {
                "unique_id": "test123",
                "entity_id": "remote.bedroom",
                "name": "Bedroom Remote",
                "area_name": "Bedroom",
            }
        ]

        # Run migration
        result = await migration_manager.check_and_migrate(broadlink_devices)

        # Verify migration was skipped
        assert result.get("needed") == False
        assert result.get("scenario") == "first_time_user"

        # Verify no devices were created
        all_devices = device_manager.get_all_devices()
        assert len(all_devices) == 0

    @pytest.mark.asyncio
    async def test_migration_skips_when_metadata_exists(
        self, migration_manager, storage_manager, device_manager
    ):
        """Test that migration skips when metadata already exists"""
        # Create existing entity in metadata.json
        storage_manager.save_entity(
            "switch.existing_device",
            {
                "entity_id": "switch.existing_device",
                "friendly_name": "Existing Device",
                "entity_type": "switch",
                "device": "existing_device",
                "commands": {"power": {"type": "ir"}},
            },
        )

        broadlink_devices = []

        # Run migration
        result = await migration_manager.check_and_migrate(broadlink_devices)

        # Verify migration was skipped
        assert result.get("needed") == False
        assert result.get("scenario") == "existing_bl_manager_user"


class TestMigrationStatus:
    """Test migration status reporting"""

    def test_get_migration_status_no_migration(self, migration_manager):
        """Test getting migration status when no migration has occurred"""
        status = migration_manager.get_migration_status()

        assert status["has_metadata"] == False
        assert status["entity_count"] == 0
        assert status["migration_performed"] == False

    def test_get_migration_status_after_entity_creation(
        self, migration_manager, storage_manager
    ):
        """Test getting migration status after entities are created"""
        # Create an entity
        storage_manager.save_entity(
            "switch.test_device",
            {
                "entity_id": "switch.test_device",
                "friendly_name": "Test Device",
                "entity_type": "switch",
                "device": "test_device",
                "commands": {},
            },
        )

        status = migration_manager.get_migration_status()

        assert status["has_metadata"] == True
        assert status["entity_count"] == 1
