"""Functions for creating time-of-day based playlists."""

import questionary
from tqdm import tqdm
from spotify_playlist_creator import config
from spotify_playlist_creator.analysis import color_analysis
import datetime

# Define time periods with their display names, time ranges, and moods
TIME_PERIODS = {
    "sunrise": {
        "display": "Sunrise (5-8 AM)",
        "time_range": (5, 8),
        "colors": [(255, 200, 100), (255, 150, 50), (200, 100, 0)],  # Oranges and yellows
        "description": "Calm, peaceful music for the early morning",
        "mood_keywords": ["calm", "peaceful", "acoustic", "soft", "ambient"]
    },
    "morning": {
        "display": "Morning (8-11 AM)",
        "time_range": (8, 11),
        "colors": [(200, 220, 255), (150, 200, 250), (100, 180, 250)],  # Light blues
        "description": "Upbeat, energizing tracks to start your day",
        "mood_keywords": ["upbeat", "motivational", "bright", "energetic"]
    },
    "midday": {
        "display": "Midday (11 AM-2 PM)",
        "time_range": (11, 14),
        "colors": [(100, 200, 255), (50, 150, 255), (0, 100, 200)],  # Blues
        "description": "Productive, focused music for the middle of the day",
        "mood_keywords": ["focus", "instrumental", "work", "productivity"]
    },
    "afternoon": {
        "display": "Afternoon (2-5 PM)",
        "time_range": (14, 17),
        "colors": [(200, 200, 100), (220, 180, 50), (240, 160, 0)],  # Yellows
        "description": "Relaxed but upbeat music for the afternoon",
        "mood_keywords": ["relaxed", "upbeat", "chill", "laid-back"]
    },
    "sunset": {
        "display": "Sunset (5-8 PM)",
        "time_range": (17, 20),
        "colors": [(255, 100, 100), (200, 50, 100), (150, 0, 100)],  # Reds and purples
        "description": "Relaxing, warm music for the evening",
        "mood_keywords": ["relaxing", "warm", "melodic", "soothing"]
    },
    "night": {
        "display": "Night (8-11 PM)",
        "time_range": (20, 23),
        "colors": [(50, 50, 100), (20, 20, 80), (0, 0, 50)],  # Dark blues
        "description": "Atmospheric, moody tracks for the night",
        "mood_keywords": ["atmospheric", "moody", "dark", "deep"]
    },
    "late_night": {
        "display": "Late Night (11 PM-5 AM)",
        "time_range": (23, 5),
        "colors": [(20, 0, 40), (40, 0, 60), (60, 0, 80)],  # Deep purples
        "description": "Ambient, dreamy music for late night hours",
        "mood_keywords": ["ambient", "dreamy", "sleep", "chill", "electronic"]
    }
}

def create_time_of_day_playlist(sp, tracks, analysis_results, time_key, playlist_type="mood", prefix="", public=True, max_tracks=50):
    """
    Create a playlist based on time of day.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries
        analysis_results: Dictionary of analysis results
        time_key: Key of the time period (e.g., "sunrise", "night")
        playlist_type: "release_time" or "mood" to determine how to select tracks
        prefix: Optional prefix for playlist name
        public: Whether the playlist should be public
        max_tracks: Maximum number of tracks to include in the playlist
        
    Returns:
        Created playlist information or None if canceled
    """
    # Get time period data
    time_period = TIME_PERIODS.get(time_key)
    if not time_period:
        print(f"Unknown time period: {time_key}")
        return None
    
    # Determine playlist name and description
    base_name = time_period["display"].split(" ")[0]  # Just get "Sunrise", "Night", etc.
    
    if playlist_type == "release_time":
        playlist_name = f"{prefix}{base_name} Time Releases"
        description = f"Songs released during {time_period['display']}. Created by Spotify Color Playlist Creator."
        all_selected_tracks = select_tracks_by_release_time(tracks, time_period["time_range"])
    else:  # mood-based
        playlist_name = f"{prefix}{base_name} Vibes"
        description = f"{time_period['description']}. Created by Spotify Color Playlist Creator."
        all_selected_tracks = select_tracks_by_mood(tracks, analysis_results, time_period)
    
    if not all_selected_tracks:
        print(f"No suitable tracks found for {time_period['display']} {playlist_type} playlist.")
        return None
    
    # Limit to the specified maximum number of tracks
    selected_tracks = all_selected_tracks[:max_tracks]
    
    # Preview the selected tracks and confirm with user
    confirmed = preview_and_confirm_tracks(selected_tracks, time_period["display"], playlist_type)
    if not confirmed:
        return None
    
    # Create the playlist
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=public,
        description=description
    )
    
    # Add tracks to the playlist
    track_uris = [track['uri'] for track in selected_tracks]
    
    # Add tracks in batches of 100 (Spotify API limit)
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i+100]
        sp.playlist_add_items(playlist['id'], batch)
    
    print(f"Created playlist: {playlist_name} with {len(selected_tracks)} tracks")
    
    # Return playlist info
    return {
        'id': playlist['id'],
        'name': playlist_name,
        'time_period': time_key,
        'track_count': len(selected_tracks)
    }

