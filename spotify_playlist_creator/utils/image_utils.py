"""Utilities for image processing and analysis."""

import requests
import numpy as np
from PIL import Image
from io import BytesIO
import time
import colorsys
from spotify_playlist_creator import config

def download_image(image_url, max_retries=None, timeout=None):
    """Download album artwork image from URL with retry mechanism."""
    if max_retries is None:
        max_retries = config.DEFAULT_MAX_RETRIES
    if timeout is None:
        timeout = config.DEFAULT_IMAGE_TIMEOUT
        
    for attempt in range(max_retries):
        try:
            response = requests.get(image_url, timeout=timeout)
            return Image.open(BytesIO(response.content))
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Image download timed out. Retrying... ({attempt+1}/{max_retries})")
                time.sleep(1)
            else:
                print(f"Failed to download image after {max_retries} attempts.")
                return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

def is_grayscale(image, threshold=10):
    """Check if an image is grayscale (black, white, or gray)."""
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Check if image is already grayscale (only 1 channel)
    if len(img_array.shape) < 3 or img_array.shape[2] == 1:
        return True
    
    # Calculate difference between RGB channels
    r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
    diff_rg = np.abs(r - g)
    diff_rb = np.abs(r - b)
    diff_gb = np.abs(g - b)
    
    # If the average difference is below threshold, consider it grayscale
    avg_diff = (np.mean(diff_rg) + np.mean(diff_rb) + np.mean(diff_gb)) / 3
    return avg_diff < threshold

def categorize_grayscale(image):
    """Categorize grayscale image as black, white, or gray."""
    img_array = np.array(image.convert('L'))  # Convert to grayscale
    brightness = np.mean(img_array)
    
    if brightness < 50:
        return "Black"
    elif brightness > 200:
        return "White"
    else:
        return "Gray"

def rgb_to_hsv(rgb_tuple):
    """Convert RGB values (0-255) to HSV."""
    r, g, b = [x/255.0 for x in rgb_tuple]
    return colorsys.rgb_to_hsv(r, g, b)

def create_image_mosaic(images, grid_size=(5, 5), image_size=(300, 300), output_file=None):
    """Create a mosaic from multiple images."""
    rows, cols = grid_size
    
    # If we don't have enough images, duplicate some
    while len(images) < rows * cols and images:
        images.append(images[0])
    
    # Create the mosaic
    if not images:
        print("No images available for mosaic")
        return None
        
    mosaic_width = cols * image_size[0]
    mosaic_height = rows * image_size[1]
    mosaic = Image.new('RGB', (mosaic_width, mosaic_height))
    
    # Place images in the mosaic
    for i, img in enumerate(images[:rows*cols]):
        # Resize image
        img = img.resize(image_size)
        row = i // cols
        col = i % cols
        mosaic.paste(img, (col * image_size[0], row * image_size[1]))
    
    # Save the mosaic if output file is specified
    if output_file:
        mosaic.save(output_file)
        print(f"Saved mosaic to {output_file}")
        
    return mosaic
