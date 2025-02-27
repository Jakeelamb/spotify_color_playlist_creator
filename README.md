# Spotify Color Playlist Creator

A tool that analyzes album artwork from your Spotify library to create playlists based on colors, objects, moods, and more.

## Overview

This project leverages the Spotify API to analyze album artwork and create custom playlists based on various visual attributes:

- **Color-based playlists**: Group songs by dominant album cover colors
- **Object detection**: Create playlists based on objects detected in album art
- **Seasonal themes**: Generate playlists that match seasonal color palettes and themes
- **Time of day**: Curate playlists suitable for different times of day
- **Mood-based**: Create playlists based on the mood conveyed by the artwork
- **Gradient collections**: Organize songs in color gradient sequences
- **Image creation**: Arrange songs to form visual patterns when viewed as a playlist

## Directory Structure

# spotify_color_playlist_creator
Use spotify api to create playlists by colors from album artwork


# Spotify web api details
Client_id = 7d31698de0874df9ab08249f3c046561
Client secret = 20bb675d81d64cd3a771b75daed51012
app name : Color_playlist_maker
redirect url: http://localhost:8080


# Breakdown

## Directory Structure
    Spotify_Playlist_Maker
  spotify_api
    scrape_songs.py
  Analysis
    Color_analysis.py
    Object_detection.py
  Playlists
    Color.py
    Seasonal.py
    Time_of_Day.py
    Mood.py
    Objects.py
    Gradient.py
    Image.py


## Workflow

# 1. Login
    - Enter login credentials 

# 2. Choose playlist
    - Default (liked songs)

# 3. Scrape metadata using api
    - scrape_songs.py
        (store all the metadata in a file or cache to prevent reanalysis)
# 4. Analyze
    - Color analysis using deep learning, kmeans clustering, or whatever is best
        (Store all the attributes of the colors [each unique color and its proportion, mean color, blended color value, etc])
    - Object analysis using machine leaning model for object detection. 
        (Create a list of all the objects found in the image, Need to explore clustering these objects into groups to offer options for ideas)
    - Lyrics analysis
        (Need to think about this but maybe perform an analysis to capture the themes of the lyrics)
    - Location analysis
        (Be able to group songs by city, county, state, country, continent, etc)
    - Time analysis
        (Time data and year that the song was released) *Need to be careful about remastered tracks
    - Genre and bpm
        (collect and store info on Genre and bpm if possible)
** Important to create a master data set that is not provided to user to limit the amount of unique analysis needed to be done user to user
# 5. Create playlists
    - Color
        (Create playlists based on colors)
    - Seasonal
        (Create playlists based on seasonal things, color pallete, lyrics, publish data, etc. 
    - Time_of_Day
        (Create playlists for songs that are energetic for morning, calm for evening, reckless for friday after work, etc)
    - Mood
        (Create playlists based on mood)
    - Objects
        (Create playlists based on objects detected in artwork or discussed in lyrics)
    - Gradient
        (Create playlists using color gradients)
    - Image
        (Create playlists by making images in the artwork. For instance a smiley face can be selected and the songs will be matched from their colors to the pixels to create the playlist and the playlist coverart)


## Future Directions
    - Implement stripe payment to $1.99 per month
    - Create a website for the tool

## Authentication Setup

This project requires Spotify API credentials. For security:

1. Create a `config.py` file in the root directory with your Spotify credentials:

```python
# config.py
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:8080'
```

2. Add this file to your `.gitignore` to prevent it from being committed:
```
# .gitignore
config.py
__pycache__/
*.pyc
```

3. Reference these credentials in your code:
```python
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
```

**Note:** Never commit API keys or secrets to GitHub. The `config.py` approach keeps credentials local to your development environment.

## Workflow

### 1. Authentication
- User authenticates with Spotify credentials
- Application requests appropriate permissions

### 2. Select Source Playlist
- User selects a playlist to analyze (default: liked songs)

### 3. Metadata Collection
- `scrape_songs.py` collects metadata from selected playlist
- Data is cached to prevent redundant analysis

### 4. Analysis
- **Color analysis**: Extract color patterns using ML techniques
- **Object detection**: Identify objects in album artwork
- **Lyrics analysis**: Extract themes and topics from lyrics
- **Geographical analysis**: Group songs by artist location
- **Temporal analysis**: Analyze release dates and time-related metadata
- **Genre and BPM**: Collect audio features and characteristics

### 5. Playlist Creation
The tool generates playlists based on various attributes:
- **Color**: Songs with similar dominant colors
- **Seasonal**: Songs matching seasonal palettes
- **Time of Day**: Energy-appropriate playlists for different times
- **Mood**: Playlists based on perceived mood
- **Objects**: Songs with common objects in artwork
- **Gradient**: Color gradient-based arrangements
- **Image**: Songs arranged to create visual patterns

## Setup and Installation

*Instructions coming soon*

## Usage

*Instructions coming soon*

## Future Directions
- Implement premium features
- Create a dedicated website interface
- Expand analysis capabilities
- Add social sharing features

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

*License information coming soon*
