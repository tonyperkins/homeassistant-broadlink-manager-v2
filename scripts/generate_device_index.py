#!/usr/bin/env python3
"""
Generate device index from SmartIR device database
This script scans the device database and creates an index file
for fast lookups without hitting GitHub API repeatedly.

Run this periodically to update the index.
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

GITHUB_API_BASE = "https://api.github.com/repos/tonyperkins/smartir-device-database"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/tonyperkins/smartir-device-database/master"
PLATFORMS = ["climate", "media_player", "fan", "light"]


def fetch_directory(path: str) -> List[Dict[str, Any]]:
    """Fetch directory listing from GitHub API"""
    url = f"{GITHUB_API_BASE}/contents/{path}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_device_metadata(platform: str, code: str) -> Dict[str, Any]:
    """Fetch device JSON to extract metadata"""
    url = f"{GITHUB_RAW_BASE}/codes/{platform}/{code}.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def generate_index() -> Dict[str, Any]:
    """Generate complete device index"""
    index = {
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "source": "https://github.com/tonyperkins/smartir-device-database",
        "platforms": {}
    }
    
    for platform in PLATFORMS:
        print(f"Processing {platform}...")
        platform_data = {
            "manufacturers": {},
            "total_devices": 0
        }
        
        try:
            # Get all JSON files in platform directory
            files = fetch_directory(f"codes/{platform}")
            json_files = [f for f in files if f["name"].endswith(".json")]
            
            for file_info in json_files:
                code = file_info["name"].replace(".json", "")
                
                try:
                    # Fetch device metadata
                    device_data = fetch_device_metadata(platform, code)
                    manufacturer = device_data.get("manufacturer", "Unknown")
                    supported_models = device_data.get("supportedModels", [])
                    
                    # Initialize manufacturer if needed
                    if manufacturer not in platform_data["manufacturers"]:
                        platform_data["manufacturers"][manufacturer] = {
                            "models": []
                        }
                    
                    # Add device entry
                    device_entry = {
                        "code": code,
                        "models": supported_models,
                        "url": f"{GITHUB_RAW_BASE}/codes/{platform}/{code}.json"
                    }
                    
                    platform_data["manufacturers"][manufacturer]["models"].append(device_entry)
                    platform_data["total_devices"] += 1
                    
                    print(f"  ✓ {code}: {manufacturer} - {supported_models[0] if supported_models else 'Unknown'}")
                    
                except Exception as e:
                    print(f"  ✗ Error processing {code}: {e}")
                    continue
            
            # Sort manufacturers and models
            for manufacturer in platform_data["manufacturers"].values():
                manufacturer["models"].sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)
            
            index["platforms"][platform] = platform_data
            print(f"✓ {platform}: {platform_data['total_devices']} devices")
            
        except Exception as e:
            print(f"✗ Error processing {platform}: {e}")
            continue
    
    return index


def main():
    """Main entry point"""
    print("Generating SmartIR device index...")
    print("=" * 60)
    
    index = generate_index()
    
    # Save to file
    output_file = Path(__file__).parent.parent / "smartir_device_index.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"✓ Index saved to: {output_file}")
    print(f"  Total platforms: {len(index['platforms'])}")
    for platform, data in index["platforms"].items():
        print(f"  - {platform}: {data['total_devices']} devices, {len(data['manufacturers'])} manufacturers")


if __name__ == "__main__":
    main()
