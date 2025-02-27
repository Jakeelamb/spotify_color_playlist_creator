"""Functions for fetching data from Spotify API."""

import time
import requests
from tqdm import tqdm
from datetime import datetime
import os

from spotify_playlist_creator import config
from spotify_playlist_creator.utils import caching

def get_user_liked_songs(sp, limit=50, use_cache=True, cache_file=None, max_retries=None, retry_delay=None):
    """Retrieve user's saved/liked tracks with caching support and retry mechanism."""
    if cache_file is None:
        cache_file = config.LIKED_SONGS_CACHE
    if max_retries is None:
        max_retries = config.DEFAULT_MAX_RETRIES
    if retry_delay is None:
        retry_delay = config.DEFAULT_RETRY_DELAY
    
    # Check if cache exists and is recent (less than 24 hours old)
    if use_cache and caching.is_cache_valid(cache_file):
        cache_data = caching.load_cache(cache_file)
        if cache_data and 'tracks' in cache_data:
            print(f"Using cached liked songs from {cache_data.get('timestamp', 'unknown date')}")
            return cache_data['tracks']
        else:
            print("Cache exists but is invalid. Fetching fresh data...")
    
    print("Fetching your liked songs from Spotify...")
    
    tracks = []
    offset = 0
    
    # Get initial results to determine total
    initial_results = None
    for attempt in range(max_retries):
        try:
            initial_results = sp.current_user_saved_tracks(limit=1, offset=0)
            break
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout occurred. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("Maximum retries reached. Using partial data or try again later.")
                if os.path.exists(cache_file):
                    print("Falling back to cached data...")
                    cache_data = caching.load_cache(cache_file)
                    if cache_data and 'tracks' in cache_data:
                        return cache_data['tracks']
                return tracks
    
    if not initial_results:
        print("Could not connect to Spotify API. Please try again later.")
        return tracks
        
    total_tracks = initial_results['total']
    
    # Create progress bar
    pbar = tqdm(total=total_tracks, desc="Fetching tracks", unit="track")
    
    # Paginate through all liked songs
    while True:
        # Try to fetch with retries
        results = None
        for attempt in range(max_retries):
            try:
                results = sp.current_user_saved_tracks(limit=limit, offset=offset)
                break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"\nTimeout occurred. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print("\nMaximum retries reached. Using partial data.")
                    # Save partial data to cache before exiting
                    if use_cache and tracks:
                        cache_data = {
                            'tracks': tracks,
                            'partial': True
                        }
                        caching.save_cache(cache_data, cache_file)
                        print(f"Saved {len(tracks)} tracks to cache (partial data)")
                    return tracks
        
        if not results or not results['items']:
            break
            
        for item in results['items']:
            track = item['track']
            # Store relevant track info
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'uri': track['uri'],
                'album_name': track['album']['name'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
            tracks.append(track_info)
        
        fetched = len(results['items'])
        pbar.update(fetched)
        offset += limit
        
        # Respect rate limits but don't wait too long
        time.sleep(0.1)
    
    pbar.close()
    print(f"Total tracks fetched: {len(tracks)}")
    
    # Save to cache
    if use_cache:
        cache_data = {'tracks': tracks}
        caching.save_cache(cache_data, cache_file)
        print(f"Saved {len(tracks)} tracks to cache")
    
    # After getting all tracks, fetch audio features
    audio_features = get_audio_features(sp, tracks)
    
    # Enrich track data with audio features
    for track in tracks:
        if track['id'] in audio_features:
            track['audio_features'] = audio_features[track['id']]
    
    return tracks

def get_playlist_tracks(sp, playlist_id, limit=100, use_cache=True):
    """Fetch tracks from a specific playlist."""
    cache_file = f"playlist_{playlist_id}_cache.json"
    
    if use_cache and caching.is_cache_valid(cache_file):
        cache_data = caching.load_cache(cache_file)
        if cache_data and 'tracks' in cache_data:
            print(f"Using cached playlist tracks from {cache_data.get('timestamp', 'unknown date')}")
            return cache_data['tracks']
    
    print(f"Fetching tracks from playlist {playlist_id}...")
    
    tracks = []
    offset = 0
    
    while True:
        results = sp.playlist_tracks(
            playlist_id=playlist_id,
            limit=limit,
            offset=offset
        )
        
        if not results['items']:
            break
            
        for item in results['items']:
            if not item['track']:
                continue
                
            track = item['track']
            track_info = {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'uri': track['uri'],
                'album_name': track['album']['name'],
                'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
            tracks.append(track_info)
        
        offset += limit
        
        if offset >= results['total']:
            break
    
    print(f"Fetched {len(tracks)} tracks from playlist")
    
    # Save to cache
    if use_cache:
        cache_data = {'tracks': tracks}
        caching.save_cache(cache_data, cache_file)
    
    # After getting all tracks, fetch audio features
    audio_features = get_audio_features(sp, tracks)
    
    # Enrich track data with audio features
    for track in tracks:
        if track['id'] in audio_features:
            track['audio_features'] = audio_features[track['id']]
    
    return tracks

def get_user_info(sp):
    """Get information about the current user."""
    return sp.me()

def get_audio_features(sp, tracks):
    """Fetch audio features for tracks from Spotify API.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries with 'id' field
        
    Returns:
        Dictionary mapping track IDs to audio features
    """
    print("Fetching audio features for tracks...")
    audio_features = {}
    
    # Process in batches of 100 (Spotify API limit)
    for i in range(0, len(tracks), 100):
        batch = tracks[i:i+100]
        track_ids = [track['id'] for track in batch]
        
        # Remove None or empty IDs
        track_ids = [tid for tid in track_ids if tid]
        
        if not track_ids:
            continue
            
        try:
            results = sp.audio_features(track_ids)
            
            # Map results to track IDs
            for j, features in enumerate(results):
                if features:  # Some tracks might not have features
                    audio_features[track_ids[j]] = features
                    
        except Exception as e:
            print(f"Error fetching audio features: {e}")
    
    print(f"Retrieved audio features for {len(audio_features)} tracks")
    return audio_features
