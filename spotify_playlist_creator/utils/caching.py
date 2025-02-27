"""Utilities for caching data."""

import json
import os
import time
import numpy as np
from datetime import datetime
from spotify_playlist_creator import config

def save_cache(data, cache_file):
    """Save data to a cache file."""
    # Add timestamp for cache invalidation
    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Make sure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(cache_file)), exist_ok=True)
    
    # Convert numpy data types to standard Python types before saving
    processed_data = convert_numpy_types(data)
    
    with open(cache_file, 'w') as f:
        json.dump(processed_data, f, indent=2)

def convert_numpy_types(obj):
    """
    Recursively convert numpy data types to standard Python types for JSON serialization.
    
    Args:
        obj: The object to convert (can be dict, list, numpy array or scalar)
        
    Returns:
        Object with numpy types converted to standard Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime, np.datetime64)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

def load_cache(cache_file):
    """Load data from a cache file."""
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def is_cache_valid(cache_file, max_age_hours=None):
    """Check if cache file exists and is recent enough."""
    if max_age_hours is None:
        max_age_hours = config.DEFAULT_CACHE_EXPIRY_HOURS
        
    if not os.path.exists(cache_file):
        return False
        
    try:
        # Get file modification time
        mod_time = os.path.getmtime(cache_file)
        current_time = time.time()
        
        # Convert hours to seconds
        max_age_seconds = max_age_hours * 60 * 60
        
        # Check if cache is still valid
        return (current_time - mod_time) < max_age_seconds
    except:
        return False
