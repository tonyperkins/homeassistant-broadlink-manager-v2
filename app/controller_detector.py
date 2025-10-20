#!/usr/bin/env python3
"""
Controller Type Detector for Broadlink Manager
Detects the type of remote controller and its capabilities
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ControllerDetector:
    """Detect controller type and capabilities from entity ID"""

    # Controller type definitions with capabilities
    CONTROLLER_TYPES = {
        "broadlink": {
            "name": "Broadlink",
            "supports_learning": True,
            "supports_deletion": True,
            "supports_sending": True,
            "icon": "mdi:remote",
            "color": "#03a9f4",
            "description": "Broadlink RM device with learning support",
        },
        "xiaomi": {
            "name": "Xiaomi/Aqara",
            "supports_learning": False,
            "supports_deletion": False,
            "supports_sending": True,
            "icon": "mdi:cellphone-wireless",
            "color": "#ff6f00",
            "description": "Xiaomi/Aqara IR remote (uses pre-programmed codes)",
        },
        "harmony": {
            "name": "Harmony Hub",
            "supports_learning": False,
            "supports_deletion": False,
            "supports_sending": True,
            "icon": "mdi:television-guide",
            "color": "#00bcd4",
            "description": "Logitech Harmony Hub",
        },
        "esphome": {
            "name": "ESPHome",
            "supports_learning": False,  # Has own learning mechanism
            "supports_deletion": False,
            "supports_sending": True,
            "icon": "mdi:chip",
            "color": "#4caf50",
            "description": "ESPHome IR blaster (configure learning in ESPHome)",
        },
        "unknown": {
            "name": "Generic Remote",
            "supports_learning": False,  # Assume no learning for safety
            "supports_deletion": False,
            "supports_sending": True,
            "icon": "mdi:remote",
            "color": "#9e9e9e",
            "description": "Generic Home Assistant remote entity",
        },
    }

    def detect_controller_type(self, controller_entity: str) -> Dict:
        """
        Detect controller type from entity ID

        Args:
            controller_entity: Entity ID (e.g., "remote.broadlink_rm4_pro")

        Returns:
            Dict with type, confidence, and capabilities
        """
        if not controller_entity or not isinstance(controller_entity, str):
            return self._get_controller_info("unknown", "low")

        entity_lower = controller_entity.lower()

        # Check for Broadlink patterns
        if any(
            pattern in entity_lower
            for pattern in ["broadlink", "rm4", "rm_", "rm3", "rm2"]
        ):
            return self._get_controller_info("broadlink", "high")

        # Check for Xiaomi/Aqara patterns
        elif any(pattern in entity_lower for pattern in ["xiaomi", "aqara", "miio"]):
            return self._get_controller_info("xiaomi", "high")

        # Check for Harmony Hub patterns
        elif "harmony" in entity_lower:
            return self._get_controller_info("harmony", "high")

        # Check for ESPHome patterns
        elif "esphome" in entity_lower:
            return self._get_controller_info("esphome", "medium")

        # Unknown controller type
        else:
            return self._get_controller_info("unknown", "low")

    def _get_controller_info(self, controller_type: str, confidence: str) -> Dict:
        """
        Get controller information with capabilities

        Args:
            controller_type: Type of controller
            confidence: Confidence level ('high', 'medium', 'low')

        Returns:
            Dict with type, confidence, and capabilities
        """
        type_info = self.CONTROLLER_TYPES.get(
            controller_type, self.CONTROLLER_TYPES["unknown"]
        )

        return {"type": controller_type, "confidence": confidence, **type_info}

    def get_capabilities(self, controller_type: str) -> Dict:
        """
        Get capabilities for a specific controller type

        Args:
            controller_type: Type of controller

        Returns:
            Dict with capabilities
        """
        return self.CONTROLLER_TYPES.get(
            controller_type, self.CONTROLLER_TYPES["unknown"]
        )

    def supports_learning(self, controller_entity: str) -> bool:
        """
        Check if a controller supports learning commands

        Args:
            controller_entity: Entity ID

        Returns:
            True if controller supports learning
        """
        info = self.detect_controller_type(controller_entity)
        return info.get("supports_learning", False)

    def supports_deletion(self, controller_entity: str) -> bool:
        """
        Check if a controller supports deleting commands

        Args:
            controller_entity: Entity ID

        Returns:
            True if controller supports deletion
        """
        info = self.detect_controller_type(controller_entity)
        return info.get("supports_deletion", False)
