# ⚽ Ultimate Soccer 3D

A full-featured 3D soccer game built with Python and the Ursina Engine.

## Features
- **Full 3D gameplay** with broadcast-style camera
- **Dribbling, passing, shooting, crossing** with power control
- **Slide tackles, standing tackles, pressing**
- **AI opponents** with formation-based tactics
- **Referee system** with fouls, yellow/red cards, free kicks, penalties
- **Offside detection**
- **Corner kicks, throw-ins, goal kicks**
- **Multiple teams** with real formations (4-3-3, 4-4-2, 3-5-2, etc.)
- **Tournament & League mode**
- **Weather effects** (rain, snow, night)
- **Commentary system**
- **Replay system**
- **Minimap & full HUD**
- **Skill moves & tricks**

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Controls

### Offense (with ball)
| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move player |
| Space | Pass (hold for power) |
| E | Through ball |
| Q | Shoot (hold for power) |
| Shift | Sprint |
| F | Skill move / Dribble trick |
| C | Cross |
| R | Lob pass |

### Defense (without ball)
| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move player |
| Space | Switch player |
| Q | Slide tackle |
| E | Standing tackle / Press |
| Shift | Sprint |
| F | Contain / Jockey |
| Tab | Team press |

### General
| Key | Action |
|-----|--------|
| Escape | Pause menu |
| 1-4 | Camera angles |
| M | Toggle minimap |
| V | Replay last action |

## Requirements
- Python 3.8+
- Ursina Engine 7.0+
- NumPy

## Architecture
The game is built with a modular architecture:
- `engine/` - Core game systems (physics, camera, rendering)
- `entities/` - Game objects (players, ball, field)
- `gameplay/` - Match logic, referee, formations
- `ai/` - AI decision making and pathfinding
- `ui/` - HUD, menus, minimap
- `data/` - Teams, players, tournaments
