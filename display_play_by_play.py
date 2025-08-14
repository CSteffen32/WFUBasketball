#!/usr/bin/env python3
"""
Display Enhanced Play-by-Play Table

This script reads the enhanced play-by-play CSV file and displays it
in a nicely formatted table showing all plays with complete information.
"""

import pandas as pd
import sys
import os

def get_team_names_from_data(df):
    """
    Determine home and away team names from the data.
    Returns tuple of (home_team_name, away_team_name)
    """
    # Look at the first few rows to determine team names
    home_team_name = "Home Team"
    away_team_name = "Away Team"
    
    # Get unique teams from the data
    unique_teams = df['team'].dropna().unique()
    
    if len(unique_teams) >= 2:
        # For this dataset, we know the pattern - but in general, we'd need to determine
        # which team is home vs away from the data structure
        # This is a simple heuristic - in a real implementation, you might want to
        # read this from game metadata or configuration
        
        # Check if we have the expected teams
        teams_list = [str(team) for team in unique_teams]
        
        # Simple logic for this dataset - can be made more robust
        if 'Wake Forest' in teams_list:
            home_team_name = 'Wake Forest'
        if 'Michigan' in teams_list:
            away_team_name = 'Michigan'
    
    return home_team_name, away_team_name

def filter_and_clean_lineups(df):
    """
    Filter out substitution plays and clean lineup data.
    Returns filtered DataFrame with only non-substitution plays.
    """
    # Filter out substitution events
    filtered_df = df[~df['event_type'].str.contains('substitution', case=False, na=False)]
    
    # Clean lineup strings - take first 5 unique players
    def clean_lineup(lineup_str):
        if pd.isna(lineup_str) or lineup_str == '':
            return ''
        
        # Split by comma and clean up
        players = [p.strip() for p in lineup_str.split(',') if p.strip()]
        
        # Take first 5 unique players
        unique_players = []
        seen = set()
        for player in players:
            if player not in seen and len(unique_players) < 5:
                unique_players.append(player)
                seen.add(player)
        
        return ', '.join(unique_players)
    
    # Apply cleaning to lineup columns
    filtered_df['home_lineup'] = filtered_df['home_lineup'].apply(clean_lineup)
    filtered_df['away_lineup'] = filtered_df['away_lineup'].apply(clean_lineup)
    
    return filtered_df

def display_enhanced_play_by_play_table(csv_file='basketball_analysis_output/enhanced_play_by_play.csv'):
    """
    Display the enhanced play-by-play data in a formatted table.
    """
    try:
        # Read the enhanced play-by-play CSV
        df = pd.read_csv(csv_file)
        
        # Get team names from the data
        home_team_name, away_team_name = get_team_names_from_data(df)
        
        # Filter out substitutions and clean lineups
        filtered_df = filter_and_clean_lineups(df)
        
        print("=" * 120)
        print("ENHANCED PLAY-BY-PLAY TABLE (EXCLUDING SUBSTITUTIONS)")
        print("=" * 120)
        print(f"Total Plays: {len(filtered_df)} (filtered from {len(df)} total plays)")
        print("=" * 120)
        
        # Display each play
        for index, row in filtered_df.iterrows():
            play_num = index + 1
            
            # Format the play information
            print(f"\nPlay #{play_num:3d} | {row['game_clock']}")
            print("-" * 120)
            
            # Event description
            print(f"Event: {row['event_description']}")
            
            # Team and player info
            if pd.notna(row['team']) and row['team'] != '':
                print(f"Team: {row['team']} | Player: {row['player']}")
            
            # Points and score (if applicable)
            if pd.notna(row['points']) and row['points'] != 0:
                print(f"Points: {row['points']}")
                if pd.notna(row['home_score']) and pd.notna(row['away_score']):
                    print(f"Score: {row['home_score']} - {row['away_score']}")
            
            # Lineups
            print(f"{home_team_name} (Home): {row['home_lineup']}")
            print(f"{away_team_name} (Away): {row['away_lineup']}")
            
            # Additional details for specific event types
            additional_details = []
            event_type = row.get('event_type', '').lower()
            
            # Only show relevant details based on event type
            if 'assist' in event_type or 'shot' in event_type:
                if pd.notna(row['assist_player']) and row['assist_player'] != '':
                    additional_details.append(f"Assist: {row['assist_player']}")
            
            if 'rebound' in event_type:
                if pd.notna(row['rebound_type']) and row['rebound_type'] != '':
                    additional_details.append(f"Rebound Type: {row['rebound_type']}")
            
            if 'foul' in event_type:
                if pd.notna(row['foul_type']) and row['foul_type'] != '':
                    additional_details.append(f"Foul Type: {row['foul_type']}")
                if pd.notna(row['foul_player']) and row['foul_player'] != '':
                    additional_details.append(f"Foul On: {row['foul_player']}")
            
            if 'shot' in event_type:
                if pd.notna(row['shot_type']) and row['shot_type'] != '':
                    additional_details.append(f"Shot Type: {row['shot_type']}")
            
            if additional_details:
                print("Additional Details: " + " | ".join(additional_details))
            
            print("-" * 120)
        
        print("End of Play-by-Play Data ({} plays, substitutions excluded)".format(len(filtered_df)))
        print("=" * 120)
        
    except FileNotFoundError:
        print(f"Error: Could not find the enhanced play-by-play CSV file: {csv_file}")
        print("Please run 'python3 main.py example.XML' first to generate the data.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or processing the CSV file: {e}")
        sys.exit(1)

