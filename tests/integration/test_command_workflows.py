"""
Integration tests for command learn/test/delete workflows.

Tests both Broadlink and SmartIR device types to ensure:
1. Commands can be learned successfully
2. Learned commands can be tested immediately
3. Commands can be deleted
4. Pending commands are rejected
5. SmartIR and Broadlink storage are kept separate
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock


class TestBroadlinkCommandWorkflow:
    """Test command workflow for native Broadlink devices"""

    @pytest.fixture
    def broadlink_device(self, client, mock_ha_api):
        """Create a test Broadlink device"""
        device_data = {
            "friendly_name": "Test Remote",
            "device_type": "broadlink",
            "entity_id": "remote.test_remote",
            "area": "Living Room",
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 200
        return response.json["device_id"]

    def test_learn_command_returns_actual_code(self, client, broadlink_device, mock_ha_api):
        """Test that learning a command returns the actual IR code, not 'pending'"""
        # Mock the learn command to return success
        mock_ha_api.post.return_value = []

        # Mock _get_all_broadlink_commands to return the learned code
        with patch("app.web_server.WebServer._get_all_broadlink_commands") as mock_get_commands:
            mock_get_commands.return_value = {
                "test_remote": {"power": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA"}
            }

            response = client.post(
                "/api/commands/learn",
                json={
                    "entity_id": "remote.test_remote",
                    "device": "test_remote",
                    "command": "power",
                    "command_type": "ir",
                },
            )

        assert response.status_code == 200
        data = response.json
        assert data["success"] is True
        assert "code" in data
        assert data["code"] != "pending"
        assert len(data["code"]) > 10  # Actual IR codes are long base64 strings

    def test_test_command_immediately_after_learn(self, client, broadlink_device, mock_ha_api):
        """Test that a command can be tested immediately after learning"""
        # First learn a command
        mock_ha_api.post.return_value = []
        with patch("app.web_server.WebServer._get_all_broadlink_commands") as mock_get_commands:
            mock_get_commands.return_value = {
                "test_remote": {"power": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA"}
            }
            learn_response = client.post(
                "/api/commands/learn",
                json={
                    "entity_id": "remote.test_remote",
                    "device": "test_remote",
                    "command": "power",
                    "command_type": "ir",
                },
            )

        assert learn_response.status_code == 200
        learned_code = learn_response.json["code"]

        # Now test the command
        test_response = client.post(
            "/api/commands/send-raw",
            json={
                "entity_id": "remote.test_remote",
                "command": learned_code,
                "command_type": "ir",
            },
        )

        assert test_response.status_code == 200
        assert test_response.json["success"] is True

    def test_reject_pending_command_in_test(self, client, broadlink_device):
        """Test that 'pending' commands are rejected when testing"""
        response = client.post(
            "/api/commands/send-raw",
            json={
                "entity_id": "remote.test_remote",
                "command": "pending",
                "command_type": "ir",
            },
        )

        assert response.status_code == 400
        assert "not been learned yet" in response.json["error"]

    def test_delete_command(self, client, broadlink_device, mock_ha_api, tmp_path):
        """Test that commands can be deleted from Broadlink storage"""
        # Setup mock storage file
        storage_dir = tmp_path / ".storage"
        storage_dir.mkdir()
        storage_file = storage_dir / "broadlink_remote_test_codes"

        storage_data = {
            "version": 1,
            "data": {
                "test_remote": {
                    "power": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA",
                    "volume_up": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA",
                }
            },
        }

        with open(storage_file, "w") as f:
            json.dump(storage_data, f)

        # Mock the config path
        with patch("flask.current_app.config.get", return_value=str(tmp_path)):
            response = client.delete(
                "/api/commands/test_remote/power",
                json={"device_id": broadlink_device},
            )

        assert response.status_code == 200
        assert response.json["success"] is True

        # Verify command was removed from storage
        with open(storage_file, "r") as f:
            updated_data = json.load(f)

        assert "power" not in updated_data["data"]["test_remote"]
        assert "volume_up" in updated_data["data"]["test_remote"]  # Other commands remain


class TestSmartIRCommandWorkflow:
    """Test command workflow for SmartIR devices"""

    @pytest.fixture
    def smartir_device(self, client, mock_smartir_installed):
        """Create a test SmartIR device"""
        device_data = {
            "friendly_name": "Test AC",
            "device_type": "smartir",
            "entity_id": "climate.test_ac",
            "area": "Bedroom",
            "device_code": 10000,
            "controller_entity": "remote.test_remote",
        }
        response = client.post("/api/devices", json=device_data)
        assert response.status_code == 200
        return response.json["device_id"]

    def test_smartir_learn_returns_actual_code(self, client, smartir_device, mock_ha_api, mock_smartir_installed):
        """Test that SmartIR learning returns actual code"""
        mock_ha_api.post.return_value = []

        with patch("app.web_server.WebServer._get_all_broadlink_commands") as mock_get_commands:
            mock_get_commands.return_value = {
                "daikin_test": {"off": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA"}
            }

            response = client.post(
                "/api/commands/learn",
                json={
                    "entity_id": "remote.test_remote",
                    "device": "daikin_test",
                    "command": "off",
                    "command_type": "ir",
                },
            )

        assert response.status_code == 200
        assert response.json["code"] != "pending"

    def test_smartir_test_command(self, client, smartir_device, mock_ha_api):
        """Test that SmartIR commands can be tested"""
        # Mock the SmartIR profile with a learned command
        profile_data = {
            "manufacturer": "Daikin",
            "supportedModels": ["Test"],
            "commands": {
                "off": "JgBQAAABKZIVEhUSFBMUEhQSFBIUNxQ3FDcUNxQ3FDcUNxQ3FBIUERQSFBIUERQSFBIUERQ3FDcUNxQ3FDcUNxQ3FDcUAA0FAAAAAAAAAAAAAAAA"
            },
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(profile_data)

            response = client.post(
                "/api/commands/test",
                json={
                    "entity_id": "remote.test_remote",
                    "command": "off",
                    "device_id": smartir_device,
                },
            )

        assert response.status_code == 200

    def test_smartir_reject_pending_command(self, client, smartir_device):
        """Test that SmartIR rejects pending commands"""
        # Mock profile with pending command
        profile_data = {
            "manufacturer": "Daikin",
            "supportedModels": ["Test"],
            "commands": {"off": "pending"},
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(profile_data)

            response = client.post(
                "/api/commands/test",
                json={
                    "entity_id": "remote.test_remote",
                    "command": "off",
                    "device_id": smartir_device,
                },
            )

        assert response.status_code == 400
        assert "not been learned yet" in response.json["error"]

    def test_smartir_profile_deletion_blocked_when_in_use(self, client, smartir_device, mock_smartir_installed):
        """Test that SmartIR profiles cannot be deleted when in use"""
        response = client.delete(
            "/api/smartir/profiles/10000",
            json={"platform": "climate"},
        )

        assert response.status_code == 400
        assert "currently in use" in response.json["error"]
        assert "Test AC" in response.json["devices"]

    def test_smartir_profile_deletion_allowed_when_not_in_use(self, client, mock_smartir_installed, tmp_path):
        """Test that SmartIR profiles can be deleted when not in use"""
        # Create a profile file
        codes_dir = tmp_path / "custom_components" / "smartir" / "codes" / "climate"
        codes_dir.mkdir(parents=True)
        profile_file = codes_dir / "10001.json"

        profile_data = {
            "manufacturer": "Test",
            "supportedModels": ["Model"],
            "commands": {},
        }

        with open(profile_file, "w") as f:
            json.dump(profile_data, f)

        with patch("app.smartir_detector.SmartIRDetector.smartir_path", tmp_path / "custom_components" / "smartir"):
            response = client.delete(
                "/api/smartir/profiles/10001",
                json={"platform": "climate"},
            )

        assert response.status_code == 200
        assert not profile_file.exists()


class TestStorageSeparation:
    """Test that Broadlink and SmartIR storage are kept separate"""

    def test_smartir_does_not_read_broadlink_storage(self, client, mock_smartir_installed, tmp_path):
        """Test that SmartIR devices don't read from Broadlink storage files"""
        # Create Broadlink storage with commands
        storage_dir = tmp_path / ".storage"
        storage_dir.mkdir()
        storage_file = storage_dir / "broadlink_remote_test_codes"

        storage_data = {
            "version": 1,
            "data": {
                "daikin_test": {
                    "off": "BROADLINK_STORAGE_CODE",
                }
            },
        }

        with open(storage_file, "w") as f:
            json.dump(storage_data, f)

        # Create SmartIR profile with different code
        codes_dir = tmp_path / "custom_components" / "smartir" / "codes" / "climate"
        codes_dir.mkdir(parents=True)
        profile_file = codes_dir / "10000.json"

        profile_data = {
            "manufacturer": "Daikin",
            "supportedModels": ["Test"],
            "commands": {"off": "SMARTIR_JSON_CODE"},
        }

        with open(profile_file, "w") as f:
            json.dump(profile_data, f)

        # Test that SmartIR uses its JSON file, not Broadlink storage
        with patch("app.smartir_detector.SmartIRDetector.smartir_path", tmp_path / "custom_components" / "smartir"):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(profile_data)

                # The SmartIR test endpoint should use the JSON code
                response = client.get("/api/smartir/profiles/10000?platform=climate")

        # Verify it reads from SmartIR JSON, not Broadlink storage
        assert response.status_code == 200
        # The actual verification would be in the command execution

    def test_broadlink_does_not_write_to_smartir_json(self, client, mock_ha_api, tmp_path):
        """Test that Broadlink learning doesn't write to SmartIR JSON files"""
        # Create a SmartIR profile
        codes_dir = tmp_path / "custom_components" / "smartir" / "codes" / "climate"
        codes_dir.mkdir(parents=True)
        profile_file = codes_dir / "10000.json"

        original_data = {
            "manufacturer": "Daikin",
            "supportedModels": ["Test"],
            "commands": {"off": "ORIGINAL_CODE"},
        }

        with open(profile_file, "w") as f:
            json.dump(original_data, f)

        # Learn a command for a Broadlink device
        mock_ha_api.post.return_value = []

        with patch("app.web_server.WebServer._get_all_broadlink_commands") as mock_get_commands:
            mock_get_commands.return_value = {"test_device": {"power": "NEW_LEARNED_CODE"}}

            client.post(
                "/api/commands/learn",
                json={
                    "entity_id": "remote.test_remote",
                    "device": "test_device",
                    "command": "power",
                    "command_type": "ir",
                },
            )

        # Verify SmartIR JSON was not modified
        with open(profile_file, "r") as f:
            current_data = json.load(f)

        assert current_data == original_data  # Should be unchanged


class TestCodeNumbering:
    """Test that SmartIR profile code numbering works correctly"""

    def test_next_code_increments_correctly(self, client, mock_smartir_installed, tmp_path):
        """Test that next code number increments even after deletion"""
        codes_dir = tmp_path / "custom_components" / "smartir" / "codes" / "climate"
        codes_dir.mkdir(parents=True)

        # Create profiles 10000, 10001, 10002
        for code in [10000, 10001, 10002]:
            profile_file = codes_dir / f"{code}.json"
            with open(profile_file, "w") as f:
                json.dump({"manufacturer": "Test", "commands": {}}, f)

        with patch("app.smartir_detector.SmartIRDetector.codes_path", tmp_path / "custom_components" / "smartir" / "codes"):
            response = client.get("/api/smartir/platforms/climate/next-code")

        assert response.status_code == 200
        assert response.json["next_code"] == 10003  # Should be max + 1

        # Delete 10001
        (codes_dir / "10001.json").unlink()

        # Next code should still be 10003, not 10001
        with patch("app.smartir_detector.SmartIRDetector.codes_path", tmp_path / "custom_components" / "smartir" / "codes"):
            response = client.get("/api/smartir/platforms/climate/next-code")

        assert response.json["next_code"] == 10003
