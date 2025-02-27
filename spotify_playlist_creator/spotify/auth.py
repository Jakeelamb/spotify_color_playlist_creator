"""Functions for Spotify authentication."""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotify_playlist_creator import config

def authenticate_spotify():
    """Authenticate with Spotify API and return authenticated client."""
    print("Authenticating with Spotify...")
    
    # Set up authentication manager
    auth_manager = SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope=config.SCOPE,
        open_browser=True
    )
    
    # Create Spotify client
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Verify connection by getting current user
    user = sp.me()
    print(f"Authenticated as: {user['display_name']} ({user['id']})")
    
    return sp
