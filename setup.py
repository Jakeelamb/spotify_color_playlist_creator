# setup.py
from setuptools import setup, find_packages

setup(
    name="spotify_color_playlist_creator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "spotipy",
        "numpy",
        "pillow",
        "scikit-learn",
        "tqdm",
        "questionary",
        "requests",
        "colorthief",
    ],
    extras_require={
        "object_detection": ["ultralytics"],
        "lyrics": ["lyricsgenius", "nltk", "textblob"],
        "all": ["ultralytics", "lyricsgenius", "nltk", "textblob"]
    },
    entry_points={
        "console_scripts": [
            "spotify-playlists=spotify_playlist_creator.cli:main",
        ],
    },
)