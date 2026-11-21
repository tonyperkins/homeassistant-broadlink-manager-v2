#!/usr/bin/env python3
"""
Tests for the per-command repeat count editor (Issue #61)

A learned Broadlink code is [type][repeat][len][pulses...]. The repeat byte
tells the hardware how many extra times to transmit the frame back-to-back,
so raising it lets a single send behave like a held button (TV lifts, RF
motors - see issue #60).
"""

import sys
import os
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest

from broadlink_code import parse_code, set_repeat_count

# type 0xB1 (RF 433MHz), repeat 0, length 2, two pulse bytes
RF_CODE = base64.b64encode(bytes([0xB1, 0x00, 0x02, 0x00, 0x12, 0x34])).decode()
# type 0x26 (IR), repeat 5
IR_CODE = base64.b64encode(bytes([0x26, 0x05, 0x02, 0x00, 0x12, 0x34])).decode()
# type 0x51 - not a recognized Broadlink code type
UNKNOWN_TYPE_CODE = base64.b64encode(
    bytes([0x51, 0x00, 0x02, 0x00, 0x12, 0x34])
).decode()


def create_device_with_command(client, command="close", command_data=RF_CODE):
    """Helper: create a managed device and seed one command via the paste API"""
    create_resp = client.post(
        "/api/devices/managed",
        json={
            "device_name": "Test Lift",
            "entity_type": "cover",
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
            "command_data": command_data,
            "command_type": "rf",
        },
    )
    assert paste_resp.status_code == 200, paste_resp.get_json()

    return device_id


class TestBroadlinkCodeHelpers:
    """broadlink_code.parse_code / set_repeat_count unit tests"""

    def test_parse_rf_code(self):
        info = parse_code(RF_CODE)
        assert info == {
            "type_byte": "0xb1",
            "type": "rf433",
            "repeat": 0,
            "data_length": 6,
        }

    def test_parse_ir_code(self):
        info = parse_code(IR_CODE)
        assert info["type"] == "ir"
        assert info["repeat"] == 5

    def test_set_repeat_roundtrip(self):
        patched = set_repeat_count(RF_CODE, 255)
        assert parse_code(patched)["repeat"] == 255
        # Only byte 1 changes
        assert base64.b64decode(patched)[0] == 0xB1
        assert base64.b64decode(patched)[2:] == base64.b64decode(RF_CODE)[2:]

    def test_set_repeat_rejects_out_of_range(self):
        for bad in (-1, 256, 1000):
            with pytest.raises(ValueError):
                set_repeat_count(RF_CODE, bad)

    def test_set_repeat_rejects_non_int(self):
        for bad in (None, "10", 1.5, True):
            with pytest.raises(ValueError):
                set_repeat_count(RF_CODE, bad)

    def test_parse_rejects_unknown_type_byte(self):
        with pytest.raises(ValueError):
            parse_code(UNKNOWN_TYPE_CODE)

    def test_parse_rejects_invalid_base64(self):
        with pytest.raises(ValueError):
            parse_code("not!!valid!!base64!!!")

    def test_parse_rejects_too_short(self):
        with pytest.raises(ValueError):
            parse_code(base64.b64encode(bytes([0xB1])).decode())


@pytest.mark.regression
class TestCommandRepeatAPI:
    """GET/POST /api/commands/<device_id>/<command_name>/repeat"""

    def test_get_returns_current_repeat(self, client):
        device_id = create_device_with_command(client)

        response = client.get(f"/api/commands/{device_id}/close/repeat")

        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert body["repeat"] == 0
        assert body["type"] == "rf433"
        assert body["min"] == 0
        assert body["max"] == 255

    def test_set_updates_stored_code(self, client):
        device_id = create_device_with_command(client)

        response = client.post(
            f"/api/commands/{device_id}/close/repeat",
            json={"repeat": 200},
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["success"] is True
        assert response.get_json()["repeat"] == 200

        # Stored data is patched in place, other metadata preserved
        device = client.get(f"/api/devices/managed/{device_id}").get_json()["device"]
        command = device["commands"]["close"]
        assert parse_code(command["data"])["repeat"] == 200
        assert command["type"] == "rf"
        assert command["name"] == "close"

        # GET now reports the new value
        repeat = client.get(f"/api/commands/{device_id}/close/repeat").get_json()
        assert repeat["repeat"] == 200

    def test_set_missing_command_404(self, client):
        device_id = create_device_with_command(client)

        response = client.post(
            f"/api/commands/{device_id}/nonexistent/repeat",
            json={"repeat": 10},
        )

        assert response.status_code == 404, response.get_json()

    def test_set_missing_device_404(self, client):
        response = client.post(
            "/api/commands/no_such_device/close/repeat",
            json={"repeat": 10},
        )

        assert response.status_code == 404, response.get_json()

    def test_set_rejects_out_of_range(self, client):
        device_id = create_device_with_command(client)

        for bad in (-1, 256, 1000):
            response = client.post(
                f"/api/commands/{device_id}/close/repeat",
                json={"repeat": bad},
            )
            assert response.status_code == 400, (bad, response.get_json())

        # Command must be untouched
        device = client.get(f"/api/devices/managed/{device_id}").get_json()["device"]
        assert parse_code(device["commands"]["close"]["data"])["repeat"] == 0

    def test_set_rejects_non_int(self, client):
        device_id = create_device_with_command(client)

        for bad in (None, "20", 1.5):
            response = client.post(
                f"/api/commands/{device_id}/close/repeat",
                json={"repeat": bad},
            )
            assert response.status_code == 400, (bad, response.get_json())

    def test_set_rejects_unknown_code_type(self, client):
        device_id = create_device_with_command(
            client, command_data=UNKNOWN_TYPE_CODE
        )

        response = client.post(
            f"/api/commands/{device_id}/close/repeat",
            json={"repeat": 10},
        )

        assert response.status_code == 400, response.get_json()
        assert "type" in response.get_json()["error"]

    def test_get_missing_command_404(self, client):
        device_id = create_device_with_command(client)

        response = client.get(f"/api/commands/{device_id}/nonexistent/repeat")

        assert response.status_code == 404, response.get_json()


@pytest.mark.regression
class TestUpdateCommandDataManager:
    """DeviceManager.update_command_data unit tests"""

    def _create_device(self, device_manager):
        device_manager.create_device(
            "test_lift",
            {
                "name": "Test Lift",
                "entity_type": "cover",
                "device_type": "broadlink",
                "broadlink_entity": "remote.test",
            },
        )

    def test_update_command_data(self, device_manager):
        self._create_device(device_manager)
        device_manager.add_command(
            "test_lift", "close", {"data": RF_CODE, "type": "rf", "name": "close"}
        )

        new_code = set_repeat_count(RF_CODE, 255)
        assert device_manager.update_command_data("test_lift", "close", new_code) is True

        command = device_manager.get_device_commands("test_lift")["close"]
        assert command["data"] == new_code
        # Metadata preserved
        assert command["type"] == "rf"
        assert command["name"] == "close"

    def test_update_missing_command_fails(self, device_manager):
        self._create_device(device_manager)

        assert device_manager.update_command_data("test_lift", "ghost", "x") is False

    def test_update_missing_device_fails(self, device_manager):
        assert device_manager.update_command_data("ghost", "close", "x") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
