"""
XML Format Adapters

This module provides adapters for different XML formats commonly used
in basketball play-by-play data. It allows the parser to handle various
XML structures flexibly.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import re


class XMLFormatAdapter:
    """Base class for XML format adapters."""
    
    def __init__(self):
        self.format_name = "base"
    
    def can_handle(self, root: ET.Element) -> bool:
        """Check if this adapter can handle the given XML structure."""
        raise NotImplementedError
    
    def extract_game_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract game information from the XML."""
        raise NotImplementedError
    
    def extract_teams(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract team information from the XML."""
        raise NotImplementedError
    
    def extract_players(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract player information from the XML."""
        raise NotImplementedError
    
    def extract_plays(self, root: ET.Element) -> List[Dict]:
        """Extract play-by-play data from the XML."""
        raise NotImplementedError


class GeniusSportsAdapter(XMLFormatAdapter):
    """Adapter for Genius Sports basketball XML format."""
    
    def __init__(self):
        self.format_name = "genius_sports"
    
    def can_handle(self, root: ET.Element) -> bool:
        """Check if this looks like Genius Sports format."""
        # Look for Genius Sports indicators
        genius_indicators = [
            root.tag == 'bbgame',
            root.get('source', '').lower() == 'genius sports',
            root.find('.//venue') is not None,
            root.find('.//plays') is not None
        ]
        return any(genius_indicators)
    
    def extract_game_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract game information from Genius Sports format."""
        game_info = {}
        
        # Extract from venue element
        venue_elem = root.find('.//venue')
        if venue_elem is not None:
            game_info.update({
                'game_id': venue_elem.get('gameid', ''),
                'date': venue_elem.get('date', ''),
                'venue': venue_elem.get('location', ''),
                'home_team': venue_elem.get('homename', ''),
                'away_team': venue_elem.get('visname', ''),
                'home_id': venue_elem.get('homeid', ''),
                'away_id': venue_elem.get('visid', ''),
                'time': venue_elem.get('time', ''),
                'attendance': venue_elem.get('attend', ''),
                'league_game': venue_elem.get('leaguegame', ''),
                'neutral_game': venue_elem.get('neutralgame', ''),
                'postseason': venue_elem.get('postseason', ''),
            })
        
        # Extract from root element
        game_info.update({
            'source': root.get('source', ''),
            'version': root.get('version', ''),
            'generated': root.get('generated', ''),
        })
        
        return game_info
    
    def extract_teams(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract team information from Genius Sports format."""
        teams = {}
        
        team_elements = root.findall('.//team')
        for team_elem in team_elements:
            team_id = team_elem.get('id', '')
            team_name = team_elem.get('name', '')
            team_code = team_elem.get('code', '')
            team_vh = team_elem.get('vh', '')  # V for visitor, H for home
            team_record = team_elem.get('record', '')
            
            if team_id:
                teams[team_id] = {
                    'name': team_name,
                    'code': team_code,
                    'vh': team_vh,
                    'record': team_record,
                    'players': {}
                }
        
        return teams
    
    def extract_players(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract player information from Genius Sports format."""
        players = {}
        
        # Iterate through each team element to get all players
        for team_elem in root.findall('.//team'):
            team_id = team_elem.get('id', '')
            
            # Get all players for this team
            for player_elem in team_elem.findall('.//player'):
                # Get player info from attributes
                uni = player_elem.get('uni', '')
                code = player_elem.get('code', '')
                name = player_elem.get('name', '')
                checkname = player_elem.get('checkname', '')
                gp = player_elem.get('gp', '0')
                gs = player_elem.get('gs', '0')
                pos = player_elem.get('pos', '')
                
                # Create unique player ID
                player_id = f"{team_id}_{uni}"
                
                if player_id and name:  # Only add if we have a name
                    players[player_id] = {
                        'team_id': team_id,
                        'name': name,
                        'jersey': uni,
                        'position': pos,
                        'checkname': checkname,
                        'code': code,
                        'games_played': int(gp) if gp.isdigit() else 0,
                        'games_started': int(gs) if gs.isdigit() else 0,
                    }
        
        return players
    
    def extract_plays(self, root: ET.Element) -> List[Dict]:
        """Extract play-by-play data from Genius Sports format."""
        plays = []
        
        # Extract starting lineups from player data (gs="1" indicates games started)
        starting_lineups = self._extract_starting_lineups_from_players(root)
        
        # Find all play elements within periods
        play_elements = root.findall('.//play')
        
        for play_elem in play_elements:
            play_data = self._parse_genius_play(play_elem)
            if play_data:
                # Filter out initial lineup plays at exactly 20:00 (start of period)
                if play_data['time'] == '20:00' and play_data['event_type'] == 'substitution':
                    continue
                plays.append(play_data)
        
        # Store starting lineups in the adapter for later access
        self.starting_lineups = starting_lineups
        return plays
    
    def _extract_starting_lineups_from_players(self, root: ET.Element) -> Dict:
        """Extract starting lineups from player data using gs attribute."""
        starting_lineups = {'home': [], 'away': []}
        
        # Find all players with gs="1" (games started)
        for team_elem in root.findall('.//team'):
            team_id = team_elem.get('id', '')
            team_vh = team_elem.get('vh', '')  # V for visitor, H for home
            
            for player_elem in team_elem.findall('.//player'):
                gs = player_elem.get('gs', '0')
                if gs == '1':  # This player started the game
                    uni = player_elem.get('uni', '')
                    name = player_elem.get('name', '')
                    pos = player_elem.get('pos', '')
                    
                    team_side = 'home' if team_vh == 'H' else 'away'
                    starting_lineups[team_side].append({
                        'player_id': f"{team_id}_{uni}",
                        'player_name': name,
                        'jersey': uni,
                        'position': pos
                    })
        
        return starting_lineups
    
    def get_starting_lineups(self) -> Dict:
        """Get the starting lineups for both teams."""
        return getattr(self, 'starting_lineups', {'home': [], 'away': []})
    
    def _parse_genius_play(self, play_elem: ET.Element) -> Optional[Dict]:
        """Parse individual Genius Sports play element."""
        try:
            # Get basic play info
            vh = play_elem.get('vh', '')  # V for visitor, H for home
            time = play_elem.get('time', '')
            uni = play_elem.get('uni', '')
            team = play_elem.get('team', '')
            checkname = play_elem.get('checkname', '')
            action = play_elem.get('action', '')
            play_type = play_elem.get('type', '')
            
            # Get period info from parent
            period_elem = play_elem.getparent() if hasattr(play_elem, 'getparent') else None
            period = 1  # Default
            if period_elem is not None and period_elem.tag == 'period':
                period = int(period_elem.get('number', 1))
            
            # Create unique play ID (using a simple counter)
            play_id = f"play_{hash(play_elem)}"
            
            # Determine event type and points
            event_type = self._map_action_to_event_type(action, play_type)
            points = self._calculate_points(action, play_type)
            
            # Create player ID
            player_id = f"{team}_{uni}" if team and uni else ""
            
            # Build description
            description = self._build_description(action, play_type, checkname, team)
            
            play_data = {
                'play_id': play_id,
                'period': period,
                'time': time,
                'clock': time,
                'team_id': team,
                'player_id': player_id,
                'player_name': checkname,  # Add player name
                'event_type': event_type,
                'description': description,
                'points': points,
                'shot_type': self._map_shot_type(play_type),
                'shot_distance': '',
                'assist_player_id': '',
                'rebound_type': 'offensive' if 'OFF' in play_type else 'defensive' if 'DEF' in play_type else '',
                'foul_type': '',
                'foul_player_id': '',
                'substitution_in': uni if action == 'SUB' and play_type == 'IN' else '',
                'substitution_out': uni if action == 'SUB' and play_type == 'OUT' else '',
                'timeout_team': team if action == 'TIMEOUT' else '',
                'jumpball_won': '',
                'jumpball_player': '',
                'vh': vh,
                'action': action,
                'play_type': play_type,
            }
            
            # Extract score if available
            vscore = play_elem.get('vscore', '')
            hscore = play_elem.get('hscore', '')
            if vscore and hscore:
                play_data['home_score'] = hscore
                play_data['away_score'] = vscore
            
            return play_data
            
        except Exception as e:
            print(f"Error parsing Genius Sports play element: {e}")
            return None
    
    def _map_action_to_event_type(self, action: str, play_type: str) -> str:
        """Map Genius Sports action to standard event type."""
        action_lower = action.lower()
        play_type_lower = play_type.lower()
        
        if 'good' in action_lower:
            if '3ptr' in play_type_lower:
                return 'shot'
            elif 'ft' in play_type_lower:
                return 'free_throw'
            else:
                return 'shot'
        elif 'miss' in action_lower:
            if 'ft' in play_type_lower:
                return 'free_throw'
            else:
                return 'shot'
        elif 'rebound' in action_lower:
            return 'rebound'
        elif 'assist' in action_lower:
            return 'assist'
        elif 'steal' in action_lower:
            return 'steal'
        elif 'block' in action_lower:
            return 'block'
        elif 'turnover' in action_lower:
            return 'turnover'
        elif 'foul' in action_lower:
            return 'foul'
        elif 'sub' in action_lower:
            return 'substitution'
        elif 'timeout' in action_lower:
            return 'timeout'
        else:
            return action_lower
    
    def _calculate_points(self, action: str, play_type: str) -> int:
        """Calculate points for a play."""
        action_lower = action.lower()
        play_type_lower = play_type.lower()
        
        if 'good' in action_lower:
            if '3ptr' in play_type_lower:
                return 3
            elif 'ft' in play_type_lower:
                return 1
            else:
                return 2
        return 0
    
    def _map_shot_type(self, play_type: str) -> str:
        """Map play type to shot type."""
        play_type_lower = play_type.lower()
        
        if '3ptr' in play_type_lower:
            return '3pt'
        elif 'ft' in play_type_lower:
            return 'free_throw'
        else:
            return '2pt'
    
    def _build_description(self, action: str, play_type: str, checkname: str, team: str) -> str:
        """Build description for the play."""
        if not checkname:
            return f"{action} {play_type}"
        
        if 'good' in action.lower():
            if '3ptr' in play_type.lower():
                return f"{checkname} makes 3pt shot"
            elif 'ft' in play_type.lower():
                return f"{checkname} makes free throw"
            else:
                return f"{checkname} makes {play_type.lower()} shot"
        elif 'miss' in action.lower():
            if 'ft' in play_type.lower():
                return f"{checkname} misses free throw"
            else:
                return f"{checkname} misses {play_type.lower()} shot"
        elif 'rebound' in action.lower():
            rebound_type = 'offensive' if 'off' in play_type.lower() else 'defensive'
            return f"{checkname} {rebound_type} rebound"
        elif 'assist' in action.lower():
            return f"{checkname} assist"
        elif 'steal' in action.lower():
            return f"{checkname} steals the ball"
        elif 'block' in action.lower():
            return f"{checkname} blocks shot"
        elif 'turnover' in action.lower():
            return f"{checkname} turnover"
        elif 'foul' in action.lower():
            return f"{checkname} foul"
        elif 'sub' in action.lower():
            direction = 'enters' if 'in' in play_type.lower() else 'exits'
            return f"{checkname} {direction} the game"
        elif 'timeout' in action.lower():
            return f"{team} timeout"
        else:
            return f"{checkname} {action} {play_type}"


class GenericXMLAdapter(XMLFormatAdapter):
    """Generic adapter that tries to handle common XML patterns."""
    
    def __init__(self):
        self.format_name = "generic"
    
    def can_handle(self, root: ET.Element) -> bool:
        """Generic adapter can always attempt to handle any XML."""
        return True
    
    def extract_game_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract game information using common patterns."""
        game_info = {}
        
        # Look for game-related elements
        game_elements = root.findall('.//game') or root.findall('.//Game') or root.findall('.//GAME')
        
        if game_elements:
            game = game_elements[0]
            game_info.update(game.attrib)
        
        # Look for metadata elements
        for elem in root.iter():
            if any(keyword in elem.tag.lower() for keyword in ['game', 'match', 'event']):
                game_info.update(elem.attrib)
                break
        
        return game_info
    
    def extract_teams(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract team information using common patterns."""
        teams = {}
        
        # Look for team elements
        team_elements = root.findall('.//team') or root.findall('.//Team') or root.findall('.//TEAM')
        
        for team_elem in team_elements:
            team_id = team_elem.get('id', '') or team_elem.get('team_id', '')
            team_name = team_elem.get('name', '') or team_elem.get('team_name', '')
            team_code = team_elem.get('code', '') or team_elem.get('abbreviation', '')
            
            if team_id:
                teams[team_id] = {
                    'name': team_name,
                    'code': team_code,
                    'players': {}
                }
        
        return teams
    
    def extract_players(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract player information using common patterns."""
        players = {}
        
        # Look for player elements
        player_elements = root.findall('.//player') or root.findall('.//Player') or root.findall('.//PLAYER')
        
        for player_elem in player_elements:
            player_id = player_elem.get('id', '') or player_elem.get('player_id', '')
            team_id = player_elem.get('team_id', '') or player_elem.get('team', '')
            player_name = player_elem.get('name', '') or player_elem.get('player_name', '')
            jersey_number = player_elem.get('jersey', '') or player_elem.get('number', '')
            position = player_elem.get('position', '') or player_elem.get('pos', '')
            
            if player_id:
                players[player_id] = {
                    'team_id': team_id,
                    'name': player_name,
                    'jersey': jersey_number,
                    'position': position
                }
        
        return players
    
    def extract_plays(self, root: ET.Element) -> List[Dict]:
        """Extract play-by-play data using common patterns."""
        plays = []
        
        # Look for play elements
        play_elements = root.findall('.//play') or root.findall('.//Play') or root.findall('.//PLAY')
        
        for play_elem in play_elements:
            play_data = self._parse_play_element(play_elem)
            if play_data:
                plays.append(play_data)
        
        return plays
    
    def _parse_play_element(self, play_elem: ET.Element) -> Optional[Dict]:
        """Parse individual play element."""
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


class NBAPBPAdapter(XMLFormatAdapter):
    """Adapter for NBA-style play-by-play XML format."""
    
    def __init__(self):
        self.format_name = "nba_pbp"
    
    def can_handle(self, root: ET.Element) -> bool:
        """Check if this looks like NBA play-by-play format."""
        # Look for NBA-specific elements or attributes
        nba_indicators = [
            'nba' in root.tag.lower(),
            'basketball' in root.tag.lower(),
            any('nba' in elem.get('league', '').lower() for elem in root.iter() if elem.get('league')),
        ]
        return any(nba_indicators)
    
    def extract_game_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract NBA-specific game information."""
        game_info = {}
        
        # NBA-specific game info extraction
        game_elem = root.find('.//game') or root.find('.//Game')
        if game_elem is not None:
            game_info.update(game_elem.attrib)
        
        return game_info
    
    def extract_teams(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract NBA team information."""
        teams = {}
        
        team_elements = root.findall('.//team')
        for team_elem in team_elements:
            team_id = team_elem.get('id')
            team_name = team_elem.get('name')
            team_code = team_elem.get('abbreviation')
            
            if team_id:
                teams[team_id] = {
                    'name': team_name,
                    'code': team_code,
                    'players': {}
                }
        
        return teams
    
    def extract_players(self, root: ET.Element) -> Dict[str, Dict]:
        """Extract NBA player information."""
        players = {}
        
        player_elements = root.findall('.//player')
        for player_elem in player_elements:
            player_id = player_elem.get('id')
            team_id = player_elem.get('team_id')
            player_name = player_elem.get('name')
            jersey_number = player_elem.get('jersey')
            position = player_elem.get('position')
            
            if player_id:
                players[player_id] = {
                    'team_id': team_id,
                    'name': player_name,
                    'jersey': jersey_number,
                    'position': position
                }
        
        return players
    
    def extract_plays(self, root: ET.Element) -> List[Dict]:
        """Extract NBA play-by-play data."""
        plays = []
        
        play_elements = root.findall('.//play')
        for play_elem in play_elements:
            play_data = self._parse_nba_play(play_elem)
            if play_data:
                plays.append(play_data)
        
        return plays
    
    def _parse_nba_play(self, play_elem: ET.Element) -> Optional[Dict]:
        """Parse NBA-specific play element."""
        try:
            # NBA-specific play parsing
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
            
            return play_data
            
        except Exception as e:
            print(f"Error parsing NBA play element: {e}")
            return None


class AdapterManager:
    """Manager for XML format adapters."""
    
    def __init__(self):
        self.adapters = [
            GeniusSportsAdapter(),
            NBAPBPAdapter(),
            GenericXMLAdapter(),
        ]
    
    def get_adapter(self, root: ET.Element) -> XMLFormatAdapter:
        """Get the appropriate adapter for the XML structure."""
        for adapter in self.adapters:
            if adapter.can_handle(root):
                print(f"Using {adapter.format_name} adapter")
                return adapter
        
        # Fall back to generic adapter
        print("Using generic adapter")
        return GenericXMLAdapter()
    
    def add_adapter(self, adapter: XMLFormatAdapter):
        """Add a new adapter to the manager."""
        self.adapters.insert(0, adapter)  # Add to beginning to check first 