"""Configuration settings for the Spotify Color Playlist Creator."""

import os
import json
from pathlib import Path

# Try to import local config (not in version control)
try:
    from spotify_playlist_creator.config_local import *
except ImportError:
    # Default values if local config doesn't exist
    CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
    CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8080")
    
    # Genius API credentials
    GENIUS_CLIENT_ID = os.environ.get("GENIUS_CLIENT_ID", "")
    GENIUS_CLIENT_SECRET = os.environ.get("GENIUS_CLIENT_SECRET", "")
    GENIUS_CLIENT_ACCESS_TOKEN = os.environ.get("GENIUS_CLIENT_ACCESS_TOKEN", "")

# Create cache directory if it doesn't exist
CACHE_DIR = Path.home() / ".spotify_playlist_creator"
CACHE_DIR.mkdir(exist_ok=True)

# Cache file paths
TOKEN_CACHE = CACHE_DIR / "token.json" 
LIKED_SONGS_CACHE = CACHE_DIR / "liked_songs.json"
ALBUM_IMAGES_DIR = CACHE_DIR / "album_images"
COLOR_CACHE = CACHE_DIR / "color_analysis.json"
OBJECT_DETECTION_CACHE = CACHE_DIR / "object_detection.json"
LYRICS_CACHE = CACHE_DIR / "lyrics_analysis.json"
AUDIO_FEATURES_CACHE = CACHE_DIR / "audio_features.json"

# Create album image directory if it doesn't exist
ALBUM_IMAGES_DIR.mkdir(exist_ok=True)

# Default scopes and settings
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# Add this import at the top
import numpy as np

# Expanded color categories mapping with more nuanced colors
COLOR_CATEGORIES = {
    # Reds
    "red": "Red", "darkred": "Red", "firebrick": "Red", "crimson": "Red", "indianred": "Red",
    "maroon": "Red", "tomato": "Red", "salmon": "Red", "darksalmon": "Red", "lightcoral": "Red",
    
    # Blues
    "blue": "Blue", "darkblue": "Blue", "royalblue": "Blue", "navy": "Blue", "dodgerblue": "Blue",
    "steelblue": "Blue", "deepskyblue": "Blue", "cornflowerblue": "Blue", "cadetblue": "Blue", 
    "lightblue": "Blue", "powderblue": "Blue", "skyblue": "Blue", "lightskyblue": "Blue",
    
    # Greens
    "green": "Green", "darkgreen": "Green", "forestgreen": "Green", "limegreen": "Green",
    "seagreen": "Green", "mediumseagreen": "Green", "springgreen": "Green", "mediumspringgreen": "Green",
    "olive": "Green", "olivedrab": "Green", "darkolivegreen": "Green", "yellowgreen": "Green",
    "lawngreen": "Green", "chartreuse": "Green", "greenyellow": "Green", "lime": "Green",
    "mediumaquamarine": "Green", "aquamarine": "Green", "palegreen": "Green", "lightgreen": "Green",
    "darkseagreen": "Green", "teal": "Green", "darkcyan": "Green",
    
    # Yellows
    "yellow": "Yellow", "gold": "Yellow", "khaki": "Yellow", "lightyellow": "Yellow",
    "lemonchiffon": "Yellow", "lightgoldenrodyellow": "Yellow", "papayawhip": "Yellow",
    "moccasin": "Yellow", "palegoldenrod": "Yellow", "darkkhaki": "Yellow",
    
    # Purples
    "purple": "Purple", "darkviolet": "Purple", "indigo": "Purple", "blueviolet": "Purple",
    "darkorchid": "Purple", "darkmagenta": "Purple", "fuchsia": "Purple", "magenta": "Purple",
    "orchid": "Purple", "mediumorchid": "Purple", "mediumpurple": "Purple", "plum": "Purple",
    "violet": "Purple", "thistle": "Purple", "lavender": "Purple", "rebeccapurple": "Purple",
    
    # Oranges
    "orange": "Orange", "darkorange": "Orange", "coral": "Orange", "peachpuff": "Orange", 
    "bisque": "Orange", "navajowhite": "Orange", "wheat": "Orange", "burlywood": "Orange",
    "tan": "Orange", "sandybrown": "Orange", "goldenrod": "Orange", "peru": "Orange",
    "darkgoldenrod": "Orange", "chocolate": "Orange", "sienna": "Orange", "orangered": "Orange",
    
    # Pinks
    "pink": "Pink", "hotpink": "Pink", "deeppink": "Pink", "lightpink": "Pink",
    "palevioletred": "Pink", "mediumvioletred": "Pink", "lavenderblush": "Pink",
    "mistyrose": "Pink", "rosybrown": "Pink",
    
    # Browns
    "brown": "Brown", "saddlebrown": "Brown", "sienna": "Brown", "chocolate": "Brown", 
    "peru": "Brown", "darkgoldenrod": "Brown", "rosybrown": "Brown", "maroon": "Brown",
    "burywood": "Brown", "tan": "Brown", "sandybrown": "Brown",
    
    # Turquoise/Cyan
    "turquoise": "Turquoise", "mediumturquoise": "Turquoise", "darkturquoise": "Turquoise",
    "aqua": "Turquoise", "cyan": "Turquoise", "lightcyan": "Turquoise", "paleturquoise": "Turquoise",
    "aquamarine": "Turquoise", "mediumaquamarine": "Turquoise",
    
    # Grays, blacks, whites
    "black": "Black", "darkgray": "Gray", "gray": "Gray", "dimgray": "Gray", "lightgray": "Gray",
    "lightslategray": "Gray", "slategray": "Gray", "silver": "Gray", 
    "white": "White", "snow": "White", "honeydew": "White", "mintcream": "White", 
    "azure": "White", "aliceblue": "White", "ghostwhite": "White", "whitesmoke": "White",
    "seashell": "White", "beige": "White", "oldlace": "White", "floralwhite": "White",
    "ivory": "White", "antiquewhite": "White", "linen": "White", "lavenderblush": "White",
    "mistyrose": "White"
}

# Mood color mappings
MOOD_COLORS = {
    "energetic": ["Red", "Orange", "Yellow"],
    "calm": ["Blue", "Turquoise", "Purple"],
    "happy": ["Yellow", "Orange", "Pink"],
    "melancholic": ["Purple", "Blue", "Gray"],
    "focused": ["Green", "Blue", "Gray"]
}

# Time of day color palettes
TIME_OF_DAY_PALETTES = {
    "sunrise": [(255, 200, 100), (255, 150, 50), (200, 100, 0)],  # Oranges and yellows
    "midday": [(100, 200, 255), (50, 150, 255), (0, 100, 200)],   # Blues 
    "sunset": [(255, 100, 100), (200, 50, 100), (150, 0, 100)],   # Reds and purples
    "night": [(50, 50, 100), (20, 20, 80), (0, 0, 50)]            # Dark blues
}

# Complementary color pairs for contrast playlists
CONTRAST_PAIRS = [
    ("Red", "Green"),
    ("Blue", "Orange"),
    ("Yellow", "Purple"),
    ("Black", "White")
]

# Genius API for lyrics (you'll need to sign up at https://genius.com/api-clients)
GENIUS_API_TOKEN = "YOUR_GENIUS_API_TOKEN"  # Replace with your actual token

# Object detection settings
OBJECT_DETECTION_CONFIDENCE = 0.4  # Minimum confidence for object detection
OBJECT_MIN_TRACKS = 3  # Minimum number of tracks to create an object-based playlist