#!/usr/bin/env python3
"""
Regression tests for stateless flag persistence on device creation (Issue #55)

The "Stateless Device" checkbox was dropped when creating a new device:
- POST /api/devices/managed did not copy the stateless field into device_data
- The frontend store's createDevice action did not send the stateless field

Editing a device worked because the update path passed all fields through.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

import pytest


@pytest.mark.regression
class TestStatelessDeviceCreation:
    """Stateless flag must persist when a device is created, not just edited"""

    def test_create_managed_device_persists_stateless_true(self, client):
        """POST /api/devices/managed with stateless=true must save it"""
        payload = {
            "device_name": "Garage Door",
            "entity_type": "cover",
            "device_type": "broadlink",
            "broadlink_entity": "remote.master_bedroom_rm4_pro",
            "stateless": True,
        }

        response = client.post("/api/devices/managed", json=payload)

        assert response.status_code == 201, response.get_json()
        device = response.get_json()["device"]
        assert device["stateless"] is True

        # Verify it was actually persisted, not just echoed
        get_resp = client.get("/api/devices/managed/garage_door")
        assert get_resp.status_code == 200, get_resp.get_json()
        assert get_resp.get_json()["device"]["stateless"] is True

    def test_create_managed_device_defaults_stateless_false(self, client):
        """Omitting stateless should default to False"""
        payload = {
            "device_name": "Living Room Light",
            "entity_type": "light",
            "device_type": "broadlink",
            "broadlink_entity": "remote.master_bedroom_rm4_pro",
        }

        response = client.post("/api/devices/managed", json=payload)

        assert response.status_code == 201, response.get_json()
        device = response.get_json()["device"]
        assert device["stateless"] is False

    def test_update_managed_device_keeps_stateless(self, client):
        """PUT must still save stateless (known-working path, guard against regressions)"""
        create_payload = {
            "device_name": "RF Fan",
            "entity_type": "fan",
            "device_type": "broadlink",
            "broadlink_entity": "remote.master_bedroom_rm4_pro",
            "stateless": False,
        }
        response = client.post("/api/devices/managed", json=create_payload)
        assert response.status_code == 201, response.get_json()

        update_payload = {"stateless": True}
        put_resp = client.put("/api/devices/managed/rf_fan", json=update_payload)

        assert put_resp.status_code == 200, put_resp.get_json()
        device = put_resp.get_json()["device"]
        assert device["stateless"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
