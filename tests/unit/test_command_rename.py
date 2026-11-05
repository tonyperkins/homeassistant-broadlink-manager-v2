#!/usr/bin/env python3
"""
Tests for renaming tracked commands (Issue #57)

Renaming must preserve the learned command data so users can fix typos
without deleting and relearning the command.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest

IR_CODE = "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQ3FAANBQ=="


def create_device_with_command(client, device_name="Test Fan", command="turn_on"):
    """Helper: create a managed device and seed one command via the paste API"""
    create_resp = client.post(
        "/api/devices/managed",
        json={
            "device_name": device_name,
            "entity_type": "fan",
            "device_type": "broadlink",
            "broadlink_entity": "remote.master_bedroom_rm4_pro",
        },
    )
    assert create_resp.status_code == 201, create_resp.get_json()
    device_id = create_resp.get_json()["device"]["id"]

    paste_resp = client.post(
        "/api/commands/paste",
        json={
            "device_id": device_id,
            "command_name": command,
            "command_data": IR_CODE,
            "command_type": "ir",
        },
    )
    assert paste_resp.status_code == 200, paste_resp.get_json()

    return device_id


@pytest.mark.regression
class TestRenameCommandAPI:
    """POST /api/commands/<device_id>/<command_name>/rename"""

    def test_rename_preserves_command_data(self, client):
        device_id = create_device_with_command(client, command="tun_on")

        response = client.post(
            f"/api/commands/{device_id}/tun_on/rename",
            json={"new_name": "turn_on"},
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["success"] is True
        assert response.get_json()["renamed"] is True

        # Verify old name gone, new name present with the same learned code
        device = client.get(f"/api/devices/managed/{device_id}").get_json()["device"]
        assert "tun_on" not in device["commands"]
        assert device["commands"]["turn_on"]["data"] == IR_CODE

    def test_rename_to_existing_name_conflicts(self, client):
        device_id = create_device_with_command(client, command="turn_on")
        client.post(
            "/api/commands/paste",
            json={
                "device_id": device_id,
                "command_name": "speed_1",
                "command_data": IR_CODE,
                "command_type": "ir",
            },
        )

        response = client.post(
            f"/api/commands/{device_id}/speed_1/rename",
            json={"new_name": "turn_on"},
        )

        assert response.status_code == 409, response.get_json()
        # Original command must be untouched
        device = client.get(f"/api/devices/managed/{device_id}").get_json()["device"]
        assert "speed_1" in device["commands"]

    def test_rename_missing_command_404(self, client):
        device_id = create_device_with_command(client)

        response = client.post(
            f"/api/commands/{device_id}/nonexistent/rename",
            json={"new_name": "turn_off"},
        )

        assert response.status_code == 404, response.get_json()

    def test_rename_missing_device_404(self, client):
        response = client.post(
            "/api/commands/no_such_device/turn_on/rename",
            json={"new_name": "turn_off"},
        )

        assert response.status_code == 404, response.get_json()

    def test_rename_rejects_invalid_names(self, client):
        device_id = create_device_with_command(client, command="turn_on")

        for bad_name in ["", "   ", "has space", "semicolons;are;bad", "qùoted"]:
            response = client.post(
                f"/api/commands/{device_id}/turn_on/rename",
                json={"new_name": bad_name},
            )
            assert response.status_code == 400, (bad_name, response.get_json())

        # Command must be untouched
        device = client.get(f"/api/devices/managed/{device_id}").get_json()["device"]
        assert "turn_on" in device["commands"]

    def test_rename_same_name_is_noop(self, client):
        device_id = create_device_with_command(client, command="turn_on")

        response = client.post(
            f"/api/commands/{device_id}/turn_on/rename",
            json={"new_name": "turn_on"},
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["renamed"] is False


@pytest.mark.regression
class TestRenameCommandManager:
    """DeviceManager.rename_command unit tests"""

    def test_rename_command(self, device_manager):
        device_manager.create_device(
            "test_fan",
            {
                "name": "Test Fan",
                "entity_type": "fan",
                "device_type": "broadlink",
                "broadlink_entity": "remote.test",
            },
        )
        device_manager.add_command(
            "test_fan", "tun_on", {"data": IR_CODE, "type": "ir"}
        )

        assert device_manager.rename_command("test_fan", "tun_on", "turn_on") is True

        commands = device_manager.get_device_commands("test_fan")
        assert "tun_on" not in commands
        assert commands["turn_on"] == {"data": IR_CODE, "type": "ir"}

    def test_rename_preserves_position(self, device_manager):
        device_manager.create_device(
            "test_fan",
            {
                "name": "Test Fan",
                "entity_type": "fan",
                "device_type": "broadlink",
                "broadlink_entity": "remote.test",
            },
        )
        device_manager.add_command("test_fan", "first", {"data": "a"})
        device_manager.add_command("test_fan", "second", {"data": "b"})
        device_manager.add_command("test_fan", "third", {"data": "c"})

        device_manager.rename_command("test_fan", "second", "renamed_second")

        assert list(device_manager.get_device_commands("test_fan").keys()) == [
            "first",
            "renamed_second",
            "third",
        ]

    def test_rename_missing_command_fails(self, device_manager):
        device_manager.create_device(
            "test_fan",
            {
                "name": "Test Fan",
                "entity_type": "fan",
                "device_type": "broadlink",
                "broadlink_entity": "remote.test",
            },
        )

        assert device_manager.rename_command("test_fan", "ghost", "new_name") is False

    def test_rename_missing_device_fails(self, device_manager):
        assert device_manager.rename_command("ghost", "a", "b") is False

    def test_rename_duplicate_fails(self, device_manager):
        device_manager.create_device(
            "test_fan",
            {
                "name": "Test Fan",
                "entity_type": "fan",
                "device_type": "broadlink",
                "broadlink_entity": "remote.test",
            },
        )
        device_manager.add_command("test_fan", "a", {"data": "1"})
        device_manager.add_command("test_fan", "b", {"data": "2"})

        assert device_manager.rename_command("test_fan", "a", "b") is False
        commands = device_manager.get_device_commands("test_fan")
        assert commands["a"] == {"data": "1"}
        assert commands["b"] == {"data": "2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