def preview_and_confirm_tracks(tracks, time_display, playlist_type):
    """
    Preview tracks and ask for user confirmation.
    
    Args:
        tracks: List of selected track dictionaries
        time_display: Display name of time period
        playlist_type: Type of playlist (release_time or mood)
        
    Returns:
        Boolean indicating whether user confirmed the selection
    """
    print(f"\n🎵 Preview of tracks for {time_display} ({playlist_type} based):")
    print(f"Total tracks selected: {len(tracks)}")
    print("-" * 70)
    
    # Display a sample of tracks (first 10)
    display_count = min(10, len(tracks))
    for i, track in enumerate(tracks[:display_count]):
        artist = track.get('artist', 'Unknown Artist')
        name = track.get('name', 'Unknown Track')
        
        # If this is a release_time playlist, show the release time
        if playlist_type == "release_time" and 'added_at' in track:
            # Convert ISO format to datetime and extract hour
            try:
                added_time = datetime.datetime.fromisoformat(track['added_at'].replace('Z', '+00:00'))
                time_str = f"{added_time.hour:02d}:{added_time.minute:02d}"
                print(f"{i+1}. {artist} - {name} [{time_str}]")
            except Exception:
                print(f"{i+1}. {artist} - {name}")
        else:
            print(f"{i+1}. {artist} - {name}")
    
    if len(tracks) > display_count:
        print(f"... and {len(tracks) - display_count} more tracks")
    
    print("-" * 70)
    
    # Ask for confirmation
    confirm = questionary.select(
        "Would you like to proceed with these tracks?",
        choices=[
            "Yes, create playlist with these tracks",
            "Show me more tracks from the selection",
            "No, resample tracks",
            "Cancel"
        ]
    ).ask()
    
    if confirm == "Yes, create playlist with these tracks":
        return True
    elif confirm == "Show me more tracks from the selection":
        # Show more tracks and ask again
        print("\nMore tracks from the selection:")
        for i, track in enumerate(tracks[display_count:display_count*2]):
            artist = track.get('artist', 'Unknown Artist')
            name = track.get('name', 'Unknown Track')
            print(f"{i+display_count+1}. {artist} - {name}")
        
        if len(tracks) > display_count*2:
            print(f"... and {len(tracks) - display_count*2} more tracks")
        
        # Recursive call to confirm again
        return preview_and_confirm_tracks(tracks, time_display, playlist_type)
    elif confirm == "No, resample tracks":
        # Signal to the caller that we want to resample
        return False
    else:  # Cancel
        return False

