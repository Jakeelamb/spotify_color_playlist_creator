"""Functions for analyzing Spotify audio features."""

import numpy as np
from collections import defaultdict
from tqdm import tqdm

def summarize_audio_features(tracks):
    """
    Generate a summary of audio features across all tracks.
    
    Args:
        tracks: List of track dictionaries with audio_features
        
    Returns:
        Dictionary with feature statistics
    """
    # Initialize counters and accumulators
    features_count = 0
    features_sum = defaultdict(float)
    features_min = {}
    features_max = {}
    
    # These are the numeric features we'll analyze
    numeric_features = [
        'acousticness', 'danceability', 'energy', 'instrumentalness',
        'liveness', 'loudness', 'speechiness', 'tempo', 'valence'
    ]
    
    # Count occurrences of categorical features
    key_counts = defaultdict(int)
    mode_counts = defaultdict(int)
    time_signature_counts = defaultdict(int)
    
    # Key names for better display
    key_names = {
        0: 'C', 1: 'C♯/D♭', 2: 'D', 3: 'D♯/E♭', 4: 'E', 5: 'F',
        6: 'F♯/G♭', 7: 'G', 8: 'G♯/A♭', 9: 'A', 10: 'A♯/B♭', 11: 'B'
    }
    
    mode_names = {0: 'Minor', 1: 'Major'}
    
    # Process each track
    for track in tracks:
        # Skip tracks without audio features
        if 'audio_features' not in track or not track['audio_features']:
            continue
            
        features = track['audio_features']
        features_count += 1
        
        # Process numeric features
        for feature in numeric_features:
            if feature in features and features[feature] is not None:
                value = features[feature]
                features_sum[feature] += value
                
                # Update min/max
                if feature not in features_min or value < features_min[feature]:
                    features_min[feature] = value
                if feature not in features_max or value > features_max[feature]:
                    features_max[feature] = value
        
        # Process categorical features
        if 'key' in features and features['key'] is not None and features['key'] >= 0:
            key_counts[features['key']] += 1
            
        if 'mode' in features and features['mode'] is not None:
            mode_counts[features['mode']] += 1
            
        if 'time_signature' in features and features['time_signature'] is not None:
            time_signature_counts[features['time_signature']] += 1
    
    # Calculate averages
    features_avg = {feature: features_sum[feature] / features_count 
                   for feature in features_sum}
    
    # Format the summary
    summary = {
        'count': features_count,
        'averages': features_avg,
        'min': features_min,
        'max': features_max,
        'key_distribution': {key_names[k]: count for k, count in key_counts.items()},
        'mode_distribution': {mode_names[m]: count for m, count in mode_counts.items()},
        'time_signature_distribution': dict(time_signature_counts)
    }
    
    return summary

def categorize_tracks_by_feature(tracks, feature, thresholds=None):
    """
    Group tracks based on a specific audio feature.
    
    Args:
        tracks: List of track dictionaries with audio_features
        feature: Feature name to categorize by (e.g., 'energy')
        thresholds: Dictionary of category thresholds (if None, uses defaults)
        
    Returns:
        Dictionary mapping categories to lists of tracks
    """
    # Default thresholds for common features
    default_thresholds = {
        'energy': {'low': 0.3, 'medium': 0.6, 'high': 1.0},
        'danceability': {'low': 0.4, 'medium': 0.7, 'high': 1.0},
        'valence': {'sad': 0.3, 'neutral': 0.6, 'happy': 1.0},
        'acousticness': {'low': 0.3, 'medium': 0.7, 'high': 1.0},
        'tempo': {'slow': 95, 'medium': 120, 'fast': 180, 'very_fast': 300},
        'loudness': {'quiet': -20, 'medium': -10, 'loud': 0},
        'instrumentalness': {'vocal': 0.2, 'mixed': 0.7, 'instrumental': 1.0},
        'speechiness': {'music': 0.33, 'music_and_speech': 0.66, 'speech': 1.0},
        'liveness': {'studio': 0.4, 'live': 1.0}
    }
    
    # Use provided thresholds or defaults
    if thresholds is None:
        if feature in default_thresholds:
            thresholds = default_thresholds[feature]
        else:
            # For unknown features, split into generic low/medium/high
            thresholds = {'low': 0.33, 'medium': 0.67, 'high': 1.0}
    
    # Initialize categories
    categories = {cat: [] for cat in thresholds.keys()}
    
    # Special handling for key and mode
    if feature == 'key':
        key_names = {
            0: 'C', 1: 'C♯/D♭', 2: 'D', 3: 'D♯/E♭', 4: 'E', 5: 'F',
            6: 'F♯/G♭', 7: 'G', 8: 'G♯/A♭', 9: 'A', 10: 'A♯/B♭', 11: 'B'
        }
        categories = {name: [] for name in key_names.values()}
    elif feature == 'mode':
        categories = {'Minor': [], 'Major': []}
    elif feature == 'time_signature':
        categories = {'3/4': [], '4/4': [], '5/4': [], '6/8': [], 'Other': []}
    
    # Categorize tracks
    for track in tracks:
        if 'audio_features' not in track or not track['audio_features']:
            continue
            
        features = track['audio_features']
        
        # Skip if the feature doesn't exist
        if feature not in features or features[feature] is None:
            continue
            
        value = features[feature]
        
        # Handle categorical features
        if feature == 'key' and value >= 0:
            key_name = key_names.get(value, 'Unknown')
            categories[key_name].append(track)
            continue
            
        if feature == 'mode':
            mode_name = 'Major' if value == 1 else 'Minor'
            categories[mode_name].append(track)
            continue
            
        if feature == 'time_signature':
            if value == 3:
                categories['3/4'].append(track)
            elif value == 4:
                categories['4/4'].append(track)
            elif value == 5:
                categories['5/4'].append(track)
            elif value == 6:
                categories['6/8'].append(track)
            else:
                categories['Other'].append(track)
            continue
        
        # Handle numeric features
        last_cat = list(thresholds.keys())[0]  # Default if below all thresholds
        for cat, threshold in thresholds.items():
            if value <= threshold:
                categories[cat].append(track)
                break
            last_cat = cat
    
    # Remove empty categories
    categories = {cat: tracks for cat, tracks in categories.items() if tracks}
    
    return categories

