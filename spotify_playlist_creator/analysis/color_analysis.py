"""Functions for analyzing colors in album artwork."""

import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import colorsys
from PIL import Image
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import os
import time
from tqdm import tqdm
import concurrent.futures
import multiprocessing

from spotify_playlist_creator import config
from spotify_playlist_creator.utils import image_utils, caching

def analyze_tracks_colors(tracks, use_cache=True, cache_file=None, force_reanalyze=False, max_workers=None):
    """
    Analyze colors of album artwork for a list of tracks using parallel processing.
    
    Args:
        tracks: List of track dictionaries containing 'image_url'
        use_cache: Whether to use cached results
        cache_file: Path to cache file
        force_reanalyze: Force reanalysis even if cache exists
        max_workers: Maximum number of parallel workers (defaults to CPU count - 1)
        
    Returns:
        Dictionary mapping track IDs to their color analysis results
    """
    if cache_file is None:
        cache_file = config.COLOR_ANALYSIS_CACHE
    
    # Try to load from cache first
    if use_cache and not force_reanalyze and caching.is_cache_valid(cache_file):
        cache_data = caching.load_cache(cache_file)
        if cache_data and 'color_analysis' in cache_data:
            print(f"Using cached color analysis from {cache_data.get('timestamp', 'unknown date')}")
            
            # Check if we need to analyze any new tracks
            cached_track_ids = set(cache_data['color_analysis'].keys())
            current_track_ids = set(track['id'] for track in tracks)
            
            missing_tracks = current_track_ids - cached_track_ids
            if not missing_tracks:
                return cache_data['color_analysis']
            
            print(f"Found {len(missing_tracks)} new tracks to analyze")
            # Continue with analysis but only for new tracks
            tracks_to_analyze = [t for t in tracks if t['id'] in missing_tracks]
            analysis_results = cache_data['color_analysis'].copy()
        else:
            tracks_to_analyze = tracks
            analysis_results = {}
    else:
        tracks_to_analyze = tracks
        analysis_results = {}
    
    if not tracks_to_analyze:
        return analysis_results
        
    print(f"Analyzing colors for {len(tracks_to_analyze)} tracks in parallel...")
    
    # Set default max_workers if not specified
    if max_workers is None:
        max_workers = max(1, multiprocessing.cpu_count() - 1)
    
    # Define a worker function for parallel processing
    def process_track(track):
        if not track.get('image_url'):
            return track['id'], None
            
        # Download and analyze image
        image = image_utils.download_image(track['image_url'])
        if image:
            # Analyze the image
            return track['id'], extract_color_info(image)
        return track['id'], None
    
    # Use ThreadPoolExecutor for I/O-bound operations (downloading images)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and create a mapping of futures to track IDs
        future_to_track = {
            executor.submit(process_track, track): track 
            for track in tracks_to_analyze
        }
        
        # Process results as they complete with progress bar
        for future in tqdm(
            concurrent.futures.as_completed(future_to_track), 
            total=len(tracks_to_analyze),
            desc="Analyzing album artwork"
        ):
            track_id, result = future.result()
            if result:
                analysis_results[track_id] = result
    
    # Cache results
    if use_cache:
        cache_data = {'color_analysis': analysis_results}
        caching.save_cache(cache_data, cache_file)
        print(f"Saved color analysis for {len(analysis_results)} tracks to cache")
    
    return analysis_results


def analyze_image_batch(image_batch):
    """Process a batch of images in parallel using ProcessPoolExecutor."""
    results = []
    # Use ProcessPoolExecutor for CPU-bound operations (color analysis)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Map the extract_color_info function to each image
        results = list(executor.map(extract_color_info, image_batch))
    return results