def select_tracks_by_release_time(tracks, time_range):
    """
    Select tracks that were released during a specific time range.
    
    Args:
        tracks: List of track dictionaries
        time_range: Tuple of (start_hour, end_hour)
        
    Returns:
        List of tracks matching the time range
    """
    selected_tracks = []
    start_hour, end_hour = time_range
    
    # First check if we have any tracks with the needed time data
    has_time_data = False
    for track in tracks[:10]:  # Check first few tracks
        if 'added_at' in track:
            has_time_data = True
            break
    
    if not has_time_data:
        print("\n⚠️ IMPORTANT: Your track data does not include 'added_at' timestamps.")
        print("This is required for time-of-day playlists based on release time.")
        print("Try using the 'mood' option instead, or fetch fresh data from Spotify.")
        
        # Emergency fallback: just select some random tracks for the time period
        import random
        return random.sample(tracks, min(30, len(tracks)))
    
    for track in tracks:
        # Skip tracks without timestamp data
        if 'added_at' not in track:
            continue
            
        try:
            # Parse the ISO timestamp
            added_time = datetime.datetime.fromisoformat(track['added_at'].replace('Z', '+00:00'))
            hour = added_time.hour
            
            # Handle wraparound for late_night (e.g., 23-5)
            if start_hour > end_hour:  # Crosses midnight
                if hour >= start_hour or hour < end_hour:
                    selected_tracks.append(track)
            else:  # Normal time range
                if start_hour <= hour < end_hour:
                    selected_tracks.append(track)
                    
        except Exception as e:
            # Skip tracks with invalid timestamps
            continue
    
    # If we don't have enough tracks, provide a fallback
    if len(selected_tracks) < 5:
        print(f"\n⚠️ Only found {len(selected_tracks)} tracks for the {start_hour}-{end_hour} time range.")
        print("Selecting some additional tracks by mood instead.")
        
        # Add some mood-based tracks as fallback
        import random
        extra_tracks = random.sample([t for t in tracks if t not in selected_tracks], 
                                     min(25, len(tracks) - len(selected_tracks)))
        selected_tracks.extend(extra_tracks)
    
    # Shuffle the results for variety
    import random
    random.shuffle(selected_tracks)
    
    return selected_tracks

def select_tracks_by_mood(tracks, analysis_results, time_period):
    """
    Select tracks that match the mood for a specific time of day.
    
    Args:
        tracks: List of track dictionaries
        analysis_results: Dictionary of analysis results
        time_period: Dictionary with time period data
        
    Returns:
        List of tracks that match the mood
    """
    # Get color analysis if available
    color_data = analysis_results.get('color', {})
    
    # Prepare result list
    selected_tracks = []
    
    # Target colors for this time period
    target_colors = time_period.get("colors", [])
    
    # Score each track based on how well it matches the time of day mood
    track_scores = []
    
    for track in tracks:
        track_id = track['id']
        score = 0
        
        # Use color analysis to score tracks
        if track_id in color_data:
            color_info = color_data[track_id]
            
            # Score based on dominant color similarity to target colors
            if 'dominant_color' in color_info:
                dominant_color = color_info['dominant_color']
                
                # Calculate color similarity to target colors
                for target in target_colors:
                    similarity = color_similarity(dominant_color, target)
                    score += similarity * 5  # Weight for color similarity
            
            # Also consider the overall brightness/darkness
            if 'average_hsv' in color_info:
                hsv = color_info['average_hsv']
                
                # For morning/day: prefer brighter tracks
                if time_period['time_range'][0] >= 5 and time_period['time_range'][1] <= 17:
                    score += hsv[2] * 3  # Brightness boost for daytime
                # For evening/night: prefer darker tracks
                else:
                    score += (1 - hsv[2]) * 3  # Darkness boost for nighttime
        
        # We could also use audio features if available
        # (Would need to fetch these from Spotify API)
        
        track_scores.append((track, score))
    
    # Sort tracks by score (highest first)
    track_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Select top ~50 tracks (or fewer if not enough)
    top_count = min(50, len(track_scores))
    selected_tracks = [item[0] for item in track_scores[:top_count]]
    
    return selected_tracks

