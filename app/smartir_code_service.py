#!/usr/bin/env python3
"""
SmartIR Code Service for Broadlink Manager Add-on
Fetches and caches SmartIR device codes from GitHub repository
"""

import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SmartIRCodeService:
    """Service to fetch and cache SmartIR codes from GitHub"""

    GITHUB_API_BASE = "https://api.github.com/repos/smartHomeHub/SmartIR"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/smartHomeHub/SmartIR/master"
    CACHE_TTL_HOURS = 24
    
    def __init__(self, cache_path: str = "/config/broadlink_manager/cache"):
        """
        Initialize SmartIR code service
        
        Args:
            cache_path: Path to cache directory
        """
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_path / "smartir_codes_cache.json"
        self._cache = self._load_cache()
        self._last_refresh_errors = {}  # Track errors per entity type
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk"""
        if not self.cache_file.exists():
            return {
                "last_updated": None,
                "manufacturers": {},
                "codes": {}
            }
        
        try:
            with open(self.cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {
                "last_updated": None,
                "manufacturers": {},
                "codes": {}
            }
    
    def _save_cache(self) -> bool:
        """Save cache to disk"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._cache.get("last_updated"):
            return False
        
        try:
            last_updated = datetime.fromisoformat(self._cache["last_updated"])
            age = datetime.now() - last_updated
            return age < timedelta(hours=self.CACHE_TTL_HOURS)
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
    
    def _fetch_github_directory(self, path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch directory listing from GitHub API
        
        Args:
            path: Path relative to repository root (e.g., "codes/climate")
            
        Returns:
            List of file/directory entries or None on error
        """
        url = f"{self.GITHUB_API_BASE}/contents/{path}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Network error fetching GitHub directory {path}: {e}")
            return None
    
    def _fetch_code_file(self, entity_type: str, code_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a code file from GitHub
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            code_id: Code ID (e.g., "1000")
            
        Returns:
            Parsed code data or None on error
        """
        url = f"{self.GITHUB_RAW_BASE}/codes/{entity_type}/{code_id}.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"Network error fetching code {code_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            # This is a known issue with some SmartIR repository files
            logger.debug(f"Malformed JSON in code {code_id} (SmartIR repo issue): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching code {code_id}: {e}")
            return None
    
    def refresh_codes(self, entity_type: str, force: bool = False) -> bool:
        """
        Refresh code cache for a specific entity type
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            force: Force refresh even if cache is valid
            
        Returns:
            True if successful, False otherwise
        """
        # Check if refresh is needed
        if not force and self._is_cache_valid():
            entity_cache = self._cache.get("manufacturers", {}).get(entity_type)
            if entity_cache:
                logger.info(f"Using cached data for {entity_type}")
                return True
        
        logger.info(f"Refreshing SmartIR codes for {entity_type}")
        
        # Track errors for this refresh
        errors = {
            "network_errors": 0,
            "parse_errors": 0,
            "skipped_codes": []
        }
        
        # Fetch directory listing
        files = self._fetch_github_directory(f"codes/{entity_type}")
        if not files:
            error_msg = f"Failed to fetch directory listing for {entity_type}"
            logger.error(error_msg)
            self._last_refresh_errors[entity_type] = {
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            return False
        
        # Parse code files to extract manufacturers and models
        manufacturers = defaultdict(list)
        codes_data = {}
        total_files = len([f for f in files if f.get("name", "").endswith(".json")])
        
        for file_info in files:
            if not file_info.get("name", "").endswith(".json"):
                continue
            
            code_id = file_info["name"].replace(".json", "")
            
            # Fetch the code file content
            code_data = self._fetch_code_file(entity_type, code_id)
            if not code_data:
                errors["skipped_codes"].append(code_id)
                continue
            
            manufacturer = code_data.get("manufacturer", "Unknown")
            models = code_data.get("supportedModels", [])
            
            # Store manufacturer/model mapping
            manufacturers[manufacturer].append({
                "code_id": code_id,
                "models": models,
                "controller": code_data.get("supportedController", "Broadlink")
            })
            
            # Store full code data (minimal info for cache)
            codes_data[code_id] = {
                "manufacturer": manufacturer,
                "models": models,
                "controller": code_data.get("supportedController"),
                "encoding": code_data.get("commandsEncoding")
            }
        
        # Update cache
        if "manufacturers" not in self._cache:
            self._cache["manufacturers"] = {}
        if "codes" not in self._cache:
            self._cache["codes"] = {}
        
        self._cache["manufacturers"][entity_type] = dict(manufacturers)
        self._cache["codes"][entity_type] = codes_data
        self._cache["last_updated"] = datetime.now().isoformat()
        
        # Save cache
        if self._save_cache():
            success_rate = (len(codes_data) / total_files * 100) if total_files > 0 else 0
            
            # Log summary
            if errors["skipped_codes"]:
                logger.info(
                    f"✅ Cached {len(codes_data)}/{total_files} codes for {entity_type} "
                    f"({success_rate:.1f}% success, {len(errors['skipped_codes'])} skipped)"
                )
                logger.debug(f"Skipped codes: {', '.join(errors['skipped_codes'][:10])}{'...' if len(errors['skipped_codes']) > 10 else ''}")
            else:
                logger.info(f"✅ Cached {len(codes_data)} codes for {entity_type} (100% success)")
            
            # Store error info for API access
            self._last_refresh_errors[entity_type] = {
                "skipped_count": len(errors["skipped_codes"]),
                "skipped_codes": errors["skipped_codes"][:20],  # Limit to first 20
                "success_count": len(codes_data),
                "total_count": total_files,
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        
        return False
    
    def get_manufacturers(self, entity_type: str) -> List[str]:
        """
        Get list of manufacturers for an entity type
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            
        Returns:
            Sorted list of manufacturer names
        """
        # Ensure cache is populated
        if not self._is_cache_valid() or entity_type not in self._cache.get("manufacturers", {}):
            self.refresh_codes(entity_type)
        
        manufacturers = self._cache.get("manufacturers", {}).get(entity_type, {})
        return sorted(manufacturers.keys())
    
    def get_models(self, entity_type: str, manufacturer: str) -> List[Dict[str, Any]]:
        """
        Get list of models for a manufacturer
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            manufacturer: Manufacturer name
            
        Returns:
            List of model info dicts with code_id, models, controller
        """
        # Ensure cache is populated
        if not self._is_cache_valid() or entity_type not in self._cache.get("manufacturers", {}):
            self.refresh_codes(entity_type)
        
        manufacturers = self._cache.get("manufacturers", {}).get(entity_type, {})
        models = manufacturers.get(manufacturer, [])
        
        # Sort by code_id
        return sorted(models, key=lambda x: int(x["code_id"]) if x["code_id"].isdigit() else 0)
    
    def get_code_info(self, entity_type: str, code_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached information about a specific code
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            code_id: Code ID
            
        Returns:
            Code info dict or None if not found
        """
        codes = self._cache.get("codes", {}).get(entity_type, {})
        return codes.get(code_id)
    
    def fetch_full_code(self, entity_type: str, code_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full code data from GitHub (not cached)
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            code_id: Code ID
            
        Returns:
            Full code data or None on error
        """
        return self._fetch_code_file(entity_type, code_id)
    
    def search_codes(self, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """
        Search codes by manufacturer or model name
        
        Args:
            entity_type: Entity type (climate, fan, media_player)
            query: Search query
            
        Returns:
            List of matching codes
        """
        # Ensure cache is populated
        if not self._is_cache_valid() or entity_type not in self._cache.get("codes", {}):
            self.refresh_codes(entity_type)
        
        query_lower = query.lower()
        codes = self._cache.get("codes", {}).get(entity_type, {})
        results = []
        
        for code_id, code_info in codes.items():
            manufacturer = code_info.get("manufacturer", "").lower()
            models = [m.lower() for m in code_info.get("models", [])]
            
            # Check if query matches manufacturer or any model
            if query_lower in manufacturer or any(query_lower in model for model in models):
                results.append({
                    "code_id": code_id,
                    "manufacturer": code_info.get("manufacturer"),
                    "models": code_info.get("models"),
                    "controller": code_info.get("controller")
                })
        
        return sorted(results, key=lambda x: int(x["code_id"]) if x["code_id"].isdigit() else 0)
    
    def get_refresh_errors(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        Get errors from last refresh for an entity type
        
        Args:
            entity_type: Entity type
            
        Returns:
            Error info dict or None
        """
        return self._last_refresh_errors.get(entity_type)
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        status = {
            "cache_valid": self._is_cache_valid(),
            "last_updated": self._cache.get("last_updated"),
            "cached_entity_types": list(self._cache.get("manufacturers", {}).keys()),
            "cache_file": str(self.cache_file),
            "cache_ttl_hours": self.CACHE_TTL_HOURS
        }
        
        # Add error information if available
        if self._last_refresh_errors:
            status["last_refresh_errors"] = self._last_refresh_errors
        
        return status
    
    def clear_cache(self) -> bool:
        """Clear the cache"""
        self._cache = {
            "last_updated": None,
            "manufacturers": {},
            "codes": {}
        }
        return self._save_cache()
