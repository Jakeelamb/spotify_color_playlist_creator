"""Functions for creating playlists based on audio features."""

import questionary
from tqdm import tqdm
from spotify_playlist_creator.analysis import audio_features

# Friendly names and descriptions for audio features
FEATURE_INFO = {
    'energy': {
        'name': 'Energy',
        'description': 'How energetic, intense, and active the music is',
        'categories': ['low', 'medium', 'high']
    },
    'danceability': {
        'name': 'Danceability',
        'description': 'How suitable the track is for dancing',
        'categories': ['low', 'medium', 'high']
    },
    'valence': {
        'name': 'Mood',
        'description': 'Musical positiveness conveyed by a track',
        'categories': ['sad', 'neutral', 'happy']
    },
    'acousticness': {
        'name': 'Acousticness',
        'description': 'How acoustic (vs. electronic) the track is',
        'categories': ['low', 'medium', 'high']
    },
    'tempo': {
        'name': 'Tempo',
        'description': 'Beats per minute (BPM)',
        'categories': ['slow', 'medium', 'fast', 'very_fast']
    },
    'key': {
        'name': 'Musical Key',
        'description': 'The key the track is in (C, C#, etc.)',
        'categories': ['C', 'C♯/D♭', 'D', 'D♯/E♭', 'E', 'F', 'F♯/G♭', 'G', 'G♯/A♭', 'A', 'A♯/B♭', 'B']
    },
    'mode': {
        'name': 'Mode',
        'description': 'Modality (major or minor) of the track',
        'categories': ['Minor', 'Major']
    },
    'instrumentalness': {
        'name': 'Instrumentalness',
        'description': 'Whether a track has vocals',
        'categories': ['vocal', 'mixed', 'instrumental']
    },
    'liveness': {
        'name': 'Liveness',
        'description': 'Presence of audience in the recording',
        'categories': ['studio', 'live']
    },
    'speechiness': {
        'name': 'Speechiness',
        'description': 'Presence of spoken words',
        'categories': ['music', 'music_and_speech', 'speech']
    },
    'loudness': {
        'name': 'Loudness',
        'description': 'Overall loudness in decibels',
        'categories': ['quiet', 'medium', 'loud']
    },
    'time_signature': {
        'name': 'Time Signature',
        'description': 'Time signature of the track',
        'categories': ['3/4', '4/4', '5/4', '6/8', 'Other']
    }
}

def create_feature_based_playlist(sp, tracks, feature, category, prefix="", public=True):
    """
    Create a playlist based on a specific audio feature category.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries with audio_features
        feature: Feature to categorize by (e.g., 'energy')
        category: Specific category to create playlist for (e.g., 'high')
        prefix: Prefix for playlist name
        public: Whether playlist should be public
        
    Returns:
        Created playlist information
    """
    # Get feature display name
    feature_name = FEATURE_INFO.get(feature, {}).get('name', feature.title())
    
    # Categorize tracks
    categories = audio_features.categorize_tracks_by_feature(tracks, feature)
    
    if category not in categories or not categories[category]:
        print(f"No tracks found in category '{category}' for feature '{feature_name}'")
        return None
    
    selected_tracks = categories[category]
    
    # Create playlist name and description
    playlist_name = f"{prefix}{feature_name}: {category.title()}"
    description = f"Songs with {category} {feature_name.lower()}. Created by Spotify Playlist Creator."
    
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
        'feature': feature,
        'category': category,
        'track_count': len(selected_tracks)
    }

