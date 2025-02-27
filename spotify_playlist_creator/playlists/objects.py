"""Functions for creating object-based playlists."""

from tqdm import tqdm
from collections import Counter
import questionary

from spotify_playlist_creator import config
from spotify_playlist_creator.analysis import object_detection

def create_object_playlists(sp, tracks, object_detection_results, min_tracks=3, prefix="Objects - ", public=True):
    """
    Create playlists based on objects detected in album artwork.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries
        object_detection_results: Dictionary mapping track IDs to object detections
        min_tracks: Minimum tracks required to create a playlist
        prefix: Prefix for playlist names
        public: Whether playlists should be public
        
    Returns:
        List of created playlist information
    """
    print("Analyzing objects in album artwork...")
    
    # Analyze and summarize detected objects
    object_stats = analyze_object_stats(
        object_detection_results, 
        min_confidence=config.OBJECT_DETECTION_CONFIDENCE
    )
    
    # Display summary and get viable objects
    viable_objects = display_object_summary(object_stats, min_tracks)
    
    if not viable_objects:
        print("No objects have enough tracks to create playlists.")
        return []
    
    # Let user select which objects to create playlists for
    selected_objects = []
    
    # If only one object, ask if user wants to create a playlist for it
    if len(viable_objects) == 1:
        obj = viable_objects[0]
        if questionary.confirm(
            f"Create a playlist for the only viable object: '{obj}' ({object_stats[obj]['track_count']} tracks)?",
            default=True
        ).ask():
            selected_objects = [obj]
    else:
        # Create choices for questionary with track counts
        choices = [
            f"{obj} ({object_stats[obj]['track_count']} tracks)" 
            for obj in viable_objects
        ]
        
        # Add options for all or none
        choices.append("Create playlists for all objects")
        choices.append("Cancel - don't create any playlists")
        
        # Ask user to select
        selected = questionary.select(
            "Select which object-based playlist to create:",
            choices=choices
        ).ask()
        
        # Process selection
        if selected == "Create playlists for all objects":
            selected_objects = viable_objects
        elif selected == "Cancel - don't create any playlists":
            return []
        else:
            # Extract object name from selection (remove track count)
            obj_name = selected.split(" (")[0]
            selected_objects = [obj_name]
    
    # Group tracks by selected objects
    object_groups = object_detection.group_tracks_by_object(
        tracks, object_detection_results, min_confidence=config.OBJECT_DETECTION_CONFIDENCE
    )
    
    # Get current user ID
    user_id = sp.me()['id']
    
    created_playlists = []
    
    # Create playlists for selected objects
    for obj in tqdm(selected_objects, desc="Creating object playlists"):
        if obj not in object_groups or len(object_groups[obj]) < min_tracks:
            continue
            
        object_tracks = object_groups[obj]
        
        playlist_name = f"{prefix}{obj.title()}"
        description = f"Songs with {obj} in album artwork. Created by Spotify Color Playlist Creator."
        
        # Create the playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        
        # Add tracks to the playlist
        track_uris = [track['uri'] for track in object_tracks]
        
        # Add tracks in batches of 100 (Spotify API limit)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.playlist_add_items(playlist['id'], batch)
        
        # Store playlist info
        created_playlists.append({
            'id': playlist['id'],
            'name': playlist_name,
            'object': obj,
            'track_count': len(object_tracks)
        })
        
        print(f"Created playlist: {playlist_name} with {len(object_tracks)} tracks")
    
    return created_playlists

def analyze_object_stats(object_detection_results, min_confidence=0.4):
    """
    Analyze and summarize detected objects across all album artwork.
    
    Args:
        object_detection_results: Dictionary mapping track IDs to object detections
        min_confidence: Minimum confidence to include a detection
        
    Returns:
        Dictionary mapping object classes to their counts and avg confidence
    """
    object_stats = {}
    track_count_per_object = {}
    
    # Gather all objects and their statistics
    for track_id, detections in object_detection_results.items():
        if not detections:
            continue
            
        track_objects = set()  # Track unique objects per track
        
        for detection in detections:
            if detection['confidence'] < min_confidence:
                continue
                
            obj_class = detection['class']
            confidence = detection['confidence']
            
            # Initialize stats if first occurrence
            if obj_class not in object_stats:
                object_stats[obj_class] = {
                    'total_count': 0,
                    'confidence_sum': 0,
                    'track_count': 0  # Number of tracks containing this object
                }
                
            # Update statistics
            object_stats[obj_class]['total_count'] += 1
            object_stats[obj_class]['confidence_sum'] += confidence
            
            # Count this track once per object class
            if obj_class not in track_objects:
                track_objects.add(obj_class)
                object_stats[obj_class]['track_count'] += 1
    
    # Calculate average confidence and finalize stats
    for obj_class, stats in object_stats.items():
        if stats['total_count'] > 0:
            stats['avg_confidence'] = stats['confidence_sum'] / stats['total_count']
        else:
            stats['avg_confidence'] = 0
            
    # Sort by track count
    sorted_stats = {k: v for k, v in sorted(
        object_stats.items(), 
        key=lambda item: item[1]['track_count'], 
        reverse=True
    )}
    
    return sorted_stats

def display_object_summary(object_stats, min_tracks=3):
    """
    Display a summary of detected objects for the user.
    
    Args:
        object_stats: Dictionary mapping object classes to their stats
        min_tracks: Minimum number of tracks to highlight an object
        
    Returns:
        List of objects with enough tracks to create playlists
    """
    print("\n📊 Object Detection Summary:")
    print(f"{'Object':<20} {'Tracks':<10} {'Total':<10} {'Avg Confidence':<15}")
    print("-" * 55)
    
    viable_objects = []
    
    for obj_class, stats in object_stats.items():
        track_count = stats['track_count']
        total_count = stats['total_count']
        avg_conf = stats['avg_confidence'] * 100  # Convert to percentage
        
        # Format the output
        if track_count >= min_tracks:
            viable_objects.append(obj_class)
            status = "✅"  # Viable for playlist
        else:
            status = "❌"  # Not enough tracks
            
        print(f"{obj_class:<18} {track_count:<10} {total_count:<10} {avg_conf:.1f}%  {status}")
    
    print(f"\nFound {len(viable_objects)} object categories with at least {min_tracks} tracks.")
    return viable_objects 