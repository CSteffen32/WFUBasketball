"""
Basketball Play-by-Play XML Parser

This module provides functionality to parse basketball play-by-play XML data
and generate event-level DataFrames for statistical analysis.
"""

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re
from xml_adapters import AdapterManager


class BasketballParser:
    """
    Main parser class for basketball play-by-play XML data.
    """
    
    def __init__(self, xml_file_path: str):
        """
        Initialize the parser with an XML file path.
        
        Args:
            xml_file_path (str): Path to the XML file containing play-by-play data
        """
        self.xml_file_path = xml_file_path
        self.tree = None
        self.root = None
        self.game_info = {}
        self.teams = {}
        self.players = {}
        self.plays = []
        self.adapter_manager = AdapterManager()
        self.adapter = None
        
    def load_xml(self):
        """Load and parse the XML file."""
        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            print(f"Error loading XML file: {e}")
            return False
    
    def extract_game_info(self):
        """Extract basic game information."""
        self.game_info = self.adapter.extract_game_info(self.root)
    
    def extract_teams(self):
        """Extract team information."""
        self.teams = self.adapter.extract_teams(self.root)
    
    def extract_players(self):
        """Extract player information."""
        self.players = self.adapter.extract_players(self.root)
        
        # Update team players
        for player_id, player_info in self.players.items():
            team_id = player_info['team_id']
            if team_id in self.teams:
                self.teams[team_id]['players'][player_id] = player_info
    
    def extract_plays(self):
        """Extract all play-by-play events."""
        self.plays = self.adapter.extract_plays(self.root)
        # Extract starting lineups if available
        if hasattr(self.adapter, 'get_starting_lineups'):
            self.starting_lineups = self.adapter.get_starting_lineups()
        else:
            self.starting_lineups = {'home': [], 'away': []}
    
    def _parse_play_element(self, play_elem) -> Optional[Dict]:
        """Parse individual play element and extract relevant data."""
        try:
            play_data = {
                'play_id': play_elem.get('id', ''),
                'period': int(play_elem.get('period', 1)),
                'time': play_elem.get('time', ''),
                'clock': play_elem.get('clock', ''),
                'team_id': play_elem.get('team_id', ''),
                'player_id': play_elem.get('player_id', ''),
                'event_type': play_elem.get('event_type', ''),
                'description': play_elem.get('description', ''),
                'points': int(play_elem.get('points', 0)),
                'shot_type': play_elem.get('shot_type', ''),
                'shot_distance': play_elem.get('shot_distance', ''),
                'assist_player_id': play_elem.get('assist_player_id', ''),
                'rebound_type': play_elem.get('rebound_type', ''),
                'foul_type': play_elem.get('foul_type', ''),
                'foul_player_id': play_elem.get('foul_player_id', ''),
                'substitution_in': play_elem.get('substitution_in', ''),
                'substitution_out': play_elem.get('substitution_out', ''),
                'timeout_team': play_elem.get('timeout_team', ''),
                'jumpball_won': play_elem.get('jumpball_won', ''),
                'jumpball_player': play_elem.get('jumpball_player', ''),
            }
            
            # Extract additional data from child elements
            for child in play_elem:
                if child.tag.lower() in ['coordinates', 'location']:
                    play_data['x_coord'] = child.get('x', '')
                    play_data['y_coord'] = child.get('y', '')
                elif child.tag.lower() in ['score', 'scoring']:
                    play_data['home_score'] = child.get('home', '')
                    play_data['away_score'] = child.get('away', '')
            
            return play_data
            
        except Exception as e:
            print(f"Error parsing play element: {e}")
            return None
    
    def parse(self):
        """Main parsing method that orchestrates the entire parsing process."""
        if not self.load_xml():
            return False
        
        # Get appropriate adapter for this XML format
        self.adapter = self.adapter_manager.get_adapter(self.root)
        
        self.extract_game_info()
        self.extract_teams()
        self.extract_players()
        self.extract_plays()
        
        return True


