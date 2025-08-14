#!/usr/bin/env python3
"""
Display Enhanced Play-by-Play Table

This script reads the enhanced play-by-play CSV file and displays it
in a nicely formatted table showing all plays with complete information.
"""

import pandas as pd
import sys
import os

def filter_and_clean_lineups(df):
    """
    Filter out substitution plays and clean up lineup data.
    
    Args:
        df (pd.DataFrame): The enhanced play-by-play DataFrame
        
    Returns:
        pd.DataFrame: Filtered DataFrame with cleaned lineups
    """
    # Filter out substitution plays
    filtered_df = df[df['event_type'] != 'substitution'].copy()
    
    # Clean up lineup data to show only 5 players per team
    for index, row in filtered_df.iterrows():
        # Clean home lineup (Wake Forest)
        home_lineup = row['home_lineup']
        if isinstance(home_lineup, str):
            # Split by comma and take first 5 players
            home_players = [p.strip() for p in home_lineup.split(',') if p.strip()]
            # Remove duplicates and take first 5
            unique_home_players = []
            for player in home_players:
                if player not in unique_home_players and len(unique_home_players) < 5:
                    unique_home_players.append(player)
            filtered_df.at[index, 'home_lineup'] = ', '.join(unique_home_players)
        
        # Clean away lineup (Michigan)
        away_lineup = row['away_lineup']
        if isinstance(away_lineup, str):
            # Split by comma and take first 5 players
            away_players = [p.strip() for p in away_lineup.split(',') if p.strip()]
            # Remove duplicates and take first 5
            unique_away_players = []
            for player in away_players:
                if player not in unique_away_players and len(unique_away_players) < 5:
                    unique_away_players.append(player)
            filtered_df.at[index, 'away_lineup'] = ', '.join(unique_away_players)
    
    return filtered_df

def display_enhanced_play_by_play_table(csv_file_path="basketball_analysis_output/enhanced_play_by_play.csv"):
    """
    Display the complete enhanced play-by-play data in a table format.
    
    Args:
        csv_file_path (str): Path to the enhanced play-by-play CSV file
    """
    
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found.")
        print("Please run the main parser first to generate the enhanced play-by-play data.")
        return
    
    try:
        # Read the enhanced play-by-play CSV
        df = pd.read_csv(csv_file_path)
        
        if len(df) == 0:
            print("No play-by-play data found.")
            return
        
        # Filter out substitutions and clean lineups
        filtered_df = filter_and_clean_lineups(df)
        
        print("=" * 120)
        print("ENHANCED PLAY-BY-PLAY TABLE (EXCLUDING SUBSTITUTIONS)")
        print("=" * 120)
        print(f"Total Plays: {len(filtered_df)} (filtered from {len(df)} total plays)")
        print("=" * 120)
        
        # Display each play in a formatted table
        for index, row in filtered_df.iterrows():
            play_num = index + 1
            
            # Format the play information
            print(f"\nPlay #{play_num:3d} | {row['game_clock']}")
            print("-" * 120)
            print(f"Event: {row['event_description']}")
            print(f"Team: {row['team']} | Player: {row['player']}")
            
            if pd.notna(row['points']) and row['points'] > 0:
                print(f"Points: {row['points']}")
            
            if pd.notna(row['home_score']) and pd.notna(row['away_score']):
                print(f"Score: {row['away_score']} - {row['home_score']}")
            
            print(f"\nWake Forest (Home): {row['home_lineup']}")
            print(f"Michigan (Away): {row['away_lineup']}")
            
            # Add additional details if available
            details = []
            if pd.notna(row['assist_player']) and row['assist_player']:
                details.append(f"Assist: {row['assist_player']}")
            if pd.notna(row['rebound_type']) and row['rebound_type']:
                details.append(f"Rebound Type: {row['rebound_type']}")
            if pd.notna(row['foul_type']) and row['foul_type']:
                details.append(f"Foul Type: {row['foul_type']}")
            if pd.notna(row['foul_player']) and row['foul_player']:
                details.append(f"Foul Player: {row['foul_player']}")
            
            if details:
                print(f"Additional Details: {' | '.join(details)}")
            
            print("-" * 120)
        
        print(f"\nEnd of Play-by-Play Data ({len(filtered_df)} plays, substitutions excluded)")
        print("=" * 120)
        
    except Exception as e:
        print(f"Error reading or displaying the data: {e}")
        import traceback
        traceback.print_exc()

def display_compact_table(csv_file_path="basketball_analysis_output/enhanced_play_by_play.csv"):
    """
    Display a more compact table format for easier reading.
    
    Args:
        csv_file_path (str): Path to the enhanced play-by-play CSV file
    """
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found.")
        return
    
    try:
        df = pd.read_csv(csv_file_path)
        
        if len(df) == 0:
            print("No play-by-play data found.")
            return
        
        # Filter out substitutions and clean lineups
        filtered_df = filter_and_clean_lineups(df)
        
        print("=" * 140)
        print("COMPACT PLAY-BY-PLAY TABLE (EXCLUDING SUBSTITUTIONS)")
        print("=" * 140)
        print(f"Total Plays: {len(filtered_df)} (filtered from {len(df)} total plays)")
        print("=" * 140)
        
        # Create a more compact display
        for index, row in filtered_df.iterrows():
            play_num = index + 1
            
            # Format time info
            time_info = f"{row['game_clock']}"
            
            # Format score if available
            score_info = ""
            if pd.notna(row['home_score']) and pd.notna(row['away_score']):
                score_info = f"({row['away_score']}-{row['home_score']})"
            
            # Format lineup info (truncated for compact display)
            home_lineup = row['home_lineup'][:50] + "..." if len(row['home_lineup']) > 50 else row['home_lineup']
            away_lineup = row['away_lineup'][:50] + "..." if len(row['away_lineup']) > 50 else row['away_lineup']
            
            print(f"{play_num:3d} | {time_info:25s} | {score_info:10s} | {row['team']:12s} | {row['player']:20s} | {row['event_description']}")
            
            # Show lineups on separate line for first few plays or when they change significantly
            if index < 10 or index % 50 == 0:
                print(f"     | Wake Forest: {home_lineup}")
                print(f"     | Michigan: {away_lineup}")
                print("-" * 140)
        
        print(f"\nEnd of Play-by-Play Data ({len(filtered_df)} plays, substitutions excluded)")
        print("=" * 140)
        
    except Exception as e:
        print(f"Error reading or displaying the data: {e}")

def main():
    """Main function to run the display script."""
    
    # Check command line arguments for different display modes
    if len(sys.argv) > 1:
        if sys.argv[1] == "--compact":
            display_compact_table()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python3 display_play_by_play.py          # Full detailed table (no substitutions)")
            print("  python3 display_play_by_play.py --compact # Compact table (no substitutions)")
            print("  python3 display_play_by_play.py --help    # Show this help")
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        # Default to full detailed table
        display_enhanced_play_by_play_table()

if __name__ == "__main__":
    main() 