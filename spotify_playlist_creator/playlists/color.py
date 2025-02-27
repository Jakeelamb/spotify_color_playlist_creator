"""Functions for creating color-based playlists."""

import os
from PIL import Image, ImageDraw
import numpy as np
from io import BytesIO
import requests
import base64
import random
from tqdm import tqdm

from spotify_playlist_creator.analysis import color_analysis
from spotify_playlist_creator.utils import image_utils
from spotify_playlist_creator import config

def create_color_playlists(sp, tracks, color_analysis_data, min_tracks=5, prefix="Color - ", public=True):
    """
    Create playlists based on dominant colors in album artwork.
    
    Args:
        sp: Spotify API client
        tracks: List of track dictionaries
        color_analysis_data: Dictionary mapping track IDs to color analysis
        min_tracks: Minimum number of tracks required to create a playlist
        prefix: Prefix for playlist names
        public: Whether playlists should be public
        
    Returns:
        List of created playlist information
    """
    print("Creating color-based playlists...")
    
    # Get current user ID
    user_id = sp.me()['id']
    
    # Group tracks by color
    color_groups = color_analysis.group_tracks_by_color(tracks, color_analysis_data)
    
    created_playlists = []
    
    # Create a playlist for each color with enough tracks
    for color, color_tracks in tqdm(color_groups.items(), desc="Creating playlists"):
        if len(color_tracks) < min_tracks:
            print(f"Skipping {color} playlist: only {len(color_tracks)} tracks (minimum is {min_tracks})")
            continue
            
        playlist_name = f"{prefix}{color}"
        description = f"Songs with {color.lower()} album artwork. Created by Spotify Color Playlist Creator."
        
        # Create the playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        
        # Add tracks to the playlist
        track_uris = [track['uri'] for track in color_tracks]
        
        # Add tracks in batches of 100 (Spotify API limit)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.playlist_add_items(playlist['id'], batch)
        
        # Create and upload playlist cover
        cover_image = create_color_cover_image(color_tracks, color)
        if cover_image:
            # Upload the cover image
            try:
                upload_playlist_cover(sp, playlist['id'], cover_image)
                print(f"Uploaded cover for {playlist_name}")
            except Exception as e:
                print(f"Failed to upload cover for {playlist_name}: {e}")
        
        # Store playlist info
        created_playlists.append({
            'id': playlist['id'],
            'name': playlist_name,
            'color': color,
            'track_count': len(color_tracks)
        })
        
        print(f"Created playlist: {playlist_name} with {len(color_tracks)} tracks")
    
    return created_playlists

def create_color_cover_image(tracks, color_name, size=(640, 640)):
    """Create a cover image for a color playlist."""
    # Select up to 4 album covers to include in the mosaic
    sample_size = min(4, len(tracks))
    sample_tracks = random.sample(tracks, sample_size)
    
    # Download album images
    images = []
    for track in sample_tracks:
        if track.get('image_url'):
            img = image_utils.download_image(track['image_url'])
            if img:
                images.append(img)
    
    if not images:
        # Create a solid color image if no album images are available
        dominant_color = tracks[0].get('color_analysis', {}).get('dominant_color')
        
        if not dominant_color:
            # Use a default color based on the color name
            colors = {
                'Red': (220, 60, 60),
                'Blue': (60, 60, 220),
                'Green': (60, 220, 60),
                'Yellow': (220, 220, 60),
                'Purple': (180, 60, 220),
                'Orange': (220, 140, 60),
                'Pink': (220, 60, 180),
                'Turquoise': (60, 220, 180),
                'Brown': (160, 120, 60),
                'Black': (20, 20, 20),
                'White': (240, 240, 240),
                'Gray': (128, 128, 128)
            }
            dominant_color = colors.get(color_name, (128, 128, 128))
        
        img = Image.new('RGB', size, dominant_color)
        
        # Add text to show the color name
        draw = ImageDraw.Draw(img)
        text_color = (255, 255, 255) if sum(dominant_color) < 380 else (0, 0, 0)
        draw.text((size[0]//2 - 50, size[1]//2), color_name, fill=text_color)
        
        return img
    
    # Create a mosaic of the album covers
    grid_size = (2, 2)
    img_size = (size[0]//grid_size[0], size[1]//grid_size[1])
    
    mosaic = image_utils.create_image_mosaic(images, grid_size, img_size)
    
    if not mosaic:
        return None
        
    return mosaic

def upload_playlist_cover(sp, playlist_id, image):
    """Upload a cover image for a playlist."""
    # Convert image to JPEG binary data
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    img_data = buffer.getvalue()
    
    # Encode as base64
    b64_encoded = base64.b64encode(img_data).decode('utf-8')
    
    # Upload
    sp.playlist_upload_cover_image(playlist_id, b64_encoded)
