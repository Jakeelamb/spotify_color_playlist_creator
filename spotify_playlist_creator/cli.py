"""Command Line Interface for Spotify Color Playlist Creator."""

import argparse
import questionary
import os
from spotify_playlist_creator.spotify import auth, scraper
from spotify_playlist_creator.analysis import color_analysis, object_detection, lyrics_analysis, audio_features
from spotify_playlist_creator.playlists import color, gradient, mood, time_of_day, objects, lyrics, audio_features as audio_playlists
from spotify_playlist_creator import config

def select_music_source(sp):
    """Let user select where to get tracks from (liked songs or a playlist)."""
    while True:
        source_type = questionary.select(
            "Where would you like to get tracks from?",
            choices=[
                "My Liked Songs",
                "One of my playlists",
                "Someone else's playlist (enter URL)",
                "Exit"
            ]
        ).ask()
        
        if source_type == "Exit":
            return None
        
        if source_type == "My Liked Songs":
            confirm = questionary.confirm("Use your Liked Songs?").ask()
            if confirm:
                return {"type": "liked_songs"}
            # If not confirmed, loop back to the main menu
        
        elif source_type == "One of my playlists":
            # Fetch user's playlists
            print("Fetching your playlists...")
            playlists = sp.current_user_playlists()
            
            if not playlists or playlists['total'] == 0:
                print("No playlists found.")
                continue
            
            # Create a list of choices for the user
            playlist_choices = [
                f"{p['name']} ({p['tracks']['total']} tracks)" 
                for p in playlists['items']
            ]
            
            # Add a 'Go back' option
            playlist_choices.append("Go back")
            
            # Let user select a playlist
            selected = questionary.select(
                "Choose a playlist:",
                choices=playlist_choices
            ).ask()
            
            if selected == "Go back":
                continue
            
            # Find the selected playlist's index
            selected_idx = playlist_choices.index(selected)
            # Make sure it's a valid index (not the "Go back" option)
            if selected_idx < len(playlists['items']):
                selected_playlist = playlists['items'][selected_idx]
                
                # Confirm selection
                confirm = questionary.confirm(
                    f"Use '{selected_playlist['name']}' playlist?"
                ).ask()
                
                if confirm:
                    return {
                        "type": "playlist",
                        "id": selected_playlist['id'],
                        "name": selected_playlist['name']
                    }
            
        elif source_type == "Someone else's playlist (enter URL)":
            while True:
                playlist_url = questionary.text(
                    "Enter the Spotify playlist URL or URI (or type 'back' to return):"
                ).ask()
                
                if playlist_url.lower() == 'back':
                    break
                
                # Extract playlist ID from URL/URI
                if "spotify.com/playlist/" in playlist_url:
                    playlist_id = playlist_url.split("spotify.com/playlist/")[1].split("?")[0]
                elif "spotify:playlist:" in playlist_url:
                    playlist_id = playlist_url.split("spotify:playlist:")[1]
                else:
                    print("Invalid playlist URL or URI. Please try again or type 'back'.")
                    continue
                    
                # Verify the playlist exists
                try:
                    playlist_info = sp.playlist(playlist_id, fields="name,id")
                    
                    # Confirm selection
                    confirm = questionary.confirm(
                        f"Use '{playlist_info['name']}' playlist?"
                    ).ask()
                    
                    if confirm:
                        return {
                            "type": "playlist",
                            "id": playlist_id,
                            "name": playlist_info['name']
                        }
                except Exception as e:
                    print(f"Error accessing playlist: {e}")
                    print("Please try again or type 'back'.")