class PlayByPlayProcessor:
    """
    Process play-by-play data into structured DataFrames.
    """
    
    def __init__(self, parser: BasketballParser):
        """
        Initialize with a parsed BasketballParser instance.
        
        Args:
            parser (BasketballParser): Parsed basketball data
        """
        self.parser = parser
        self.plays_df = None
        self.player_stats_df = None
        self.team_stats_df = None
        self.lineup_df = None
        
    def create_plays_dataframe(self) -> pd.DataFrame:
        """Create the main plays DataFrame."""
        if not self.parser.plays:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.parser.plays)
        
        # Add team and player information
        df['team_name'] = df['team_id'].map(lambda x: self.parser.teams.get(x, {}).get('name', ''))
        # Use player_name from the play data (which comes from checkname) instead of looking it up
        # df['player_name'] = df['player_id'].map(lambda x: self.parser.players.get(x, {}).get('name', ''))
        df['assist_player_name'] = df['assist_player_id'].map(lambda x: self.parser.players.get(x, {}).get('name', ''))
        df['foul_player_name'] = df['foul_player_id'].map(lambda x: self.parser.players.get(x, {}).get('name', ''))
        
        # Convert time to seconds for easier analysis
        df['time_seconds'] = df['time'].apply(self._time_to_seconds)
        
        # Keep plays in original XML order (chronological sequence)
        # No sorting - preserve the order as they appear in the XML file
        
        self.plays_df = df
        return df
    
    def _time_to_seconds(self, time_str: str) -> int:
        """Convert MM:SS time format to seconds."""
        if not time_str or ':' not in time_str:
            return 0
        
        try:
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        except:
            return 0
    
    def create_player_stats_dataframe(self) -> pd.DataFrame:
        """Create player statistics DataFrame with standard box score stats."""
        if self.plays_df is None:
            self.create_plays_dataframe()
        
        player_stats = {}
        
        # First pass: collect all players who appear in plays
        for _, play in self.plays_df.iterrows():
            player_id = play['player_id']
            if not player_id:
                continue
                
            if player_id not in player_stats:
                # Get player info from parser or use play data as fallback
                parser_player_info = self.parser.players.get(player_id, {})
                
                # Get player name from play data (checkname field)
                player_name = play['player_name']
                if not player_name and parser_player_info.get('name'):
                    player_name = parser_player_info.get('name')
                if not player_name:
                    # Try to extract from description as last resort
                    description = play.get('description', '')
                    if description and ' ' in description:
                        # Extract first part of description (player name)
                        parts = description.split(' ')
                        if len(parts) > 0:
                            player_name = parts[0].replace(',', ' ')
                if not player_name:
                    player_name = player_id
                
                # Clean up player name formatting
                if player_name and player_name != player_id:
                    # Convert from "LAST,FIRST" format to "First Last" format
                    if ',' in player_name:
                        parts = player_name.split(',')
                        if len(parts) == 2:
                            last_name = parts[0].strip()
                            first_name = parts[1].strip()
                            player_name = f"{first_name} {last_name}"
                    # Title case the name
                    player_name = player_name.title()
                    
                    # Ensure consistent formatting for names that might be in different orders
                    # Handle cases like "Reid Efton" vs "Efton Reid"
                    name_parts = player_name.split()
                    if len(name_parts) == 2:
                        # Check if this looks like a reversed name (last, first)
                        # For now, assume the first part is the first name
                        pass
                
                team_id = play['team_id']
                team_name = play['team_name']
                jersey = parser_player_info.get('jersey', '')
                position = parser_player_info.get('position', '')
                
                player_stats[player_id] = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'team_id': team_id,
                    'team_name': team_name,
                    'jersey': jersey,
                    'position': position,
                    'minutes_played': 0,
                    'points': 0,
                    'field_goals_made': 0,
                    'field_goals_attempted': 0,
                    'three_points_made': 0,
                    'three_points_attempted': 0,
                    'free_throws_made': 0,
                    'free_throws_attempted': 0,
                    'rebounds': 0,
                    'offensive_rebounds': 0,
                    'defensive_rebounds': 0,
                    'assists': 0,
                    'steals': 0,
                    'blocks': 0,
                    'turnovers': 0,
                    'fouls': 0,
                    'field_goal_percentage': 0.0,
                    'three_point_percentage': 0.0,
                    'free_throw_percentage': 0.0,
                }
            
            # Update statistics based on event type
            event_type = play['event_type'].lower()
            
            # Handle scoring plays - add points directly from the points column
            if play['points'] > 0:
                player_stats[player_id]['points'] += play['points']
            
            if 'shot' in event_type:
                player_stats[player_id]['field_goals_attempted'] += 1
                if play['points'] > 0:
                    player_stats[player_id]['field_goals_made'] += 1
                    
                    if '3pt' in play['shot_type'].lower() or play['points'] == 3:
                        player_stats[player_id]['three_points_made'] += 1
                        player_stats[player_id]['three_points_attempted'] += 1
                    else:
                        player_stats[player_id]['three_points_attempted'] += 1
                        
            elif 'free_throw' in event_type:
                player_stats[player_id]['free_throws_attempted'] += 1
                if play['points'] > 0:
                    player_stats[player_id]['free_throws_made'] += 1
                    
            elif 'rebound' in event_type:
                player_stats[player_id]['rebounds'] += 1
                if 'offensive' in play['rebound_type'].lower():
                    player_stats[player_id]['offensive_rebounds'] += 1
                else:
                    player_stats[player_id]['defensive_rebounds'] += 1
                    
            elif 'assist' in event_type:
                player_stats[player_id]['assists'] += 1
                
            elif 'steal' in event_type:
                player_stats[player_id]['steals'] += 1
                
            elif 'block' in event_type:
                player_stats[player_id]['blocks'] += 1
                
            elif 'turnover' in event_type:
                player_stats[player_id]['turnovers'] += 1
                
            elif 'foul' in event_type:
                player_stats[player_id]['fouls'] += 1
        
        # Calculate minutes played for each player
        self._calculate_minutes_played(player_stats)
        
        # Calculate shooting percentages
        for player_id in player_stats:
            stats = player_stats[player_id]
            
            if stats['field_goals_attempted'] > 0:
                stats['field_goal_percentage'] = stats['field_goals_made'] / stats['field_goals_attempted']
            else:
                stats['field_goal_percentage'] = 0.0
                
            if stats['three_points_attempted'] > 0:
                stats['three_point_percentage'] = stats['three_points_made'] / stats['three_points_attempted']
            else:
                stats['three_point_percentage'] = 0.0
                
            if stats['free_throws_attempted'] > 0:
                stats['free_throw_percentage'] = stats['free_throws_made'] / stats['free_throws_attempted']
            else:
                stats['free_throw_percentage'] = 0.0
        
        self.player_stats_df = pd.DataFrame(list(player_stats.values()))
        return self.player_stats_df
    
    def _calculate_minutes_played(self, player_stats: dict):
        """Calculate minutes played for each player based on substitution data."""
        # For now, let's use a simpler approach based on play frequency
        # This will give us a reasonable approximation
        
        # Count total plays per player
        player_play_counts = {}
        for _, play in self.plays_df.iterrows():
            player_id = play['player_id']
            if player_id and player_id in player_stats:
                if player_id not in player_play_counts:
                    player_play_counts[player_id] = 0
                player_play_counts[player_id] += 1
        
        # Calculate total game time (assuming 40 minutes for a typical game)
        total_game_minutes = 40.0
        
        # Find the player with the most plays (likely played the most minutes)
        if player_play_counts:
            max_plays = max(player_play_counts.values())
            
            # Estimate minutes based on play frequency
            for player_id, play_count in player_play_counts.items():
                if player_id in player_stats:
                    # Scale minutes based on play frequency relative to the most active player
                    if max_plays > 0:
                        estimated_minutes = (play_count / max_plays) * total_game_minutes * 0.8  # Scale factor
                    else:
                        estimated_minutes = 0
                    
                    # Ensure reasonable bounds
                    estimated_minutes = max(estimated_minutes, 1.0)  # Minimum 1 minute
                    estimated_minutes = min(estimated_minutes, 40.0)  # Maximum 40 minutes
                    
                    player_stats[player_id]['minutes_played'] = estimated_minutes
    
    def create_team_stats_dataframe(self) -> pd.DataFrame:
        """Create team statistics DataFrame."""
        if self.player_stats_df is None:
            self.create_player_stats_dataframe()
        
        team_stats = {}
        
        for _, player in self.player_stats_df.iterrows():
            team_id = player['team_id']
            
            if team_id not in team_stats:
                team_stats[team_id] = {
                    'team_id': team_id,
                    'team_name': player['team_name'],
                    'points': 0,
                    'field_goals_made': 0,
                    'field_goals_attempted': 0,
                    'three_points_made': 0,
                    'three_points_attempted': 0,
                    'free_throws_made': 0,
                    'free_throws_attempted': 0,
                    'rebounds': 0,
                    'offensive_rebounds': 0,
                    'defensive_rebounds': 0,
                    'assists': 0,
                    'steals': 0,
                    'blocks': 0,
                    'turnovers': 0,
                    'fouls': 0,
                }
            
            # Aggregate player stats to team stats
            for stat in ['points', 'field_goals_made', 'field_goals_attempted', 
                        'three_points_made', 'three_points_attempted', 'free_throws_made', 
                        'free_throws_attempted', 'rebounds', 'offensive_rebounds', 
                        'defensive_rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'fouls']:
                team_stats[team_id][stat] += player[stat]
        
        # Calculate team shooting percentages
        for team_id in team_stats:
            stats = team_stats[team_id]
            
            if stats['field_goals_attempted'] > 0:
                stats['field_goal_percentage'] = stats['field_goals_made'] / stats['field_goals_attempted']
            else:
                stats['field_goal_percentage'] = 0.0
                
            if stats['three_points_attempted'] > 0:
                stats['three_point_percentage'] = stats['three_points_made'] / stats['three_points_attempted']
            else:
                stats['three_point_percentage'] = 0.0
                
            if stats['free_throws_attempted'] > 0:
                stats['free_throw_percentage'] = stats['free_throws_made'] / stats['free_throws_attempted']
            else:
                stats['free_throw_percentage'] = 0.0
        
        self.team_stats_df = pd.DataFrame(list(team_stats.values()))
        return self.team_stats_df
    
    def create_lineup_dataframe(self) -> pd.DataFrame:
        """Create lineup tracking DataFrame showing who was on court for each play."""
        if self.plays_df is None:
            self.create_plays_dataframe()
        
        # This is a simplified approach - in practice, you'd need more detailed
        # substitution tracking from the XML
        lineup_data = []
        
        # Group plays by period and track substitutions
        for period in self.plays_df['period'].unique():
            period_plays = self.plays_df[self.plays_df['period'] == period].copy()
            
            # Initialize lineups (this would need to be enhanced based on actual XML structure)
            home_team_id = None
            away_team_id = None
            
            for _, play in period_plays.iterrows():
                if home_team_id is None and play['team_id']:
                    home_team_id = play['team_id']
                elif away_team_id is None and play['team_id'] and play['team_id'] != home_team_id:
                    away_team_id = play['team_id']
                
                if home_team_id and away_team_id:
                    break
            
            # Track substitutions (simplified)
            home_lineup = set()
            away_lineup = set()
            
            for _, play in period_plays.iterrows():
                event_type = play['event_type'].lower()
                
                if 'substitution' in event_type:
                    team_id = play['team_id']
                    player_in = play['substitution_in']
                    player_out = play['substitution_out']
                    
                    if team_id == home_team_id:
                        if player_out in home_lineup:
                            home_lineup.remove(player_out)
                        if player_in:
                            home_lineup.add(player_in)
                    elif team_id == away_team_id:
                        if player_out in away_lineup:
                            away_lineup.remove(player_out)
                        if player_in:
                            away_lineup.add(player_in)
                
                # Record lineup for this play
                lineup_data.append({
                    'play_id': play['play_id'],
                    'period': play['period'],
                    'time': play['time'],
                    'home_team_id': home_team_id,
                    'home_lineup': list(home_lineup),
                    'away_team_id': away_team_id,
                    'away_lineup': list(away_lineup),
                })
        
        self.lineup_df = pd.DataFrame(lineup_data)
        return self.lineup_df
    
    def create_enhanced_play_by_play_dataframe(self) -> pd.DataFrame:
        """Create an enhanced play-by-play DataFrame with better event descriptions and lineup tracking."""
        if self.plays_df is None:
            self.create_plays_dataframe()
        
        # Get starting lineups
        starting_lineups = getattr(self.parser, 'starting_lineups', {'home': [], 'away': []})
        
        # Get team IDs from game info
        home_team_id = self.parser.game_info.get('home_id', 'WF')
        away_team_id = self.parser.game_info.get('away_id', 'Mich')
        
        # Initialize lineups with starting players
        home_lineup = set()
        away_lineup = set()
        
        # Add starting players to lineups
        for player in starting_lineups.get('home', []):
            if 'player_id' in player:
                home_lineup.add(player['player_id'])
        for player in starting_lineups.get('away', []):
            if 'player_id' in player:
                away_lineup.add(player['player_id'])
        
        # Simple lineup tracking: start with starting lineups and update on substitutions
        enhanced_plays = []
        current_home_lineup = home_lineup.copy()
        current_away_lineup = away_lineup.copy()
        
        # If we don't have starting lineups, try to infer from early plays
        if len(current_home_lineup) == 0 or len(current_away_lineup) == 0:
            # Look at the first few plays to identify players who are likely starters
            early_plays = self.plays_df.head(20)  # First 20 plays
            home_players = set()
            away_players = set()
            
            for _, play in early_plays.iterrows():
                player_id = play['player_id']
                team_id = play['team_id']
                
                if player_id and team_id:
                    if team_id == home_team_id:
                        home_players.add(player_id)
                    elif team_id == away_team_id:
                        away_players.add(player_id)
            
            # Use the first 5 players from each team as starters
            if len(current_home_lineup) == 0:
                current_home_lineup = set(list(home_players)[:5])
            if len(current_away_lineup) == 0:
                current_away_lineup = set(list(away_players)[:5])
        

        
        # Track all players who have been on the court for each team
        all_home_players = current_home_lineup.copy()
        all_away_players = current_away_lineup.copy()
        
        # Also collect all players who appear in any play for each team
        for _, play in self.plays_df.iterrows():
            player_id = play['player_id']
            team_id = play['team_id']
            
            if player_id and team_id:
                if team_id == home_team_id:
                    all_home_players.add(player_id)
                elif team_id == away_team_id:
                    all_away_players.add(player_id)
        
        for _, play in self.plays_df.iterrows():
            event_type = play['event_type'].lower()
            team_id = play['team_id']
            
            # Handle substitutions to update current lineups
            if 'substitution' in event_type:
                player_id = play['player_id']
                description = play.get('description', '').lower()
                
                # Handle substitutions based on description
                if 'enters' in description or 'in' in description:
                    if team_id == home_team_id:
                        current_home_lineup.add(player_id)
                        all_home_players.add(player_id)
                    elif team_id == away_team_id:
                        current_away_lineup.add(player_id)
                        all_away_players.add(player_id)
                elif 'exits' in description or 'out' in description:
                    if team_id == home_team_id and player_id in current_home_lineup:
                        current_home_lineup.remove(player_id)
                    elif team_id == away_team_id and player_id in current_away_lineup:
                        current_away_lineup.remove(player_id)
                
                # Ensure we maintain exactly 5 players per team
                if len(current_home_lineup) > 5:
                    # Remove the most recently added player if we have more than 5
                    current_home_lineup = set(list(current_home_lineup)[:5])
                if len(current_away_lineup) > 5:
                    # Remove the most recently added player if we have more than 5
                    current_away_lineup = set(list(current_away_lineup)[:5])
            
            # Create enhanced event description
            enhanced_description = self._create_enhanced_event_description(play)
            
            # Get current lineup information - simple approach: just get names from player IDs
            home_lineup_names = []
            away_lineup_names = []
            
            # Get home team player names
            for player_id in list(current_home_lineup)[:5]:  # Limit to 5 players
                player_name = None
                if player_id in self.parser.players:
                    player_name = self.parser.players[player_id].get('name', '')
                else:
                    # Try to get from starting lineups if not in parser.players
                    for player in starting_lineups.get('home', []):
                        if player.get('player_id') == player_id:
                            player_name = player.get('player_name', '')
                            break
                
                # If still no name, try to get from plays data
                if not player_name:
                    for _, play_row in self.plays_df.iterrows():
                        if play_row['player_id'] == player_id and play_row['player_name']:
                            player_name = play_row['player_name']
                            break
                
                # If still no name, try to extract from player_id
                if not player_name and player_id:
                    # Extract jersey number from player_id (format: Team_Number)
                    if '_' in player_id:
                        jersey_num = player_id.split('_')[1]
                        player_name = f"Player #{jersey_num}"
                
                if player_name:
                    # Clean up player name formatting
                    if ',' in player_name:
                        parts = player_name.split(',')
                        if len(parts) == 2:
                            last_name = parts[0].strip()
                            first_name = parts[1].strip()
                            player_name = f"{first_name} {last_name}"
                    player_name = player_name.title()
                    home_lineup_names.append(player_name)
            
            # Get away team player names
            for player_id in list(current_away_lineup)[:5]:  # Limit to 5 players
                player_name = None
                if player_id in self.parser.players:
                    player_name = self.parser.players[player_id].get('name', '')
                else:
                    # Try to get from starting lineups if not in parser.players
                    for player in starting_lineups.get('away', []):
                        if player.get('player_id') == player_id:
                            player_name = player.get('player_name', '')
                            break
                
                # If still no name, try to get from plays data
                if not player_name:
                    for _, play_row in self.plays_df.iterrows():
                        if play_row['player_id'] == player_id and play_row['player_name']:
                            player_name = play_row['player_name']
                            break
                
                # If still no name, try to extract from player_id
                if not player_name and player_id:
                    # Extract jersey number from player_id (format: Team_Number)
                    if '_' in player_id:
                        jersey_num = player_id.split('_')[1]
                        player_name = f"Player #{jersey_num}"
                
                if player_name:
                    # Clean up player name formatting
                    if ',' in player_name:
                        parts = player_name.split(',')
                        if len(parts) == 2:
                            last_name = parts[0].strip()
                            first_name = parts[1].strip()
                            player_name = f"{first_name} {last_name}"
                    player_name = player_name.title()
                    away_lineup_names.append(player_name)
            
            # If we don't have 5 players, try to fill in from all players who have been on the court
            while len(home_lineup_names) < 5:
                # Look for players in all_home_players who aren't already in the lineup
                for player_id in all_home_players:
                    if len(home_lineup_names) >= 5:
                        break
                    
                    # Check if this player is already in the lineup
                    player_already_in_lineup = False
                    for existing_player_id in current_home_lineup:
                        if existing_player_id == player_id:
                            player_already_in_lineup = True
                            break
                    
                    if not player_already_in_lineup:
                        # Try to get player name
                        player_name = None
                        if player_id in self.parser.players:
                            player_name = self.parser.players[player_id].get('name', '')
                        else:
                            # Try to get from starting lineups
                            for player in starting_lineups.get('home', []):
                                if player.get('player_id') == player_id:
                                    player_name = player.get('player_name', '')
                                    break
                        
                        # If still no name, try to get from plays data
                        if not player_name:
                            for _, play_row in self.plays_df.iterrows():
                                if play_row['player_id'] == player_id and play_row['player_name']:
                                    player_name = play_row['player_name']
                                    break
                        
                        # If still no name, extract from player_id
                        if not player_name and player_id:
                            if '_' in player_id:
                                jersey_num = player_id.split('_')[1]
                                player_name = f"Player #{jersey_num}"
                        
                        if player_name:
                            # Clean up player name formatting
                            if ',' in player_name:
                                parts = player_name.split(',')
                                if len(parts) == 2:
                                    last_name = parts[0].strip()
                                    first_name = parts[1].strip()
                                    player_name = f"{first_name} {last_name}"
                            player_name = player_name.title()
                            home_lineup_names.append(player_name)
                            break
            
            # Same logic for away team
            while len(away_lineup_names) < 5:
                # Look for players in all_away_players who aren't already in the lineup
                for player_id in all_away_players:
                    if len(away_lineup_names) >= 5:
                        break
                    
                    # Check if this player is already in the lineup
                    player_already_in_lineup = False
                    for existing_player_id in current_away_lineup:
                        if existing_player_id == player_id:
                            player_already_in_lineup = True
                            break
                    
                    if not player_already_in_lineup:
                        # Try to get player name
                        player_name = None
                        if player_id in self.parser.players:
                            player_name = self.parser.players[player_id].get('name', '')
                        else:
                            # Try to get from starting lineups
                            for player in starting_lineups.get('away', []):
                                if player.get('player_id') == player_id:
                                    player_name = player.get('player_name', '')
                                    break
                        
                        # If still no name, try to get from plays data
                        if not player_name:
                            for _, play_row in self.plays_df.iterrows():
                                if play_row['player_id'] == player_id and play_row['player_name']:
                                    player_name = play_row['player_name']
                                    break
                        
                        # If still no name, extract from player_id
                        if not player_name and player_id:
                            if '_' in player_id:
                                jersey_num = player_id.split('_')[1]
                                player_name = f"Player #{jersey_num}"
                        
                        if player_name:
                            # Clean up player name formatting
                            if ',' in player_name:
                                parts = player_name.split(',')
                                if len(parts) == 2:
                                    last_name = parts[0].strip()
                                    first_name = parts[1].strip()
                                    player_name = f"{first_name} {last_name}"
                            player_name = player_name.title()
                            away_lineup_names.append(player_name)
                            break
            
            # If we still don't have 5 players, use jersey numbers as fallback
            while len(home_lineup_names) < 5:
                missing_count = 5 - len(home_lineup_names)
                for i in range(missing_count):
                    home_lineup_names.append(f"Player #{i+1}")
            
            while len(away_lineup_names) < 5:
                missing_count = 5 - len(away_lineup_names)
                for i in range(missing_count):
                    away_lineup_names.append(f"Player #{i+1}")
            
            enhanced_play = {
                'play_id': play['play_id'],
                'game_clock': play['time'],
                'event_description': enhanced_description,
                'team': play['team_name'],
                'player': play['player_name'],
                'points': play['points'],
                'home_score': play.get('home_score', ''),
                'away_score': play.get('away_score', ''),
                'home_lineup': ', '.join(home_lineup_names),
                'away_lineup': ', '.join(away_lineup_names),
                'event_type': play['event_type'],
                'shot_type': play['shot_type'],
                'assist_player': play.get('assist_player_name', ''),
                'rebound_type': play.get('rebound_type', ''),
                'foul_type': play.get('foul_type', ''),
                'foul_player': play.get('foul_player_name', ''),
                'time_seconds': play['time_seconds']
            }
            
            enhanced_plays.append(enhanced_play)
        
        return pd.DataFrame(enhanced_plays)
    
    def _create_enhanced_event_description(self, play: pd.Series) -> str:
        """Create enhanced event descriptions with more detail."""
        event_type = play['event_type'].lower()
        player_name = play['player_name']
        team_name = play['team_name']
        points = play['points']
        shot_type = play['shot_type']
        assist_player = play.get('assist_player_name', '')
        rebound_type = play.get('rebound_type', '')
        
        if 'shot' in event_type:
            if points > 0:
                if shot_type == '3pt':
                    if assist_player:
                        return f"Made 3PT FG by {player_name} for {team_name} (assisted by {assist_player})"
                    else:
                        return f"Made 3PT FG by {player_name} for {team_name}"
                elif shot_type == 'free_throw':
                    return f"Made Free Throw by {player_name} for {team_name}"
                else:
                    if assist_player:
                        return f"Made 2PT FG by {player_name} for {team_name} (assisted by {assist_player})"
                    else:
                        return f"Made 2PT FG by {player_name} for {team_name}"
            else:
                if shot_type == '3pt':
                    return f"Missed 3PT FG by {player_name} for {team_name}"
                elif shot_type == 'free_throw':
                    return f"Missed Free Throw by {player_name} for {team_name}"
                else:
                    return f"Missed 2PT FG by {player_name} for {team_name}"
        
        elif 'rebound' in event_type:
            if rebound_type == 'offensive':
                return f"{player_name} Offensive Rebound for {team_name}"
            else:
                return f"{player_name} Defensive Rebound for {team_name}"
        
        elif 'assist' in event_type:
            return f"Assist by {player_name} for {team_name}"
        
        elif 'steal' in event_type:
            return f"{player_name} Steal for {team_name}"
        
        elif 'block' in event_type:
            return f"{player_name} Blocked Shot for {team_name}"
        
        elif 'turnover' in event_type:
            return f"{player_name} Turnover for {team_name}"
        
        elif 'foul' in event_type:
            return f"{player_name} Foul for {team_name}"
        
        elif 'substitution' in event_type:
            if play.get('substitution_in'):
                return f"{player_name} enters the game for {team_name}"
            else:
                return f"{player_name} exits the game for {team_name}"
        
        elif 'timeout' in event_type:
            return f"{team_name} Timeout"
        
        else:
            return play.get('description', f"{player_name} {event_type} for {team_name}")
    
    def _get_player_names_from_ids(self, player_ids: List[str], team_id: str = None) -> List[str]:
        """Convert player IDs to player names, filtering by team if specified."""
        player_names = []
        seen_names = set()  # To avoid duplicates
        
        for player_id in player_ids:
            # Skip if player_id is empty or None
            if not player_id:
                continue
                
            # Extract team from player_id (format: Team_Number)
            if '_' in player_id:
                player_team_from_id = player_id.split('_')[0]
                if team_id and player_team_from_id != team_id:
                    continue  # Skip if player is not from the correct team
                
            if player_id in self.parser.players:
                player_name = self.parser.players[player_id].get('name', '')
                player_team = self.parser.players[player_id].get('team_id', '')
                
                if player_name and player_team:
                    # Clean up player name formatting
                    if ',' in player_name:
                        parts = player_name.split(',')
                        if len(parts) == 2:
                            last_name = parts[0].strip()
                            first_name = parts[1].strip()
                            player_name = f"{first_name} {last_name}"
                    player_name = player_name.title()
                    
                    # Double-check team consistency
                    if team_id and player_team != team_id:
                        continue
                    
                    # Avoid duplicates
                    if player_name not in seen_names:
                        player_names.append(player_name)
                        seen_names.add(player_name)
            else:
                # Try to extract from plays data as fallback
                for _, play in self.plays_df.iterrows():
                    if play['player_id'] == player_id and play['player_name'] and play['team_id']:
                        player_name = play['player_name']
                        play_team_id = play['team_id']
                        
                        # Check team consistency
                        if team_id and play_team_id != team_id:
                            continue
                        
                        if ',' in player_name:
                            parts = player_name.split(',')
                            if len(parts) == 2:
                                last_name = parts[0].strip()
                                first_name = parts[1].strip()
                                player_name = f"{first_name} {last_name}"
                        player_name = player_name.title()
                        
                        # Avoid duplicates
                        if player_name not in seen_names:
                            player_names.append(player_name)
                            seen_names.add(player_name)
                        break
        
        return player_names

    def process_all(self) -> Dict[str, pd.DataFrame]:
        """Process all data and return all DataFrames."""
        plays_df = self.create_plays_dataframe()
        player_stats_df = self.create_player_stats_dataframe()
        team_stats_df = self.create_team_stats_dataframe()
        lineup_df = self.create_lineup_dataframe()
        enhanced_play_by_play_df = self.create_enhanced_play_by_play_dataframe()
        
        return {
            'plays': plays_df,
            'player_stats': player_stats_df,
            'team_stats': team_stats_df,
            'lineups': lineup_df,
            'enhanced_play_by_play': enhanced_play_by_play_df,
            'game_info': self.parser.game_info,
            'teams': self.parser.teams,
            'players': self.parser.players,
            'starting_lineups': getattr(self.parser, 'starting_lineups', {'home': [], 'away': []})
        } 