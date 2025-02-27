"""Functions for creating lyrics-based playlists."""

from tqdm import tqdm

from spotify_playlist_creator.analysis import lyrics_analysis

def create_mood_playlists(sp, tracks, lyrics_analysis_results, prefix="Mood - ", public=True):
    """
    Create playlists based on lyrical mood analysis.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries
        lyrics_analysis_results: Dictionary mapping track IDs to lyrics analysis
        prefix: Prefix for playlist names
        public: Whether playlists should be public
        
    Returns:
        List of created playlist information
    """
    print("Creating mood-based playlists from lyrics...")
    
    # Group tracks by mood
    mood_groups = lyrics_analysis.group_tracks_by_mood(tracks, lyrics_analysis_results)
    
    # Get current user ID
    user_id = sp.me()['id']
    
    created_playlists = []
    
    # Create description templates for each mood
    mood_descriptions = {
        'happy': "Songs with upbeat, positive lyrics.",
        'sad': "Songs with melancholic, sad lyrics.",
        'angry': "Songs with intense, angry lyrics.",
        'neutral': "Songs with balanced, neutral lyrics.",
        'love': "Songs about love and relationships.",
        'explicit': "Songs with explicit content in lyrics."
    }
    
    # Create a playlist for each mood
    for mood, mood_tracks in tqdm(mood_groups.items(), desc="Creating mood playlists"):
        if len(mood_tracks) < 5:  # Skip if too few tracks
            continue
            
        playlist_name = f"{prefix}{mood.title()}"
        description = mood_descriptions.get(mood, "Songs grouped by lyrical mood")
        description += " Created by Spotify Color Playlist Creator."
        
        # Create the playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        
        # Add tracks to the playlist
        track_uris = [track['uri'] for track in mood_tracks]
        
        # Add tracks in batches of 100 (Spotify API limit)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.playlist_add_items(playlist['id'], batch)
        
        # Store playlist info
        created_playlists.append({
            'id': playlist['id'],
            'name': playlist_name,
            'mood': mood,
            'track_count': len(mood_tracks)
        })
        
        print(f"Created playlist: {playlist_name} with {len(mood_tracks)} tracks")
    
    return created_playlists 