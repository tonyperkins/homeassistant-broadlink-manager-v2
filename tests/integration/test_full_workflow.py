"""
Integration tests for complete workflows
"""
import pytest
import yaml


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullWorkflow:
    """Test complete device creation and entity generation workflow"""
    
    async def test_create_device_learn_commands_generate_entities(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage,
        temp_storage_dir
    ):
        """
        Test full workflow:
        1. Create device
        2. Learn commands
        3. Generate entities
        4. Verify YAML files
        """
        server = web_server_with_mocks
        storage = server.storage_manager
        
        # Step 1: Create device
        device_id = "office_lamp"
        device_data = {
            "name": "Office Lamp",
            "area": "Office",
            "entity_type": "light",
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
        
        result = server.device_manager.create_device(device_id, device_data)
        assert result is True
        
        # Step 2: Learn commands
        for command in ["turn_on", "turn_off"]:
            result = await server._learn_command({
                "entity_id": "remote.master_bedroom_rm4_pro",
                "device": device_id,
                "command": command,
                "command_type": "ir"
            })
            assert result["success"] is True
            
            # Simulate HA writing to storage
            mock_broadlink_storage.add_command(
                "abc123",
                device_id,
                command,
                "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
            )
            
            # Add to device manager
            server.device_manager.add_command(device_id, command, {
                "command_type": "ir",
                "learned_at": "2025-01-10T12:00:00"
            })
        
        # Step 3: Save entity metadata
        entity_data = {
            "device": device_id,
            "entity_type": "light",
            "name": "Office Lamp",
            "area": "Office",
            "enabled": True,
            "commands": {
                "turn_on": f"{device_id}_turn_on",
                "turn_off": f"{device_id}_turn_off"
            },
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
        storage.save_entity(device_id, entity_data)
        
        # Step 4: Generate entities
        from entity_generator import EntityGenerator
        generator = EntityGenerator(
            storage_manager=storage,
            broadlink_device_id="remote.master_bedroom_rm4_pro"
        )
        
        broadlink_commands = mock_broadlink_storage.get_all_commands()
        result = generator.generate_all(broadlink_commands)
        
        assert result["success"] is True
        assert result["entities_count"] == 1
        
        # Step 5: Verify YAML files exist and are valid
        assert storage.entities_file.exists()
        assert storage.helpers_file.exists()
        
        # Verify content
        with open(storage.entities_file, 'r') as f:
            entities_yaml = yaml.safe_load(f)
        
        assert "light" in entities_yaml
        assert "office_lamp" in entities_yaml["light"][0]["lights"]
        
        # Verify entity ID format (no prefix)
        assert "light.office_lamp" not in str(entities_yaml)
    
    async def test_fan_workflow_with_multiple_speeds(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test creating a fan with multiple speed commands"""
        server = web_server_with_mocks
        storage = server.storage_manager
        
        # Create fan device
        device_id = "bedroom_fan"
        device_data = {
            "name": "Bedroom Fan",
            "area": "Master Bedroom",
            "entity_type": "fan",
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
        
        server.device_manager.create_device(device_id, device_data)
        
        # Learn speed commands
        speeds = ["speed_1", "speed_2", "speed_3", "fan_off"]
        for speed in speeds:
            result = await server._learn_command({
                "entity_id": "remote.master_bedroom_rm4_pro",
                "device": device_id,
                "command": speed,
                "command_type": "ir"
            })
            assert result["success"] is True
            
            # Simulate storage
            mock_broadlink_storage.add_command(
                "abc123",
                device_id,
                speed,
                "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
            )
            
            server.device_manager.add_command(device_id, speed, {
                "command_type": "ir",
                "learned_at": "2025-01-10T12:00:00"
            })
        
        # Save entity metadata
        entity_data = {
            "device": device_id,
            "entity_type": "fan",
            "name": "Bedroom Fan",
            "area": "Master Bedroom",
            "enabled": True,
            "commands": {speed: f"{device_id}_{speed}" for speed in speeds},
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
        storage.save_entity(device_id, entity_data)
        
        # Generate entities
        from entity_generator import EntityGenerator
        generator = EntityGenerator(
            storage_manager=storage,
            broadlink_device_id="remote.master_bedroom_rm4_pro"
        )
        
        result = generator.generate_all(mock_broadlink_storage.get_all_commands())
        
        assert result["success"] is True
        
        # Verify fan configuration
        with open(storage.entities_file, 'r') as f:
            entities_yaml = yaml.safe_load(f)
        
        assert "fan" in entities_yaml
        fan_config = entities_yaml["fan"][0]["fans"][device_id]
        assert fan_config["speed_count"] == 3  # 3 speeds (not counting fan_off)
        
        # Verify helpers were created
        with open(storage.helpers_file, 'r') as f:
            helpers_yaml = yaml.safe_load(f)
        
        assert "input_boolean" in helpers_yaml
        assert f"{device_id}_state" in helpers_yaml["input_boolean"]
        
        assert "input_select" in helpers_yaml
        assert f"{device_id}_speed" in helpers_yaml["input_select"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestMultiDeviceWorkflow:
    """Test workflows with multiple devices"""
    
    async def test_multiple_devices_same_area(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test creating multiple devices in the same area"""
        server = web_server_with_mocks
        storage = server.storage_manager
        
        devices = [
            {
                "id": "bedroom_light",
                "name": "Bedroom Light",
                "type": "light",
                "commands": ["turn_on", "turn_off"]
            },
            {
                "id": "bedroom_fan",
                "name": "Bedroom Fan",
                "type": "fan",
                "commands": ["speed_1", "speed_2", "fan_off"]
            },
            {
                "id": "bedroom_lamp",
                "name": "Bedroom Lamp",
                "type": "switch",
                "commands": ["turn_on", "turn_off"]
            }
        ]
        
        # Create all devices
        for device in devices:
            device_data = {
                "name": device["name"],
                "area": "Master Bedroom",
                "entity_type": device["type"],
                "broadlink_entity": "remote.master_bedroom_rm4_pro"
            }
            
            server.device_manager.create_device(device["id"], device_data)
            
            # Learn commands
            for command in device["commands"]:
                await server._learn_command({
                    "entity_id": "remote.master_bedroom_rm4_pro",
                    "device": device["id"],
                    "command": command,
                    "command_type": "ir"
                })
                
                mock_broadlink_storage.add_command(
                    "abc123",
                    device["id"],
                    command,
                    "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
                )
                
                server.device_manager.add_command(device["id"], command, {
                    "command_type": "ir"
                })
            
            # Save entity metadata
            entity_data = {
                "device": device["id"],
                "entity_type": device["type"],
                "name": device["name"],
                "area": "Master Bedroom",
                "enabled": True,
                "commands": {cmd: f"{device['id']}_{cmd}" for cmd in device["commands"]},
                "broadlink_entity": "remote.master_bedroom_rm4_pro"
            }
            storage.save_entity(device["id"], entity_data)
        
        # Generate entities
        from entity_generator import EntityGenerator
        generator = EntityGenerator(
            storage_manager=storage,
            broadlink_device_id="remote.master_bedroom_rm4_pro"
        )
        
        result = generator.generate_all(mock_broadlink_storage.get_all_commands())
        
        assert result["success"] is True
        assert result["entities_count"] == 3
        
        # Verify all entity types were generated
        with open(storage.entities_file, 'r') as f:
            entities_yaml = yaml.safe_load(f)
        
        assert "light" in entities_yaml
        assert "fan" in entities_yaml
        assert "switch" in entities_yaml
        
        # Verify each device
        assert "bedroom_light" in entities_yaml["light"][0]["lights"]
        assert "bedroom_fan" in entities_yaml["fan"][0]["fans"]
        assert "bedroom_lamp" in entities_yaml["switch"][0]["switches"]