def extract_color_info(image, num_colors=5):
    """
    Extract and analyze dominant colors from an image.
    
    Args:
        image: PIL Image object
        num_colors: Number of dominant colors to extract
        
    Returns:
        Dictionary with color analysis information
    """
    # Resize image for faster processing
    img_small = image.resize((100, 100))
    
    # Convert to numpy array and reshape for clustering
    img_array = np.array(img_small)
    
    # Check if grayscale
    if image_utils.is_grayscale(image):
        gray_category = image_utils.categorize_grayscale(image)
        return {
            'is_grayscale': True,
            'grayscale_category': gray_category,
            'dominant_color': gray_category,
            'color_category': gray_category,
            'dominant_colors': [(128, 128, 128)],  # Placeholder gray
            'color_percentages': [100.0]
        }
    
    # Reshape the array to be a list of pixels
    pixels = img_array.reshape(-1, 3)
    
    # Use KMeans clustering to find dominant colors
    kmeans = KMeans(n_clusters=num_colors)
    kmeans.fit(pixels)
    
    # Get the colors - convert to standard Python ints
    colors = kmeans.cluster_centers_.astype(int).tolist()
    
    # Count pixel assignments to get color percentages
    labels = kmeans.labels_
    counter = Counter(labels)
    total_pixels = len(pixels)
    
    # Sort colors by frequency
    color_percentages = []
    dominant_colors = []
    
    for i in range(num_colors):
        if i in counter:
            percentage = float((counter[i] / total_pixels) * 100)  # Explicit conversion to float
            color_percentages.append(percentage)
            dominant_colors.append(tuple(colors[i]))  # Convert to tuple for consistent handling
    
    # Sort colors by percentage
    sorted_indices = np.argsort(color_percentages)[::-1].tolist()  # Convert to list
    dominant_colors = [dominant_colors[i] for i in sorted_indices]
    color_percentages = [float(color_percentages[i]) for i in sorted_indices]  # Explicit conversion
    
    # Get the most dominant color
    main_color = dominant_colors[0]
    
    # Determine color category
    color_name = get_closest_color_name(main_color)
    color_category = get_color_category(color_name)
    
    # Calculate average hue, saturation, and value
    hsv_values = [image_utils.rgb_to_hsv(color) for color in dominant_colors]
    
    # Convert weights to standard Python floats
    weights = [float(p) for p in color_percentages]
    
    # Calculate weighted average and convert to tuple of floats
    avg_hsv = tuple(float(v) for v in np.average(hsv_values, axis=0, weights=weights))
    
    return {
        'is_grayscale': False,
        'dominant_color': main_color,
        'color_name': color_name,
        'color_category': color_category,
        'dominant_colors': dominant_colors,
        'color_percentages': color_percentages,
        'average_hsv': avg_hsv
    }

def get_color_category(color_name):
    """Map a color name to its category based on config."""
    color_name = color_name.lower()
    if color_name in config.COLOR_CATEGORIES:
        return config.COLOR_CATEGORIES[color_name]
    return "Other"

def get_closest_color_name(rgb_color):
    """Find the closest named color to the given RGB value."""
    r, g, b = rgb_color
    
    # Convert to 0-1 range for matplotlib
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    
    # Get all named colors from matplotlib
    colors = mcolors.CSS4_COLORS
    
    min_distance = float('inf')
    closest_color = "black"
    
    for name, hex_color in colors.items():
        # Convert hex to RGB
        rgb = mcolors.to_rgb(hex_color)
        
        # Calculate Euclidean distance
        distance = (r_norm - rgb[0])**2 + (g_norm - rgb[1])**2 + (b_norm - rgb[2])**2
        
        if distance < min_distance:
            min_distance = distance
            closest_color = name
    
    return closest_color

def group_tracks_by_color(tracks, color_analysis):
    """
    Group tracks by their dominant color categories.
    
    Args:
        tracks: List of track dictionaries
        color_analysis: Dictionary mapping track IDs to color analysis
        
    Returns:
        Dictionary mapping color categories to lists of tracks
    """
    color_groups = {}
    
    for track in tracks:
        track_id = track['id']
        if track_id not in color_analysis:
            continue
            
        analysis = color_analysis[track_id]
        category = analysis.get('color_category', 'Other')
        
        if category not in color_groups:
            color_groups[category] = []
            
        color_groups[category].append({
            **track,
            'color_analysis': analysis
        })
    
    return color_groups

def visualize_color_distribution(color_analysis, output_file=None):
    """Create a visualization of the color distribution in the analyzed tracks."""
    # Count occurrences of each color category
    categories = [analysis.get('color_category', 'Other') 
                 for analysis in color_analysis.values()]
    
    counter = Counter(categories)
    
    # Create bar chart
    labels = list(counter.keys())
    values = list(counter.values())
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, values)
    
    # Color the bars according to their category
    for i, label in enumerate(labels):
        color = label.lower()
        if color in ['black', 'white', 'gray', 'other']:
            color = {'black': 'black', 'white': 'white', 
                    'gray': 'gray', 'other': 'darkgray'}[color]
        bars[i].set_color(color)
    
    plt.xlabel('Color Categories')
    plt.ylabel('Number of Tracks')
    plt.title('Distribution of Album Artwork Colors')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"Saved color distribution visualization to {output_file}")
    else:
        plt.show()
