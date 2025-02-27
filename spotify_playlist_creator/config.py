"""Configuration settings for the Spotify Color Playlist Creator."""

# Add this import at the top
import numpy as np

# Spotify API credentials
CLIENT_ID = "7d31698de0874df9ab08249f3c046561"
CLIENT_SECRET = "20bb675d81d64cd3a771b75daed51012"
REDIRECT_URI = "http://localhost:8080"


# Genius API token
GENIUS_CLIENT_ID = "H3U6-zi6eFF7AAw3YqlyLeY1buTNdrqkzSCGrnC4qMNARvUI4crwGlKDUinEgUwl"
GENIUS_CLIENT_SECRET = "AdL3gQPv3uANsFGJrv9RAvTP8QsArnsocEgwnp8jQwbP0O_eZ0FU75-fTgKbDNr23yRjJ5dvdbAA5fYlQQn2lw"
GENIUS_CLIENT_ACCESS_TOKEN = "nna9HdUF2PsSKXNPkfaU0ubzscXtsDM0OIO7gEriYqvpX1V64eOALC8OR7qoPAMN"
# Scopes required for accessing user data and creating playlists
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

# Cache file names
LIKED_SONGS_CACHE = "liked_songs_cache.json"
COLOR_ANALYSIS_CACHE = "color_analysis_cache.json"

# Default settings
DEFAULT_CACHE_EXPIRY_HOURS = 24
DEFAULT_IMAGE_TIMEOUT = 10
DEFAULT_API_TIMEOUT = 20
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 3

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

# Cache file paths
OBJECT_DETECTION_CACHE = "object_detection_cache.json"
LYRICS_CACHE = "lyrics_cache.json"

# Genius API for lyrics (you'll need to sign up at https://genius.com/api-clients)
GENIUS_API_TOKEN = "YOUR_GENIUS_API_TOKEN"  # Replace with your actual token

# Object detection settings
OBJECT_DETECTION_CONFIDENCE = 0.4  # Minimum confidence for object detection
OBJECT_MIN_TRACKS = 3  # Minimum number of tracks to create an object-based playlist