def create_custom_categories(tracks):
    """
    Create custom categories based on combinations of features.
    
    Args:
        tracks: List of track dictionaries with audio_features
        
    Returns:
        Dictionary mapping category names to lists of tracks
    """
    categories = {
        'workout': [],         # High energy, fast tempo
        'chill': [],           # Low energy, high acousticness
        'party': [],           # High danceability, high energy
        'focus': [],           # High instrumentalness, low speechiness
        'happy': [],           # High valence, medium-high energy
        'sad': [],             # Low valence, low-medium energy
        'acoustic': [],        # High acousticness 
        'electronic': [],      # Low acousticness, high energy
        'intense': [],         # High energy, high loudness
        'background': [],      # Low energy, low loudness
    }
    
    for track in tracks:
        if 'audio_features' not in track or not track['audio_features']:
            continue
            
        f = track['audio_features']
        
        # Ensure all needed features exist
        required = ['energy', 'acousticness', 'danceability', 'instrumentalness', 
                   'speechiness', 'valence', 'tempo', 'loudness']
        if not all(feat in f and f[feat] is not None for feat in required):
            continue
        
        # Workout music: high energy, fast tempo
        if f['energy'] > 0.7 and f['tempo'] > 120:
            categories['workout'].append(track)
            
        # Chill music: low energy, high acousticness
        if f['energy'] < 0.4 and f['acousticness'] > 0.6:
            categories['chill'].append(track)
            
        # Party music: high danceability, high energy
        if f['danceability'] > 0.7 and f['energy'] > 0.7:
            categories['party'].append(track)
            
        # Focus music: high instrumentalness, low speechiness
        if f['instrumentalness'] > 0.5 and f['speechiness'] < 0.1:
            categories['focus'].append(track)
            
        # Happy music: high valence, medium-high energy
        if f['valence'] > 0.7 and f['energy'] > 0.5:
            categories['happy'].append(track)
            
        # Sad music: low valence, low-medium energy
        if f['valence'] < 0.3 and f['energy'] < 0.6:
            categories['sad'].append(track)
            
        # Acoustic music: high acousticness
        if f['acousticness'] > 0.8:
            categories['acoustic'].append(track)
            
        # Electronic music: low acousticness, high energy
        if f['acousticness'] < 0.3 and f['energy'] > 0.7:
            categories['electronic'].append(track)
            
        # Intense music: high energy, high loudness
        if f['energy'] > 0.8 and f['loudness'] > -5:
            categories['intense'].append(track)
            
        # Background music: low energy, low loudness
        if f['energy'] < 0.3 and f['loudness'] < -15:
            categories['background'].append(track)
    
    # Remove empty categories
    categories = {cat: tracks for cat, tracks in categories.items() if tracks}
    
    return categories 