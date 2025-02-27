"""Functions for fetching and analyzing song lyrics."""

import os
import re
import time
import concurrent.futures
import multiprocessing
from tqdm import tqdm
from collections import Counter

from spotify_playlist_creator import config
from spotify_playlist_creator.utils import caching

# Flag to track if lyrics analysis is available
LYRICS_ANALYSIS_AVAILABLE = False

try:
    import lyricsgenius
    import nltk
    from nltk.corpus import stopwords
    from textblob import TextBlob
    
    # Download required NLTK resources
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    LYRICS_ANALYSIS_AVAILABLE = True
except ImportError:
    pass

def is_available():
    """Check if lyrics analysis functionality is available."""
    return LYRICS_ANALYSIS_AVAILABLE

def get_genius_client():
    """Initialize and return a Genius API client."""
    # First check if the user has provided their own token
    if hasattr(config, 'GENIUS_CLIENT_ACCESS_TOKEN') and config.GENIUS_CLIENT_ACCESS_TOKEN:
        # Use the user's provided access token
        return lyricsgenius.Genius(config.GENIUS_CLIENT_ACCESS_TOKEN, timeout=10, retries=3)
    # Fall back to the general token if provided
    elif hasattr(config, 'GENIUS_API_TOKEN') and config.GENIUS_API_TOKEN != "YOUR_GENIUS_API_TOKEN":
        return lyricsgenius.Genius(config.GENIUS_API_TOKEN, timeout=10, retries=3)
    else:
        print("Genius API token not properly configured in config.py")
        return None

def get_lyrics(track, genius_client=None):
    """
    Fetch lyrics for a track using Genius.
    
    Args:
        track: Dictionary containing 'name' and 'artist'
        genius_client: Optional pre-initialized Genius client
        
    Returns:
        Lyrics string or None if not found
    """
    # Create Genius client if not provided
    if genius_client is None:
        genius_client = get_genius_client()
    
    try:
        # Search for the song
        artist_name = track['artist']
        track_name = track['name']
        
        # Remove features and additional text for better searching
        cleaned_track_name = re.sub(r'\(feat\..*?\)', '', track_name)
        cleaned_track_name = re.sub(r' - .*$', '', cleaned_track_name)
        
        song = genius_client.search_song(cleaned_track_name, artist_name)
        
        if song:
            # Clean the lyrics (remove section headers, annotations, etc.)
            lyrics = song.lyrics
            lyrics = re.sub(r'\[.*?\]', '', lyrics)  # Remove [Verse], [Chorus], etc.
            lyrics = re.sub(r'\d+Embed', '', lyrics)  # Remove Genius annotations
            lyrics = re.sub(r'Lyrics\s*\d*\s*', '', lyrics)  # Remove "Lyrics"
            lyrics = lyrics.strip()
            return lyrics
    
    except Exception as e:
        print(f"Error fetching lyrics for {track['name']} by {track['artist']}: {str(e)}")
    
    return None

def fetch_and_cache_lyrics(tracks, use_cache=True, cache_file=None, force_refetch=False, max_workers=None):
    """
    Fetch lyrics for a list of tracks and cache them.
    
    Args:
        tracks: List of track dictionaries
        use_cache: Whether to use cached results
        cache_file: Path to cache file
        force_refetch: Force refetching lyrics even if cache exists
        max_workers: Maximum number of threads to use
        
    Returns:
        Dictionary of track IDs to lyrics
    """
    if not LYRICS_ANALYSIS_AVAILABLE:
        print("Lyrics analysis is not available. Install with: pip install 'spotify-color-playlist-creator[lyrics]'")
        return {}
        
    # Initialize Genius client first to check if credentials are working
    genius_client = get_genius_client()
    if not genius_client:
        print("Could not initialize Genius client. Please check your API credentials.")
        return {}
    
    if cache_file is None:
        cache_file = config.LYRICS_CACHE
    
    # Try to load from cache first
    if use_cache and not force_refetch and caching.is_cache_valid(cache_file):
        cache_data = caching.load_cache(cache_file)
        if cache_data and 'lyrics' in cache_data:
            print(f"Using cached lyrics from {cache_data.get('timestamp', 'unknown date')}")
            
            # Check for new tracks
            cached_track_ids = set(cache_data['lyrics'].keys())
            current_track_ids = set(track['id'] for track in tracks)
            
            missing_tracks = current_track_ids - cached_track_ids
            if not missing_tracks:
                return cache_data['lyrics']
            
            print(f"Found {len(missing_tracks)} new tracks to fetch lyrics for")
            tracks_to_fetch = [t for t in tracks if t['id'] in missing_tracks]
            lyrics_results = cache_data['lyrics'].copy()
        else:
            tracks_to_fetch = tracks
            lyrics_results = {}
    else:
        tracks_to_fetch = tracks
        lyrics_results = {}
    
    if not tracks_to_fetch:
        return lyrics_results
        
    print(f"Fetching lyrics for {len(tracks_to_fetch)} tracks...")
    
    # Set default max_workers if not specified
    if max_workers is None:
        # For API requests, fewer workers is often better to avoid rate limits
        max_workers = min(5, multiprocessing.cpu_count())
    
    # Use ThreadPoolExecutor for I/O-bound operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_track = {
            executor.submit(get_lyrics, track, genius_client): track 
            for track in tracks_to_fetch
        }
        
        for future in tqdm(
            concurrent.futures.as_completed(future_to_track), 
            total=len(tracks_to_fetch),
            desc="Fetching lyrics"
        ):
            track, lyrics = future.result()
            if lyrics:  # Only add if lyrics were found
                lyrics_results[track['id']] = lyrics
    
    # Cache results
    if use_cache:
        cache_data = {'lyrics': lyrics_results}
        caching.save_cache(cache_data, cache_file)
        print(f"Saved lyrics for {len(lyrics_results)} tracks to cache")
    
    return lyrics_results

