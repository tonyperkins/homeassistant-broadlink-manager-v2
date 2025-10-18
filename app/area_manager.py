#!/usr/bin/env python3
"""
Area Manager for Broadlink Manager Add-on
Handles automatic area assignment for generated entities using WebSocket API
"""

import logging
import json
import asyncio
import websockets
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AreaManager:
    """Manage area assignments for Home Assistant entities via WebSocket API"""

    def __init__(self, ha_url: str, ha_token: str):
        """
        Initialize area manager

        Args:
            ha_url: Home Assistant API URL (e.g., http://supervisor/core)
            ha_token: Supervisor token for authentication
        """
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.ws_url = ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        self.message_id = 1

    async def _send_ws_command(self, command_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Send a command via WebSocket and wait for response

        Args:
            command_type: WebSocket command type (e.g., 'config/area_registry/list')
            **kwargs: Additional parameters for the command

        Returns:
            Response data or None on error
        """
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Receive auth required message
                auth_msg = await websocket.recv()
                auth_data = json.loads(auth_msg)

                if auth_data.get("type") != "auth_required":
                    logger.error(f"Unexpected message: {auth_data}")
                    return None

                # Send auth
                await websocket.send(json.dumps({"type": "auth", "access_token": self.ha_token}))

                # Receive auth result
                auth_result = await websocket.recv()
                auth_result_data = json.loads(auth_result)

                if auth_result_data.get("type") != "auth_ok":
                    logger.error(f"Auth failed: {auth_result_data}")
                    return None

                # Send command
                command = {"id": self.message_id, "type": command_type, **kwargs}
                self.message_id += 1

                await websocket.send(json.dumps(command))

                # Wait for response
                response = await websocket.recv()
                response_data = json.loads(response)

                if response_data.get("success"):
                    return response_data.get("result")
                else:
                    logger.error(f"Command failed: {response_data.get('error')}")
                    return None

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            return None

    async def get_or_create_area(self, area_name: str) -> Optional[str]:
        """
        Get area ID by name, or create it if it doesn't exist

        Args:
            area_name: Human-readable area name (e.g., "Tony's Office")

        Returns:
            Area ID if found/created, None on error
        """
        try:
            # Get all areas via WebSocket
            areas = await self._send_ws_command("config/area_registry/list")

            if not areas:
                logger.warning("No areas returned from WebSocket")
                return None

            # Look for existing area (case-insensitive)
            for area in areas:
                if area.get("name", "").lower() == area_name.lower():
                    area_id = area.get("area_id")
                    logger.info(f"Found existing area: {area_name} (ID: {area_id})")
                    return area_id

            # Area doesn't exist, create it via WebSocket
            logger.info(f"Creating new area: {area_name}")
            new_area = await self._send_ws_command("config/area_registry/create", name=area_name)

            if new_area:
                area_id = new_area.get("area_id")
                logger.info(f"Created area: {area_name} (ID: {area_id})")
                return area_id

            return None

        except Exception as e:
            logger.error(f"Error getting/creating area '{area_name}': {e}")
            return None

    async def assign_entity_to_area(self, entity_id: str, area_id: str) -> bool:
        """
        Assign an entity to an area using WebSocket API

        Args:
            entity_id: Full entity ID (e.g., "light.office_ceiling_fan_light")
            area_id: Area ID to assign to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update entity via WebSocket
            result = await self._send_ws_command("config/entity_registry/update", entity_id=entity_id, area_id=area_id)

            if result:
                logger.info(f"Assigned {entity_id} to area {area_id}")
                return True
            else:
                logger.warning(f"Failed to assign {entity_id} (entity may not exist yet)")
                return False

        except Exception as e:
            logger.error(f"Error assigning entity {entity_id} to area: {e}")
            return False

    async def check_entity_exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists in the registry

        Args:
            entity_id: Full entity ID to check

        Returns:
            True if entity exists, False otherwise
        """
        try:
            # Try to get the specific entity directly
            result = await self._send_ws_command("config/entity_registry/get", entity_id=entity_id)

            if result:
                logger.info(f"Found entity {entity_id} in registry")
                return True
            else:
                logger.warning(f"Entity {entity_id} not found in registry")
                return False

        except Exception as e:
            logger.debug(f"Entity {entity_id} not found: {e}")
            return False

    async def get_entity_area(self, entity_id: str) -> Optional[str]:
        """
        Get the area assigned to an entity (if any)

        Args:
            entity_id: Full entity ID to check

        Returns:
            Area ID if entity is assigned to an area, None otherwise
        """
        try:
            # Get entity details from registry
            result = await self._send_ws_command("config/entity_registry/get", entity_id=entity_id)

            if result:
                area_id = result.get("area_id")
                if area_id:
                    logger.info(f"Entity {entity_id} is assigned to area: {area_id}")
                else:
                    logger.info(f"Entity {entity_id} has no area assignment")
                return area_id
            else:
                logger.warning(f"Entity {entity_id} not found in registry")
                return None

        except Exception as e:
            logger.error(f"Error getting area for entity {entity_id}: {e}")
            return None

    async def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full entity details from registry including area assignment

        Args:
            entity_id: Full entity ID to check

        Returns:
            Entity details dict with area_id, name, etc., or None if not found
        """
        try:
            result = await self._send_ws_command("config/entity_registry/get", entity_id=entity_id)

            if result:
                logger.info(f"Retrieved details for entity {entity_id}")
                return result
            else:
                logger.warning(f"Entity {entity_id} not found in registry")
                return None

        except Exception as e:
            logger.error(f"Error getting entity details for {entity_id}: {e}")
            return None

    async def assign_entities_to_areas(self, entities_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assign multiple entities to their areas based on metadata

        Args:
            entities_metadata: Dict of entity configurations with area information

        Returns:
            Dict with assignment results
        """
        results = {
            "total": len(entities_metadata),
            "assigned": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        # Group entities by area
        entities_by_area = {}
        for entity_id, entity_data in entities_metadata.items():
            area_name = entity_data.get("area")
            if not area_name:
                results["skipped"] += 1
                results["details"].append(
                    {
                        "entity_id": entity_id,
                        "status": "skipped",
                        "reason": "No area specified",
                    }
                )
                continue

            if area_name not in entities_by_area:
                entities_by_area[area_name] = []
            entities_by_area[area_name].append(entity_id)

        # Process each area
        for area_name, entity_ids in entities_by_area.items():
            # Get or create the area
            area_id = await self.get_or_create_area(area_name)

            if not area_id:
                # Failed to get/create area
                for entity_id in entity_ids:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "entity_id": entity_id,
                            "status": "failed",
                            "reason": f"Could not get/create area: {area_name}",
                        }
                    )
                continue

            # Assign each entity to the area
            for entity_id in entity_ids:
                # Convert entity_id to full format (add platform prefix)
                entity_data = entities_metadata[entity_id]
                entity_type = entity_data.get("entity_type", "light")
                full_entity_id = f"{entity_type}.{entity_id}"

                # Check if entity exists first
                exists = await self.check_entity_exists(full_entity_id)

                if not exists:
                    logger.warning(f"Entity {full_entity_id} not in registry yet, skipping")
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "entity_id": full_entity_id,
                            "area": area_name,
                            "status": "skipped",
                            "reason": "Entity not in registry yet (template entities need time to register)",
                        }
                    )
                    continue

                success = await self.assign_entity_to_area(full_entity_id, area_id)

                if success:
                    results["assigned"] += 1
                    results["details"].append(
                        {
                            "entity_id": full_entity_id,
                            "area": area_name,
                            "status": "success",
                        }
                    )
                else:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "entity_id": full_entity_id,
                            "area": area_name,
                            "status": "failed",
                            "reason": "API call failed",
                        }
                    )

        logger.info(
            f"Area assignment complete: {results['assigned']} assigned, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )
        return results

    async def reload_config(self) -> bool:
        """
        Reload Home Assistant YAML configuration to pick up new template entities

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Reloading Home Assistant YAML configuration...")

            # Use call_service to reload core config (template entities)
            result = await self._send_ws_command(
                "call_service",
                domain="homeassistant",
                service="reload_core_config",
                service_data={},
                return_response=False,
            )

            if result is not None:
                logger.info("Core configuration reload initiated successfully")
                return True
            else:
                logger.warning("Config reload may have failed")
                return False

        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return False