def analyze_tracks(tracks, sp, force_reanalyze=False):
    """Run all analysis on the tracks and return results."""
    print(f"\nAnalyzing {len(tracks)} tracks...")
    
    # Start with an empty results dictionary
    analysis_results = {}
    
    # 1. Color analysis
    print("\n🎨 Starting color analysis...")
    analysis_results['color'] = color_analysis.analyze_tracks_colors(
        tracks, force_reanalyze=force_reanalyze
    )
    
    # 2. Object detection (if available)
    if hasattr(object_detection, 'is_available') and object_detection.is_available():
        print("\n🔍 Starting object detection...")
        analysis_results['objects'] = object_detection.analyze_tracks_objects(
            tracks, force_reanalyze=force_reanalyze
        )
    else:
        print("\n🔍 Object detection is not available. Install with: pip install 'spotify-color-playlist-creator[object_detection]'")
        analysis_results['objects'] = {}
    
    # 3. Lyrics analysis (if available and user wants it)
    if hasattr(lyrics_analysis, 'is_available') and lyrics_analysis.is_available():
        run_lyrics = questionary.confirm(
            "Do you want to analyze lyrics? (Slower, requires API calls)",
            default=False
        ).ask()
        
        if run_lyrics:
            # First check if GENIUS_API_TOKEN is set
            if config.GENIUS_API_TOKEN == "YOUR_GENIUS_API_TOKEN":
                print("\n⚠️ Lyrics analysis requires a Genius API token. Please set it in config.py")
            else:
                print("\n📝 Starting lyrics analysis...")
                # First fetch lyrics
                lyrics_data = lyrics_analysis.fetch_and_cache_lyrics(
                    tracks, force_refetch=force_reanalyze
                )
                
                # Then analyze them
                analysis_results['lyrics'] = lyrics_analysis.analyze_tracks_lyrics(
                    tracks, lyrics_data
                )
    else:
        print("\n📝 Lyrics analysis is not available. Install with: pip install 'spotify-color-playlist-creator[lyrics]'")
        analysis_results['lyrics'] = {}
    
    print("\nAnalysis complete!")
    return analysis_results

def create_interactive_menu():
    """Interactive menu for users to customize playlist creation."""
    while True:
        # Build choices based on available features
        choices = [
            "Create color-based playlists",
            "Create a rainbow gradient playlist",
            "Create a mood-based playlist",
            "Create audio feature playlists"
        ]
        
        # Add object detection if available
        if hasattr(object_detection, 'is_available') and object_detection.is_available():
            choices.append("Create object-based playlists")
            
        # Add lyrics analysis if available
        if hasattr(lyrics_analysis, 'is_available') and lyrics_analysis.is_available():
            choices.append("Create mood playlists from lyrics")
            
        # Add navigation options
        choices.extend([
            "Go back to music source selection",
            "Exit"
        ])
        
        # Show menu
        action = questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask()
        
        if action == "Exit":
            return {"action": "exit"}
            
        if action == "Go back to music source selection":
            return {"action": "back_to_source"}
        
        if action == "Create color-based playlists":
            # Configuration options
            min_tracks = questionary.text("Minimum tracks per playlist?", default="3").ask()
            prefix = questionary.text("Playlist name prefix?", default="Colorful Tunes -").ask()
            is_public = questionary.confirm("Make playlists public?", default=True).ask()
            
            # Confirm settings
            print(f"\nSettings review:")
            print(f"- Minimum tracks per playlist: {min_tracks}")
            print(f"- Playlist name prefix: '{prefix}'")
            print(f"- Public playlists: {'Yes' if is_public else 'No'}")
            
            confirm = questionary.confirm("Proceed with these settings?", default=True).ask()
            if confirm:
                return {
                    "action": "color_playlists",
                    "min_tracks": int(min_tracks),
                    "prefix": prefix,
                    "public": is_public
                }
            # If not confirmed, loop back to main menu
        
        elif action == "Create a rainbow gradient playlist":
            name = questionary.text("Playlist name?", default="Rainbow Gradient").ask()
            max_tracks = questionary.text("Maximum number of tracks?", default="100").ask()
            
            # Confirm settings
            confirm = questionary.confirm(
                f"Create '{name}' playlist with up to {max_tracks} tracks?", 
                default=True
            ).ask()
            
            if confirm:
                return {
                    "action": "rainbow",
                    "name": name,
                    "max_tracks": int(max_tracks)
                }
        
        elif action == "Create a mood-based playlist":
            mood_choices = ["energetic", "calm", "happy", "melancholic", "focused", "Go back"]
            mood = questionary.select(
                "Select a mood:",
                choices=mood_choices
            ).ask()
            
            if mood == "Go back":
                continue
                
            confirm = questionary.confirm(f"Create a '{mood}' mood playlist?", default=True).ask()
            if confirm:
                return {
                    "action": "mood",
                    "mood": mood
                }
        
        elif action == "Create audio feature playlists":
            return {
                "action": "audio_features"
            }
        
        elif action == "Create object-based playlists":
            min_tracks = questionary.text(
                "Minimum tracks per playlist?", 
                default="3"
            ).ask()
            
            # Simplified prompt since the detailed selection will happen later
            return {
                "action": "object_playlists",
                "min_tracks": int(min_tracks)
            }
        
        elif action == "Create mood playlists from lyrics":
            confirm = questionary.confirm(
                "Create playlists based on lyrical mood analysis?", 
                default=True
            ).ask()
            
            if confirm:
                return {
                    "action": "mood_playlists"
                }

