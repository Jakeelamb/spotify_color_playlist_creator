# Spotify Playlist Creator

A powerful Python application that creates intelligent, customized Spotify playlists based on various attributes of your music including:

- Album artwork colors
- Audio features (energy, danceability, tempo, etc.)
- Time of day characteristics
- Objects detected in album artwork
- Lyrical themes and sentiment

## Installation

### Basic Installation
bash
pip install spotify-playlist-creator

### Full Installation (with all features)

pip install 'spotify-playlist-creator[all]'


### Feature-specific Installation


pip install 'spotify-playlist-creator[object_detection]'


pip install 'spotify-playlist-creator[lyrics]'

## Configuration

Before using the application, you need to set up your API credentials.

1. Create a file named `config_local.py` in the `spotify_playlist_creator` directory with the following content:
```python
"""Local configuration file for storing sensitive credentials.
This file should not be committed to version control."""

# Spotify API credentials
CLIENT_ID = "your_spotify_client_id"
CLIENT_SECRET = "your_spotify_client_secret"
REDIRECT_URI = "http://localhost:8080"

# Genius API credentials (optional - for lyrics features)
GENIUS_CLIENT_ID = ""
GENIUS_CLIENT_SECRET = ""
GENIUS_CLIENT_ACCESS_TOKEN = ""
```

2. Get your Spotify API credentials:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create a new application
   - Set the redirect URI to `http://localhost:8080`
   - Copy your Client ID and Client Secret

3. (Optional) For lyrics analysis, get your Genius API token:
   - Go to [Genius API Clients](https://genius.com/api-clients)
   - Create a new API client
   - Copy your Client ID, Client Secret, and Access Token

## Usage

Run the application with:

```bash
spotify-playlists
```

This will launch an interactive CLI that guides you through:
1. Authenticating with Spotify
2. Selecting your music source (liked songs, playlist, etc.)
3. Choosing what type of playlists to create
4. Customizing playlist options

## Features

### Color-based Playlists
Creates playlists based on the dominant colors in album artwork, with customized playlist covers.

### Audio Feature Playlists
Groups songs by audio characteristics like:
- Energy (high, medium, low)
- Danceability
- Acousticness
- Tempo
- Valence (musical positivity)
- And more!

### Time-of-day Playlists
Creates playlists optimized for different times of day:
- Sunrise (5-8 AM)
- Morning (8-11 AM)
- Afternoon (11 AM-2 PM)
- Evening (5-8 PM)
- Night (8-11 PM)
- Late Night (11 PM-5 AM)

### Object-based Playlists (requires extra dependencies)
Detects objects in album artwork and creates themed playlists.

### Lyrics-based Playlists (requires extra dependencies)
Analyzes song lyrics to create mood-based playlists:
- Happy
- Sad
- Angry
- Neutral

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.