def analyze_lyrics_sentiment(lyrics):
    """
    Analyze sentiment of lyrics using TextBlob.
    
    Args:
        lyrics: String containing lyrics
        
    Returns:
        Dictionary with sentiment analysis results
    """
    if not lyrics:
        return None
        
    blob = TextBlob(lyrics)
    
    # Overall sentiment
    sentiment = blob.sentiment
    
    # Count occurrences of specific emotion words
    emotion_keywords = {
        'love': ['love', 'loved', 'loving', 'lover'],
        'sad': ['sad', 'sadness', 'grief', 'sorrow', 'tear', 'tears', 'cry', 'crying'],
        'happy': ['happy', 'happiness', 'joy', 'smile', 'laugh', 'laughing'],
        'angry': ['angry', 'anger', 'rage', 'hate', 'mad', 'fury'],
        'fear': ['fear', 'afraid', 'scared', 'terror', 'horror'],
    }
    
    # Count emotions
    emotion_counts = {}
    
    for emotion, keywords in emotion_keywords.items():
        count = sum(lyrics.lower().count(keyword) for keyword in keywords)
        emotion_counts[emotion] = count
    
    return {
        'polarity': float(sentiment.polarity),  # -1 to 1, negative to positive
        'subjectivity': float(sentiment.subjectivity),  # 0 to 1, objective to subjective
        'emotion_counts': emotion_counts,
        'word_count': len(blob.words),
        'is_explicit': is_explicit(lyrics)
    }

def is_explicit(lyrics):
    """Check if lyrics contain explicit content."""
    if not lyrics:
        return False
        
    # List of explicit words to check for
    explicit_words = set([
        'fuck', 'shit', 'bitch', 'ass', 'damn', 'hell', 'crap', 
        'dick', 'cock', 'pussy', 'nigga', 'nigger', 'hoe'
    ])
    
    # Count explicit words in lyrics
    words = re.findall(r'\b\w+\b', lyrics.lower())
    explicit_count = sum(1 for word in words if word in explicit_words)
    
    # Return True if any explicit words are found
    return explicit_count > 0

def extract_topics(lyrics, n_topics=5):
    """
    Extract main topics/themes from lyrics.
    
    Args:
        lyrics: String containing lyrics
        n_topics: Number of top topics to extract
        
    Returns:
        List of top topics
    """
    if not lyrics:
        return []
    
    # Tokenize and clean
    words = nltk.word_tokenize(lyrics.lower())
    
    # Remove stopwords, punctuation, and numbers
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 2]
    
    # Get word frequencies
    word_freq = Counter(words)
    
    # Return top N topics
    return word_freq.most_common(n_topics)

def analyze_tracks_lyrics(tracks, lyrics_data):
    """
    Analyze lyrics for a list of tracks.
    
    Args:
        tracks: List of track dictionaries
        lyrics_data: Dictionary mapping track IDs to lyrics
        
    Returns:
        Dictionary mapping track IDs to lyrics analysis
    """
    analysis_results = {}
    
    print(f"Analyzing lyrics for {len(lyrics_data)} tracks...")
    
    for track_id, lyrics in tqdm(lyrics_data.items(), desc="Analyzing lyrics"):
        sentiment = analyze_lyrics_sentiment(lyrics)
        topics = extract_topics(lyrics)
        
        if sentiment:
            analysis_results[track_id] = {
                'sentiment': sentiment,
                'topics': topics
            }
    
    return analysis_results

def group_tracks_by_mood(tracks, lyrics_analysis):
    """
    Group tracks by their lyrical mood based on sentiment analysis.
    
    Args:
        tracks: List of track dictionaries
        lyrics_analysis: Dictionary mapping track IDs to lyrics analysis
        
    Returns:
        Dictionary mapping moods to lists of tracks
    """
    mood_groups = {
        'happy': [],
        'sad': [],
        'angry': [],
        'neutral': [],
        'love': [],
        'explicit': []
    }
    
    for track in tracks:
        track_id = track['id']
        if track_id not in lyrics_analysis:
            continue
            
        analysis = lyrics_analysis[track_id]
        sentiment = analysis.get('sentiment', {})
        
        if not sentiment:
            continue
            
        # Add to explicit group if applicable
        if sentiment.get('is_explicit', False):
            mood_groups['explicit'].append(track)
        
        # Get the dominant emotion based on word counts
        emotion_counts = sentiment.get('emotion_counts', {})
        max_emotion = max(emotion_counts.items(), key=lambda x: x[1], default=('neutral', 0))
        
        # If love is dominant, add to love group
        if max_emotion[0] == 'love' and max_emotion[1] > 0:
            mood_groups['love'].append(track)
            continue
        
        # Otherwise use sentiment polarity
        polarity = sentiment.get('polarity', 0)
        
        if polarity > 0.3:
            mood_groups['happy'].append(track)
        elif polarity < -0.3:
            mood_groups['sad'].append(track)
        elif 'angry' in emotion_counts and emotion_counts['angry'] > 0:
            mood_groups['angry'].append(track)
        else:
            mood_groups['neutral'].append(track)
    
    return mood_groups 