def color_similarity(color1, color2):
    """Calculate a simple similarity score between two RGB colors."""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    
    # Calculate Euclidean distance in RGB space
    distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
    
    # Convert to similarity (closer = higher similarity)
    max_distance = 441.7  # Max possible distance in RGB space
    similarity = 1 - (distance / max_distance)
    
    return similarity

def get_time_period_choices():
    """Get formatted choices for time periods."""
    choices = []
    for key, data in TIME_PERIODS.items():
        choices.append(data["display"])
    return choices

def get_time_key_from_display(display_name):
    """Convert a display name back to its key."""
    for key, data in TIME_PERIODS.items():
        if data["display"] == display_name:
            return key
    return None

def debug_track_data(tracks, count=3):
    """
    Debug function to inspect track data structure.
    
    Args:
        tracks: List of track dictionaries
        count: Number of tracks to inspect
    """
    print("\n🔍 DEBUG: Examining track data structure")
    print("-" * 70)
    
    sample_tracks = tracks[:count]
    for i, track in enumerate(sample_tracks):
        print(f"Track {i+1}:")
        
        # Essential fields for time-of-day playlists
        print(f"  ID: {track.get('id', 'Not available')}")
        print(f"  Name: {track.get('name', 'Not available')}")
        print(f"  Artist: {track.get('artist', 'Not available')}")
        
        # Time-related fields
        print("  Time fields:")
        if 'added_at' in track:
            print(f"    added_at: {track['added_at']}")
        else:
            print("    added_at: Not available")
            
        # Check for alternate time fields that might be available
        for key in ['timestamp', 'date_added', 'release_date']:
            if key in track:
                print(f"    {key}: {track[key]}")
                
        # Check if track has album info with dates
        if 'album' in track and isinstance(track['album'], dict):
            if 'release_date' in track['album']:
                print(f"    album.release_date: {track['album']['release_date']}")
        
        print("-" * 70)

def create_time_of_day_playlists(sp, tracks, analysis_results):
    """Interactive function to create time-of-day based playlists."""
    print("\n🕒 Creating Time-of-Day Playlist")
    
    # Debug the track data to understand what we're working with
    debug_track_data(tracks)
    
    # Get time period choices with their display names
    time_choices = get_time_period_choices()
    time_choices.append("Cancel")
    
    # Let user select a time period
    selected_time = questionary.select(
        "Which time of day playlist would you like to create?",
        choices=time_choices
    ).ask()
    
    if selected_time == "Cancel":
        return []
    
    # Get the time key from the display name
    time_key = get_time_key_from_display(selected_time)
    
    # Let user choose between release time or mood-based playlist
    playlist_type = questionary.select(
        "What kind of time-of-day playlist would you like?",
        choices=[
            "Songs that match the mood for this time of day",
            "Songs released during this time frame",
            "Cancel"
        ]
    ).ask()
    
    if playlist_type == "Cancel":
        return []
    
    # Convert selection to type
    if playlist_type == "Songs released during this time frame":
        playlist_type = "release_time"
    else:
        playlist_type = "mood"
    
    # Ask for maximum number of tracks
    max_tracks_input = questionary.text(
        "Maximum number of tracks in playlist?",
        default="50"
    ).ask()
    
    try:
        max_tracks = int(max_tracks_input)
        if max_tracks <= 0:
            print("Invalid number, using default of 50 tracks")
            max_tracks = 50
    except ValueError:
        print("Invalid input, using default of 50 tracks")
        max_tracks = 50
    
    # Create the playlist with resampling loop
    while True:
        created_playlist = create_time_of_day_playlist(
            sp, 
            tracks, 
            analysis_results,
            time_key,
            playlist_type,
            max_tracks=max_tracks
        )
        
        if created_playlist:
            return [created_playlist]
        else:
            # Ask if user wants to try again with same settings
            retry = questionary.select(
                "Would you like to try again?",
                choices=[
                    "Yes, resample tracks",
                    "No, cancel playlist creation"
                ]
            ).ask()
            
            if retry != "Yes, resample tracks":
                return []
