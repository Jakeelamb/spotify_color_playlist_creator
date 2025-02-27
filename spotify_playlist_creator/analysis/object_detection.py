"""Functions for detecting and classifying objects in album artwork."""

import os
import numpy as np
from PIL import Image
from tqdm import tqdm
import concurrent.futures
import multiprocessing

from spotify_playlist_creator import config
from spotify_playlist_creator.utils import image_utils, caching

# Flag to track if object detection is available
OBJECT_DETECTION_AVAILABLE = False

try:
    from ultralytics import YOLO
    OBJECT_DETECTION_AVAILABLE = True
except ImportError:
    pass

def is_available():
    """Check if object detection functionality is available."""
    return OBJECT_DETECTION_AVAILABLE

# Initialize the YOLO model (downloads pretrained weights if needed)
def get_model():
    """Get or initialize the YOLO model."""
    model_path = os.path.join(os.path.dirname(__file__), 'yolov8n.pt')
    # Check if model exists locally
    if not os.path.exists(model_path):
        print("Downloading pre-trained object detection model...")
        # This will download the model if it doesn't exist
    return YOLO('yolov8n')  # Use the smallest variant for speed

def detect_objects(image, confidence=0.3):
    """
    Detect objects in an image using YOLO.
    
    Args:
        image: PIL Image object
        confidence: Minimum confidence threshold (0-1)
        
    Returns:
        List of detected objects with their confidence scores
    """
    model = get_model()
    
    # Convert PIL image to format expected by YOLO
    img_array = np.array(image)
    
    # Run inference
    results = model(img_array, conf=confidence)[0]
    
    # Extract results
    detections = []
    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, conf, class_id = result
        class_name = results.names[int(class_id)]
        
        detections.append({
            'class': class_name,
            'confidence': float(conf),
            'bbox': (float(x1), float(y1), float(x2), float(y2))
        })
    
    return detections

def analyze_tracks_objects(tracks, use_cache=True, cache_file=None, force_reanalyze=False, max_workers=None, confidence=0.3):
    """
    Detect objects in album artwork for a list of tracks using parallel processing.
    
    Args:
        tracks: List of track dictionaries containing 'image_url'
        use_cache: Whether to use cached results
        cache_file: Path to cache file
        force_reanalyze: Force reanalysis even if cache exists
        max_workers: Maximum number of parallel workers
        confidence: Minimum confidence threshold
        
    Returns:
        Dictionary mapping track IDs to their object detection results
    """
    if cache_file is None:
        cache_file = config.OBJECT_DETECTION_CACHE
    
    # Try to load from cache first
    if use_cache and not force_reanalyze and caching.is_cache_valid(cache_file):
        cache_data = caching.load_cache(cache_file)
        if cache_data and 'object_detection' in cache_data:
            print(f"Using cached object detection from {cache_data.get('timestamp', 'unknown date')}")
            
            # Check if we need to analyze any new tracks
            cached_track_ids = set(cache_data['object_detection'].keys())
            current_track_ids = set(track['id'] for track in tracks)
            
            missing_tracks = current_track_ids - cached_track_ids
            if not missing_tracks:
                return cache_data['object_detection']
            
            print(f"Found {len(missing_tracks)} new tracks to analyze")
            tracks_to_analyze = [t for t in tracks if t['id'] in missing_tracks]
            analysis_results = cache_data['object_detection'].copy()
        else:
            tracks_to_analyze = tracks
            analysis_results = {}
    else:
        tracks_to_analyze = tracks
        analysis_results = {}
    
    if not tracks_to_analyze:
        return analysis_results
        
    print(f"Detecting objects in {len(tracks_to_analyze)} album covers...")
    
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
            try:
                # Detect objects in the image
                objects = detect_objects(image, confidence=confidence)
                return track['id'], objects
            except Exception as e:
                print(f"Error detecting objects in track {track['id']}: {str(e)}")
                return track['id'], None
        return track['id'], None
    
    # Use ThreadPoolExecutor for I/O-bound operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_track = {
            executor.submit(process_track, track): track 
            for track in tracks_to_analyze
        }
        
        for future in tqdm(
            concurrent.futures.as_completed(future_to_track), 
            total=len(tracks_to_analyze),
            desc="Detecting objects"
        ):
            track_id, result = future.result()
            if result:
                analysis_results[track_id] = result
    
    # Cache results
    if use_cache:
        cache_data = {'object_detection': analysis_results}
        caching.save_cache(cache_data, cache_file)
        print(f"Saved object detection for {len(analysis_results)} tracks to cache")
    
    return analysis_results

def group_tracks_by_object(tracks, object_detection_results, min_confidence=0.5):
    """
    Group tracks by detected objects in album artwork.
    
    Args:
        tracks: List of track dictionaries
        object_detection_results: Dictionary mapping track IDs to detection results
        min_confidence: Minimum confidence to include a detection
        
    Returns:
        Dictionary mapping object classes to lists of tracks
    """
    object_groups = {}
    
    for track in tracks:
        track_id = track['id']
        if track_id not in object_detection_results:
            continue
            
        detections = object_detection_results[track_id]
        if not detections:
            continue
            
        # Group by each object class that meets confidence threshold
        for detection in detections:
            if detection['confidence'] < min_confidence:
                continue
                
            obj_class = detection['class']
            
            if obj_class not in object_groups:
                object_groups[obj_class] = []
                
            # Add track with its detection info
            track_with_detection = track.copy()
            track_with_detection['detection'] = detection
            object_groups[obj_class].append(track_with_detection)
    
    return object_groups
