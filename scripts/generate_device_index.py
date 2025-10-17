#!/usr/bin/env python3
"""
Generate device index from SmartIR Code Aggregator
This script scans the aggregator's codes directory and creates an index file
for fast lookups without hitting GitHub API repeatedly.

Usage:
  # From GitHub (requires codes to be pushed):
  python scripts/generate_device_index.py
  
  # From local aggregator directory:
  python scripts/generate_device_index.py --local ../smartir-code-aggregator
"""

import json
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

GITHUB_API_BASE = "https://api.github.com/repos/tonyperkins/smartir-code-aggregator"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/tonyperkins/smartir-code-aggregator/main"
PLATFORMS = ["climate", "media_player", "fan", "light"]


def fetch_directory_github(path: str) -> List[Dict[str, Any]]:
    """Fetch directory listing from GitHub API"""
    url = f"{GITHUB_API_BASE}/contents/{path}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_directory_local(path: Path) -> List[Dict[str, Any]]:
    """Get directory listing from local filesystem"""
    if not path.exists():
        return []
    return [{"name": f.name, "type": "file"} for f in path.iterdir() if f.is_file()]


def fetch_device_metadata_github(platform: str, code: str) -> Dict[str, Any]:
    """Fetch device JSON from GitHub"""
    url = f"{GITHUB_RAW_BASE}/codes/{platform}/{code}.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_device_metadata_local(platform_path: Path, code: str) -> Dict[str, Any]:
    """Fetch device JSON from local filesystem"""
    file_path = platform_path / f"{code}.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_index(local_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generate complete device index"""
    index = {
        "version": "1.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "source": "https://github.com/tonyperkins/smartir-code-aggregator",
        "description": "Aggregated IR/RF codes from SmartIR, IRDB, and other sources in SmartIR format",
        "platforms": {}
    }
    
    use_local = local_path is not None
    
    for platform in PLATFORMS:
        print(f"Processing {platform}...")
        platform_data = {
            "manufacturers": {},
            "total_devices": 0
        }
        
        try:
            # Get all JSON files in platform directory
            if use_local:
                platform_path = local_path / "codes" / platform
                if not platform_path.exists():
                    print(f"  ⚠️  Directory not found: {platform_path}")
                    continue
                files = fetch_directory_local(platform_path)
            else:
                files = fetch_directory_github(f"codes/{platform}")
            
            json_files = [f for f in files if f["name"].endswith(".json")]
            
            for file_info in json_files:
                code = file_info["name"].replace(".json", "")
                
                try:
                    # Fetch device metadata
                    if use_local:
                        device_data = fetch_device_metadata_local(platform_path, code)
                    else:
                        device_data = fetch_device_metadata_github(platform, code)
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
    parser = argparse.ArgumentParser(description="Generate SmartIR device index")
    parser.add_argument(
        "--local",
        type=str,
        help="Path to local smartir-code-aggregator directory"
    )
    args = parser.parse_args()
    
    local_path = Path(args.local) if args.local else None
    
    if local_path:
        print(f"Generating SmartIR device index from local directory: {local_path}")
    else:
        print("Generating SmartIR device index from GitHub...")
    print("=" * 60)
    
    index = generate_index(local_path)
    
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
