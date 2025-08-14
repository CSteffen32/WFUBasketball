#!/usr/bin/env python3
"""
Main script for basketball play-by-play XML parsing.

This script demonstrates how to use the BasketballParser and PlayByPlayProcessor
to extract and analyze basketball game data from XML files.
"""

import os
import sys
import pandas as pd
from basketball_parser import BasketballParser, PlayByPlayProcessor


def main():
    """Main function to demonstrate the basketball parser."""
    
    # Check if XML file path is provided as command line argument
    if len(sys.argv) > 1:
        xml_file_path = sys.argv[1]
    else:
        # Default to looking for XML files in current directory
        xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
        if xml_files:
            xml_file_path = xml_files[0]
            print(f"Using XML file: {xml_file_path}")
        else:
            print("No XML file provided. Please provide the path to your XML file:")
            print("python main.py <path_to_xml_file>")
            print("\nOr place an XML file in the current directory.")
            return
    
    # Check if file exists
    if not os.path.exists(xml_file_path):
        print(f"Error: File '{xml_file_path}' not found.")
        return
    
    try:
        # Initialize and run the parser
        print("Initializing basketball parser...")
        parser = BasketballParser(xml_file_path)
        
        if not parser.parse():
            print("Error: Failed to parse XML file.")
            return
        
        print("XML parsing completed successfully!")
        
        # Initialize the processor
        print("Processing play-by-play data...")
        processor = PlayByPlayProcessor(parser)
        
        # Process all data
        results = processor.process_all()
        
        # Display results
        print("\n" + "="*50)
        print("PARSING RESULTS")
        print("="*50)
        
        # Game information
        print(f"\nGame Information:")
        for key, value in results['game_info'].items():
            print(f"  {key}: {value}")
        
        # Teams
        print(f"\nTeams ({len(results['teams'])}):")
        for team_id, team_info in results['teams'].items():
            print(f"  {team_id}: {team_info['name']} ({team_info['code']})")
        
        # Starting Lineups
        if 'starting_lineups' in results:
            print(f"\nStarting Lineups:")
            home_team_name = results['game_info'].get('home_team', 'Home Team')
            away_team_name = results['game_info'].get('away_team', 'Away Team')
            
            print(f"  {home_team_name} (Home):")
            for player in results['starting_lineups']['home']:
                print(f"    #{player.get('jersey', 'N/A')} {player.get('player_name', 'Unknown')} - {player.get('position', 'N/A')}")
            
            print(f"  {away_team_name} (Away):")
            for player in results['starting_lineups']['away']:
                print(f"    #{player.get('jersey', 'N/A')} {player.get('player_name', 'Unknown')} - {player.get('position', 'N/A')}")
        
        # Players
        print(f"\nPlayers ({len(results['players'])}):")
        for player_id, player_info in results['players'].items():
            print(f"  {player_id}: {player_info['name']} (#{player_info['jersey']}) - {player_info['position']}")
        
        # Plays
        plays_df = results['plays']
        print(f"\nPlays DataFrame ({len(plays_df)} rows):")
        print(f"Columns: {list(plays_df.columns)}")
        if len(plays_df) > 0:
            print("\nFirst 5 plays:")
            print(plays_df.head().to_string())
        
        # Player stats - Box Score
        player_stats_df = results['player_stats']
        print(f"\nPlayer Stats DataFrame ({len(player_stats_df)} rows):")
        if len(player_stats_df) > 0:
            print("\n=== BOX SCORE ===")
            
            # Display box score for each team
            for team_id, team_info in results['teams'].items():
                team_players = player_stats_df[player_stats_df['team_id'] == team_id].copy()
                if len(team_players) > 0:
                    print(f"\n{team_info['name']} ({team_info['code']}):")
                    print("-" * 80)
                    
                    # Sort by minutes played (descending) and then by points
                    team_players = team_players.sort_values(['minutes_played', 'points'], ascending=[False, False])
                    
                    # Display header
                    print(f"{'Player':<20} {'Min':<4} {'FG':<6} {'3PT':<6} {'FT':<6} {'PTS':<4} {'REB':<4} {'AST':<4} {'STL':<4} {'TO':<4}")
                    print("-" * 80)
                    
                    for _, player in team_players.iterrows():
                        if player['minutes_played'] > 0 and player['player_name'].lower() != 'team':  # Only show actual players
                            # Get player name, fallback to player_id if name is missing
                            player_name = player['player_name'] if player['player_name'] else player['player_id']
                            fg_str = f"{player['field_goals_made']}-{player['field_goals_attempted']}"
                            three_pt_str = f"{player['three_points_made']}-{player['three_points_attempted']}"
                            ft_str = f"{player['free_throws_made']}-{player['free_throws_attempted']}"
                            
                            print(f"{player_name:<20} {player['minutes_played']:<4.1f} {fg_str:<6} {three_pt_str:<6} {ft_str:<6} {player['points']:<4} {player['rebounds']:<4} {player['assists']:<4} {player['steals']:<4} {player['turnovers']:<4}")
                    
                    # Team totals (excluding team events)
                    actual_players = team_players[team_players['player_name'].str.lower() != 'team']
                    team_totals = actual_players.sum(numeric_only=True)
                    print("-" * 80)
                    fg_totals = f"{team_totals['field_goals_made']:.0f}-{team_totals['field_goals_attempted']:.0f}"
                    three_pt_totals = f"{team_totals['three_points_made']:.0f}-{team_totals['three_points_attempted']:.0f}"
                    ft_totals = f"{team_totals['free_throws_made']:.0f}-{team_totals['free_throws_attempted']:.0f}"
                    
                    print(f"{'TEAM TOTALS':<20} {'':<4} {fg_totals:<6} {three_pt_totals:<6} {ft_totals:<6} {team_totals['points']:<4} {team_totals['rebounds']:<4} {team_totals['assists']:<4} {team_totals['steals']:<4} {team_totals['turnovers']:<4}")
                    print()
        
        # Team stats
        team_stats_df = results['team_stats']
        print(f"\nTeam Stats DataFrame ({len(team_stats_df)} rows):")
        if len(team_stats_df) > 0:
            print(team_stats_df[['team_name', 'points', 'field_goals_made', 'field_goals_attempted', 'rebounds', 'assists']].to_string(index=False))
        
        # Lineups
        lineup_df = results['lineups']
        print(f"\nLineup DataFrame ({len(lineup_df)} rows):")
        if len(lineup_df) > 0:
            print("\nSample lineup data:")
            print(lineup_df.head().to_string())
        
        # Enhanced Play-by-Play
        enhanced_play_by_play_df = results['enhanced_play_by_play']
        print(f"\nEnhanced Play-by-Play DataFrame ({len(enhanced_play_by_play_df)} rows):")
        if len(enhanced_play_by_play_df) > 0:
            print("\nSample enhanced play-by-play data:")
            print(enhanced_play_by_play_df.head().to_string())
        
        # Save results to CSV files
        print("\n" + "="*50)
        print("SAVING RESULTS")
        print("="*50)
        
        output_dir = "basketball_analysis_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save DataFrames
        if len(plays_df) > 0:
            plays_df.to_csv(f"{output_dir}/plays.csv", index=False)
            print(f"Saved plays data to {output_dir}/plays.csv")
        
        if len(player_stats_df) > 0:
            player_stats_df.to_csv(f"{output_dir}/player_stats.csv", index=False)
            print(f"Saved player stats to {output_dir}/player_stats.csv")
        
        if len(team_stats_df) > 0:
            team_stats_df.to_csv(f"{output_dir}/team_stats.csv", index=False)
            print(f"Saved team stats to {output_dir}/team_stats.csv")
        
        if len(lineup_df) > 0:
            lineup_df.to_csv(f"{output_dir}/lineups.csv", index=False)
            print(f"Saved lineup data to {output_dir}/lineups.csv")
        
        if len(enhanced_play_by_play_df) > 0:
            enhanced_play_by_play_df.to_csv(f"{output_dir}/enhanced_play_by_play.csv", index=False)
            print(f"Saved enhanced play-by-play data to {output_dir}/enhanced_play_by_play.csv")
        
        # Save box score as a separate CSV
        if len(player_stats_df) > 0:
            # Create a clean box score DataFrame
            box_score_df = player_stats_df[player_stats_df['minutes_played'] > 0].copy()
            box_score_df = box_score_df.sort_values(['team_name', 'minutes_played'], ascending=[True, False])
            
            # Select relevant columns for box score
            box_score_columns = [
                'player_name', 'team_name', 'jersey', 'position', 'minutes_played',
                'points', 'field_goals_made', 'field_goals_attempted', 'field_goal_percentage',
                'three_points_made', 'three_points_attempted', 'three_point_percentage',
                'free_throws_made', 'free_throws_attempted', 'free_throw_percentage',
                'rebounds', 'offensive_rebounds', 'defensive_rebounds',
                'assists', 'steals', 'blocks', 'turnovers', 'fouls'
            ]
            
            box_score_df = box_score_df[box_score_columns]
            box_score_df.to_csv(f"{output_dir}/box_score.csv", index=False)
            print(f"Saved box score to {output_dir}/box_score.csv")
        
        print(f"\nAll results saved to '{output_dir}' directory.")
        
        # Return the results for further analysis
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_game_data(results):
    """
    Perform additional analysis on the parsed game data.
    
    Args:
        results (dict): Results from the PlayByPlayProcessor
    """
    if not results:
        print("No data to analyze.")
        return
    
    print("\n" + "="*50)
    print("ADDITIONAL ANALYSIS")
    print("="*50)
    
    plays_df = results['plays']
    player_stats_df = results['player_stats']
    team_stats_df = results['team_stats']
    
    if len(plays_df) == 0:
        print("No plays data available for analysis.")
        return
    
    # Game flow analysis
    print("\nGame Flow Analysis:")
    periods = plays_df['period'].unique()
    print(f"Number of periods: {len(periods)}")
    
    for period in sorted(periods):
        period_plays = plays_df[plays_df['period'] == period]
        print(f"Period {period}: {len(period_plays)} plays")
    
    # Scoring analysis
    print("\nScoring Analysis:")
    scoring_plays = plays_df[plays_df['points'] > 0]
    print(f"Total scoring plays: {len(scoring_plays)}")
    print(f"Total points scored: {scoring_plays['points'].sum()}")
    
    # Event type distribution
    print("\nEvent Type Distribution:")
    event_counts = plays_df['event_type'].value_counts()
    print(event_counts.head(10))
    
    # Player performance analysis
    if len(player_stats_df) > 0:
        print("\nPlayer Performance Analysis:")
        
        # Most efficient scorers (minimum 5 attempts)
        efficient_scorers = player_stats_df[player_stats_df['field_goals_attempted'] >= 5].copy()
        if len(efficient_scorers) > 0:
            efficient_scorers['efficiency'] = efficient_scorers['points'] / efficient_scorers['field_goals_attempted']
            top_efficient = efficient_scorers.nlargest(5, 'efficiency')[['player_name', 'team_name', 'efficiency', 'points', 'field_goals_attempted']]
            print("\nMost efficient scorers (min 5 attempts):")
            print(top_efficient.to_string(index=False))
        
        # Triple-double candidates
        triple_double_candidates = player_stats_df[
            (player_stats_df['points'] >= 10) & 
            (player_stats_df['rebounds'] >= 10) & 
            (player_stats_df['assists'] >= 10)
        ]
        if len(triple_double_candidates) > 0:
            print("\nTriple-double candidates:")
            print(triple_double_candidates[['player_name', 'team_name', 'points', 'rebounds', 'assists']].to_string(index=False))


if __name__ == "__main__":
    # Run the main parser
    results = main()
    
    # Perform additional analysis if data is available
    if results:
        analyze_game_data(results) 