def create_audio_feature_playlists(sp, tracks):
    """Interactive function to create audio feature based playlists."""
    print("\n🎵 Creating Audio Feature Playlist")
    
    # Check if tracks have audio features
    has_features = False
    for track in tracks[:10]:  # Check first few tracks
        if 'audio_features' in track and track['audio_features']:
            has_features = True
            break
    
    if not has_features:
        print("⚠️ Tracks don't have audio features. Fetching them now...")
        from spotify_playlist_creator.spotify.scraper import get_audio_features
        
        # Fetch audio features
        audio_feature_data = get_audio_features(sp, tracks)
        
        # Enrich track data
        for track in tracks:
            if track['id'] in audio_feature_data:
                track['audio_features'] = audio_feature_data[track['id']]
    
    # Summarize audio features to show the user
    summary = audio_features.summarize_audio_features(tracks)
    
    print(f"\n📊 Audio Features Summary (from {summary['count']} tracks):")
    print("-" * 70)
    print(f"Average Energy: {summary['averages'].get('energy', 0):.2f} (0=calm, 1=intense)")
    print(f"Average Danceability: {summary['averages'].get('danceability', 0):.2f} (0=least, 1=most)")
    print(f"Average Valence (mood): {summary['averages'].get('valence', 0):.2f} (0=negative, 1=positive)")
    print(f"Average Tempo: {summary['averages'].get('tempo', 0):.0f} BPM")
    print("-" * 70)
    
    # 1. Let user choose between standard feature or custom category
    playlist_type = questionary.select(
        "What type of audio feature playlist would you like to create?",
        choices=[
            "Based on a single feature (energy, danceability, etc.)",
            "Based on a custom category (workout, chill, party, etc.)",
            "Cancel"
        ]
    ).ask()
    
    if playlist_type == "Cancel":
        return []
    
    # 2. For single feature
    if playlist_type.startswith("Based on a single feature"):
        # Let user select a feature
        feature_choices = [f"{info['name']} ({info['description']})" 
                         for f, info in FEATURE_INFO.items()]
        feature_choices.append("Cancel")
        
        feature_display = questionary.select(
            "Which audio feature would you like to use?",
            choices=feature_choices
        ).ask()
        
        if feature_display == "Cancel":
            return []
        
        # Get the feature key from the display name
        selected_feature = None
        for f, info in FEATURE_INFO.items():
            if feature_display.startswith(info['name']):
                selected_feature = f
                break
        
        if not selected_feature:
            return []
        
        # Get categories for this feature
        categories = audio_features.categorize_tracks_by_feature(tracks, selected_feature)
        
        if not categories:
            print(f"No categories found for feature '{selected_feature}'")
            return []
        
        # Create category choices with counts
        category_choices = [f"{cat.title()} ({len(tracks)} tracks)" 
                          for cat, tracks in categories.items()]
        category_choices.append("Cancel")
        
        # Let user select a category
        category_display = questionary.select(
            f"Which {FEATURE_INFO[selected_feature]['name']} category would you like?",
            choices=category_choices
        ).ask()
        
        if category_display == "Cancel":
            return []
        
        # Extract category name from display
        selected_category = category_display.split(" (")[0].lower()
        
        # Create the playlist
        created_playlist = create_feature_based_playlist(
            sp, tracks, selected_feature, selected_category
        )
        
        if created_playlist:
            return [created_playlist]
        else:
            return []
    
    # 3. For custom categories
    elif playlist_type.startswith("Based on a custom category"):
        # Generate custom categories
        custom_categories = audio_features.create_custom_categories(tracks)
        
        if not custom_categories:
            print("No custom categories could be created from these tracks")
            return []
        
        # Create category choices with descriptions and counts
        category_descriptions = {
            'workout': "High energy, fast tempo - perfect for exercise",
            'chill': "Low energy, high acousticness - relaxing mood",
            'party': "High danceability, high energy - for celebrations",
            'focus': "High instrumentalness, low speechiness - for concentration",
            'happy': "High valence, medium-high energy - uplifting tracks",
            'sad': "Low valence, low-medium energy - melancholic mood",
            'acoustic': "High acousticness - unplugged, natural sound",
            'electronic': "Low acousticness, high energy - electronic music",
            'intense': "High energy, high loudness - powerful sound",
            'background': "Low energy, low loudness - for ambient listening"
        }
        
        category_choices = []
        for cat, tracks in custom_categories.items():
            desc = category_descriptions.get(cat, "")
            category_choices.append(f"{cat.title()} ({len(tracks)} tracks) - {desc}")
        
        category_choices.append("Cancel")
        
        # Let user select a category
        category_display = questionary.select(
            "Which custom category would you like to use?",
            choices=category_choices
        ).ask()
        
        if category_display == "Cancel":
            return []
        
        # Extract category name from display
        selected_category = category_display.split(" (")[0].lower()
        
        # Get tracks for this category
        selected_tracks = custom_categories[selected_category]
        
        # Create playlist name and description
        playlist_name = f"{selected_category.title()} Music"
        description = f"{category_descriptions.get(selected_category, '')}. Created by Spotify Playlist Creator."
        
        # Create the playlist
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
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
        created_playlist = {
            'id': playlist['id'],
            'name': playlist_name,
            'category': selected_category,
            'track_count': len(selected_tracks)
        }
        
        return [created_playlist]
    
    return [] 