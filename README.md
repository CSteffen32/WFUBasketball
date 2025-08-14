# Basketball Analytics Prompt

A comprehensive basketball play-by-play XML parser that extracts detailed game data and generates multiple analytical outputs.

## Features

### Enhanced Play-by-Play Analysis
- **Detailed Event Descriptions**: Each play includes enhanced descriptions like "Made 3PT FG by Player X for Team Y (assisted by Player Z)" or "Player X Defensive Rebound for Team Y"
- **Half/Period Tracking**: Automatically identifies which half (1st Half/2nd Half) each play occurred in
- **Real-time Lineup Tracking**: Shows who was on the court for each play, with automatic updates based on substitutions
- **Comprehensive Event Types**: Covers all basketball events including shots, rebounds, assists, steals, blocks, turnovers, fouls, substitutions, and timeouts

### Multiple Output Formats
The parser generates several CSV files for different analytical purposes:

1. **`enhanced_play_by_play.csv`** - The main enhanced play-by-play file with columns:
   - `play_id`: Unique identifier for each play
   - `half`: Which half the play occurred in (1st Half/2nd Half)
   - `period`: Game period number
   - `game_clock`: Time remaining in the period (MM:SS format)
   - `event_description`: Enhanced description of the play
   - `team`: Team name
   - `player`: Player name
   - `points`: Points scored (if any)
   - `home_score`: Home team score after the play
   - `away_score`: Away team score after the play
   - `home_lineup`: Current home team lineup (comma-separated player names)
   - `away_lineup`: Current away team lineup (comma-separated player names)
   - `event_type`: Type of event (shot, rebound, assist, etc.)
   - `shot_type`: Type of shot (2pt, 3pt, free_throw)
   - `assist_player`: Player who assisted (if applicable)
   - `rebound_type`: Type of rebound (offensive/defensive)
   - `foul_type`: Type of foul (if applicable)
   - `foul_player`: Player who committed the foul (if applicable)
   - `time_seconds`: Time in seconds for easier analysis

2. **`plays.csv`** - Raw play-by-play data
3. **`player_stats.csv`** - Individual player statistics
4. **`team_stats.csv`** - Team-level statistics
5. **`lineups.csv`** - Lineup tracking data
6. **`box_score.csv`** - Traditional box score format

### Event Description Examples
The enhanced play-by-play provides detailed, readable descriptions:

- **Scoring Plays**: "Made 3PT FG by John Smith for Team A (assisted by Mike Johnson)"
- **Rebounds**: "John Smith Defensive Rebound for Team A"
- **Assists**: "Assist by Mike Johnson for Team A"
- **Steals**: "John Smith Steal for Team A"
- **Blocks**: "John Smith Blocked Shot for Team A"
- **Turnovers**: "John Smith Turnover for Team A"
- **Fouls**: "John Smith Foul for Team A"
- **Substitutions**: "John Smith enters the game for Team A"
- **Timeouts**: "Team A Timeout"

### Lineup Tracking
The system automatically tracks who is on the court for each play:
- Initializes with starting lineups from the XML data
- Updates lineups in real-time based on substitution events
- Shows current lineup for both teams on every play
- Handles complex substitution scenarios

## Usage

### Basic Usage
```bash
python3 main.py <path_to_xml_file>
```

### Example
```bash
python3 main.py example.XML
```

### Output
The parser will generate all CSV files in the `basketball_analysis_output/` directory and display:
- Game information
- Team details
- Starting lineups
- Player statistics
- Sample enhanced play-by-play data
- Additional analysis including:
  - Game flow analysis
  - Scoring analysis
  - Event type distribution
  - Player performance analysis

## XML Format Support

The parser supports multiple XML formats through an adapter system:
- **Genius Sports Format**: Primary format with comprehensive support
- **NBA Play-by-Play Format**: NBA-specific XML structures
- **Generic XML Format**: Fallback for other XML structures

## Requirements

- Python 3.6+
- pandas
- numpy
- xml.etree.ElementTree (built-in)

## Installation

1. Clone or download the repository
2. Install required packages:
```bash
pip install pandas numpy
```
3. Place your basketball XML file in the directory
4. Run the parser

## Advanced Features

### Player Name Formatting
- Automatically converts "LAST,FIRST" format to "First Last"
- Handles various name formats consistently
- Title cases player names for readability

### Time Tracking
- Converts MM:SS format to seconds for easier analysis
- Maintains original time format for display
- Supports period-based time tracking

### Score Tracking
- Tracks home and away scores throughout the game
- Updates scores after each scoring play
- Handles missing score data gracefully

## Analysis Capabilities

The enhanced play-by-play data enables various analytical insights:
- **Lineup Effectiveness**: Analyze which lineups perform best
- **Player Usage Patterns**: Track substitution patterns and player combinations
- **Game Flow Analysis**: Understand momentum shifts and scoring runs
- **Event Sequencing**: Analyze play patterns and transitions
- **Time-based Analysis**: Study performance at different game stages

## File Structure

```
basketball_analysis_output/
├── enhanced_play_by_play.csv  # Main enhanced play-by-play file
├── plays.csv                  # Raw play data
├── player_stats.csv           # Player statistics
├── team_stats.csv             # Team statistics
├── lineups.csv                # Lineup tracking
└── box_score.csv              # Traditional box score
```

## Contributing

The parser is designed to be extensible. New XML formats can be added by creating new adapter classes in `xml_adapters.py`. 