def main():
    """Main function to run the color playlist creator."""
    parser = argparse.ArgumentParser(description='Spotify Color Playlist Creator')
    parser.add_argument('--reanalyze', action='store_true', 
                        help='Force re-analysis of all tracks, ignoring the cache')
    
    args = parser.parse_args()
    
    print("Starting Spotify Color Playlist Creator")
    
    # Authenticate with Spotify
    sp = auth.authenticate_spotify()
    
    while True:
        # Select music source (liked songs or a playlist)
        music_source = select_music_source(sp)
        
        if not music_source:
            print("Exiting program.")
            return
        
        # Fetch tracks based on the selected source
        if music_source["type"] == "liked_songs":
            print("Fetching your liked songs...")
            tracks = scraper.get_user_liked_songs(sp, use_cache=not args.reanalyze)
        else:
            print(f"Fetching tracks from playlist: {music_source['name']}")
            tracks = scraper.get_playlist_tracks(sp, music_source['id'], use_cache=not args.reanalyze)
        
        if not tracks:
            print("No tracks found. Please choose another source.")
            continue
            
        # Automatically run all analysis steps
        print(f"\nAnalyzing {len(tracks)} tracks...")
        analysis_results = analyze_tracks(tracks, sp, force_reanalyze=args.reanalyze)
        
        # Get user preferences through interactive menu
        options = create_interactive_menu()
        
        if options["action"] == "exit":
            print("Exiting program.")
            return
            
        if options["action"] == "back_to_source":
            print("Going back to music source selection...")
            continue
        
        # Create playlists based on action type
        if options["action"] == "color_playlists":
            created_playlists = color.create_color_playlists(
                sp, 
                tracks, 
                analysis_results['color'], 
                min_tracks=options["min_tracks"],
                prefix=options["prefix"], 
                public=options["public"]
            )
            
            print(f"\nCreated {len(created_playlists)} color-based playlists!")
        
        elif options["action"] == "rainbow":
            # This would be implemented in gradient.py
            print("Rainbow gradient playlist creation is coming soon!")
        
        elif options["action"] == "mood":
            print(f"Mood-based playlist creation for '{options['mood']}' mood is coming soon!")
        
        elif options["action"] == "object_playlists":
            if 'objects' not in analysis_results:
                print("Object detection results not available. Run analysis first.")
            else:
                created_playlists = objects.create_object_playlists(
                    sp,
                    tracks, 
                    analysis_results['objects'],
                    min_tracks=options["min_tracks"]
                )
                print(f"\nCreated {len(created_playlists)} object-based playlists!")
        
        elif options["action"] == "mood_playlists":
            if 'lyrics' not in analysis_results:
                print("Lyrics analysis not available. Run analysis with lyrics first.")
            else:
                created_playlists = lyrics.create_mood_playlists(
                    sp,
                    tracks,
                    analysis_results['lyrics']
                )
                print(f"\nCreated {len(created_playlists)} mood-based playlists!")
        
        elif options["action"] == "audio_features":
            created_playlists = audio_playlists.create_audio_feature_playlists(
                sp,
                tracks
            )
            if created_playlists:
                print(f"\nCreated {len(created_playlists)} audio feature playlists!")
            else:
                print("\nNo audio feature playlists were created.")
        
        # Ask if user wants to continue or exit
        continue_app = questionary.select(
            "What would you like to do next?",
            choices=[
                "Create more playlists with the same tracks",
                "Select a different music source",
                "Exit"
            ]
        ).ask()
        
        if continue_app == "Exit":
            print("Exiting program.")
            return
        elif continue_app == "Select a different music source":
            # Clear the current tracks data to force reloading
            continue
        else:  # User chose "Create more playlists with the same tracks"
            # Skip back to the interactive menu, but keep current tracks and analysis
            options = create_interactive_menu()
            # This will loop back to the options handling block without re-fetching tracks

if __name__ == "__main__":
    main()