def display_compact_table(csv_file='basketball_analysis_output/enhanced_play_by_play.csv', max_plays=20):
    """
    Display a compact version of the play-by-play table.
    """
    try:
        df = pd.read_csv(csv_file)
        
        # Get team names from the data
        home_team_name, away_team_name = get_team_names_from_data(df)
        
        filtered_df = filter_and_clean_lineups(df)
        
        print("=" * 120)
        print("COMPACT PLAY-BY-PLAY TABLE (First {} plays, excluding substitutions)".format(max_plays))
        print("=" * 120)
        
        # Display header
        print(f"{'Play':<6} {'Time':<8} {'Event':<50} {'Score':<12} {'Home Lineup':<30} {'Away Lineup':<30}")
        print("-" * 120)
        
        # Display plays
        for index, row in filtered_df.head(max_plays).iterrows():
            play_num = index + 1
            
            # Format time info
            time_info = f"{row['game_clock']}"
            
            # Truncate event description
            event = row['event_description'][:48] + "..." if len(row['event_description']) > 50 else row['event_description']
            
            # Format score
            if pd.notna(row['home_score']) and pd.notna(row['away_score']):
                score = f"{row['home_score']}-{row['away_score']}"
            else:
                score = ""
            
            # Truncate lineups
            home_lineup = row['home_lineup'][:28] + "..." if len(row['home_lineup']) > 30 else row['home_lineup']
            away_lineup = row['away_lineup'][:28] + "..." if len(row['away_lineup']) > 30 else row['away_lineup']
            
            print(f"{play_num:<6} {time_info:<8} {event:<50} {score:<12} {home_lineup:<30} {away_lineup:<30}")
        
        print("=" * 120)
        
    except FileNotFoundError:
        print(f"Error: Could not find the enhanced play-by-play CSV file: {csv_file}")
        print("Please run 'python3 main.py example.XML' first to generate the data.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading or processing the CSV file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if command line argument is provided
    if len(sys.argv) > 1:
        if sys.argv[1] == "--compact":
            max_plays = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            display_compact_table(max_plays=max_plays)
        else:
            print("Usage: python3 display_play_by_play.py [--compact [max_plays]]")
            print("  --compact: Display compact table format")
            print("  max_plays: Number of plays to display (default: 20)")
    else:
        # Default: display full table
        display_enhanced_play_by_play_table() 