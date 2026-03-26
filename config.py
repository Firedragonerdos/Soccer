"""
Ultimate Soccer 3D - Game Configuration
All constants, settings, controls, and tunable parameters.
"""
import math
from enum import Enum, auto


def rgb(r, g, b):
    """Create Ursina Color from 0-255 int values."""
    from ursina.color import Color
    return Color(r / 255.0, g / 255.0, b / 255.0, 1.0)


def rgba(r, g, b, a):
    """Create Ursina Color from 0-255 int values with alpha."""
    from ursina.color import Color
    return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

# =============================================================================
# WINDOW SETTINGS
# =============================================================================
WINDOW_TITLE = "Ultimate Soccer 3D"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FULLSCREEN = False
WINDOW_FULLSCREEN = False
WINDOW_SIZE = (1920, 1080)
FPS_CAP = 60
WINDOW_FPS_LIMIT = 60
VSYNC = True
BORDERLESS = False

# =============================================================================
# FIELD DIMENSIONS (in game units, roughly 1 unit = 1 meter)
# =============================================================================
FIELD_LENGTH = 105.0
FIELD_WIDTH = 68.0
FIELD_HALF_LENGTH = FIELD_LENGTH / 2.0
FIELD_HALF_WIDTH = FIELD_WIDTH / 2.0

# Penalty area
PENALTY_AREA_LENGTH = 16.5
PENALTY_AREA_WIDTH = 40.3
PENALTY_SPOT_DISTANCE = 11.0

# Goal area (6-yard box)
GOAL_AREA_LENGTH = 5.5
GOAL_AREA_WIDTH = 18.3

# Goal dimensions
GOAL_WIDTH = 7.32
GOAL_HEIGHT = 2.44
GOAL_DEPTH = 2.0
GOAL_POST_RADIUS = 0.06

# Center circle
CENTER_CIRCLE_RADIUS = 9.15

# Corner arc
CORNER_ARC_RADIUS = 1.0

# Line width
LINE_WIDTH = 0.12

# Field surface
GRASS_COLOR_1 = (0.18, 0.55, 0.15)
GRASS_COLOR_2 = (0.15, 0.50, 0.12)
GRASS_STRIPE_WIDTH = 5.25
LINE_COLOR = (1.0, 1.0, 1.0)

# =============================================================================
# BALL PHYSICS
# =============================================================================
BALL_RADIUS = 0.11
BALL_MASS = 0.43
BALL_BOUNCE_COEFFICIENT = 0.72
BALL_FRICTION_GROUND = 0.988
BALL_FRICTION_AIR = 0.999
BALL_GRAVITY = -9.81
BALL_MAX_SPEED = 48.0
BALL_SPIN_DECAY = 0.98
BALL_SPIN_EFFECT = 0.18
BALL_ROLL_FRICTION = 0.982
BALL_BOUNCE_MIN_VELOCITY = 0.25

# =============================================================================
# PLAYER PHYSICS & ATTRIBUTES
# =============================================================================
PLAYER_HEIGHT = 1.80
PLAYER_RADIUS = 0.4
PLAYER_MASS = 75.0

# Movement speeds (m/s)
PLAYER_WALK_SPEED = 2.5
PLAYER_JOG_SPEED = 5.5
PLAYER_RUN_SPEED = 7.5
PLAYER_SPRINT_SPEED = 9.5
PLAYER_MAX_SPRINT_SPEED = 10.5
PLAYER_ACCELERATION = 15.0
PLAYER_DECELERATION = 20.0
PLAYER_TURN_SPEED = 8.0
PLAYER_TURN_SPEED_WITH_BALL = 5.5

# Stamina
STAMINA_MAX = 100.0
STAMINA_SPRINT_DRAIN = 15.0
STAMINA_RUN_DRAIN = 3.0
STAMINA_RECOVERY_RATE = 8.0
STAMINA_RECOVERY_WALKING = 12.0
STAMINA_LOW_THRESHOLD = 20.0
STAMINA_SPEED_PENALTY = 0.75

# Dribbling
DRIBBLE_TOUCH_DISTANCE = 1.2
DRIBBLE_CLOSE_CONTROL = 0.6
DRIBBLE_SPEED_PENALTY = 0.85
DRIBBLE_LOSE_BALL_BASE_CHANCE = 0.001
DRIBBLE_SKILL_MOVE_DURATION = 0.5
DRIBBLE_NUTMEG_CHANCE = 0.05

# Passing
PASS_SHORT_POWER = 14.0
PASS_MEDIUM_POWER = 20.0
PASS_LONG_POWER = 28.0
PASS_THROUGH_BALL_POWER = 22.0
PASS_LOB_POWER = 17.0
PASS_LOB_ANGLE = math.radians(35)
PASS_ACCURACY_BASE = 0.92
PASS_POWER_CHARGE_RATE = 25.0
PASS_MAX_POWER = 35.0
PASS_CROSS_POWER = 26.0
PASS_CROSS_HEIGHT = 8.0
PASS_ONE_TWO_DELAY = 0.8

# Shooting
SHOOT_POWER_BASE = 20.0
SHOOT_POWER_MAX = 38.0
SHOOT_POWER_CHARGE_RATE = 30.0
SHOOT_ACCURACY_BASE = 0.80
SHOOT_FINESSE_POWER = 0.7
SHOOT_FINESSE_CURVE = 0.3
SHOOT_CHIP_ANGLE = math.radians(45)
SHOOT_VOLLEY_POWER_BONUS = 1.3
SHOOT_HEADER_POWER = 0.65
SHOOT_ANGLE_VARIANCE = math.radians(8)
SHOOT_HEIGHT_BASE = 0.8
SHOOT_HEIGHT_VARIANCE = 1.5

# Tackling
TACKLE_RANGE = 1.8
TACKLE_SLIDE_RANGE = 3.5
TACKLE_SLIDE_SPEED = 12.0
TACKLE_SLIDE_DURATION = 0.7
TACKLE_SLIDE_COOLDOWN = 1.5
TACKLE_STANDING_RANGE = 1.5
TACKLE_STANDING_DURATION = 0.3
TACKLE_SUCCESS_BASE = 0.65
TACKLE_FOUL_CHANCE_BASE = 0.15
TACKLE_FROM_BEHIND_FOUL_BONUS = 0.35
TACKLE_SLIDE_FOUL_BONUS = 0.10
TACKLE_RECOVERY_TIME = 0.5

# Heading
HEADER_JUMP_HEIGHT = 0.8
HEADER_JUMP_DURATION = 0.6
HEADER_RANGE = 2.5
HEADER_POWER = 0.5

# Goalkeeper specific
GK_DIVE_SPEED = 8.0
GK_DIVE_RANGE = 3.5
GK_DIVE_DURATION = 0.8
GK_DIVE_RECOVERY = 1.2
GK_REACTION_TIME = 0.15
GK_POSITIONING_SPEED = 6.0
GK_RUSH_SPEED = 7.5
GK_PUNCH_RANGE = 2.0
GK_CATCH_RANGE = 1.5
GK_DISTRIBUTION_POWER = 30.0
GK_KICK_POWER = 35.0
GK_THROW_POWER = 18.0
GK_PARRY_RANGE = 2.5
GK_ONE_ON_ONE_RUSH_DISTANCE = 15.0
GK_BOX_LIMIT_X = PENALTY_AREA_LENGTH
GK_BOX_LIMIT_Z = PENALTY_AREA_WIDTH / 2.0

# =============================================================================
# PLAYER ATTRIBUTES RANGE (1-99 like FIFA)
# =============================================================================
ATTR_MIN = 1
ATTR_MAX = 99

class PlayerAttribute(Enum):
    PACE = auto()
    ACCELERATION = auto()
    SPRINT_SPEED = auto()
    SHOOTING = auto()
    POSITIONING = auto()
    FINISHING = auto()
    SHOT_POWER = auto()
    LONG_SHOTS = auto()
    VOLLEYS = auto()
    PENALTIES = auto()
    PASSING = auto()
    VISION = auto()
    CROSSING = auto()
    FREE_KICK = auto()
    SHORT_PASSING = auto()
    LONG_PASSING = auto()
    CURVE = auto()
    DRIBBLING = auto()
    AGILITY = auto()
    BALANCE = auto()
    REACTIONS = auto()
    BALL_CONTROL = auto()
    COMPOSURE = auto()
    DEFENDING = auto()
    INTERCEPTIONS = auto()
    HEADING = auto()
    MARKING = auto()
    STANDING_TACKLE = auto()
    SLIDING_TACKLE = auto()
    PHYSICAL = auto()
    STRENGTH = auto()
    STAMINA = auto()
    AGGRESSION = auto()
    JUMPING = auto()
    # GK attributes
    GK_DIVING = auto()
    GK_HANDLING = auto()
    GK_KICKING = auto()
    GK_REFLEXES = auto()
    GK_POSITIONING = auto()
    GK_SPEED = auto()

# =============================================================================
# PLAYER POSITIONS
# =============================================================================
class Position(Enum):
    GK = "GK"
    LB = "LB"
    CB = "CB"
    RB = "RB"
    LWB = "LWB"
    RWB = "RWB"
    CDM = "CDM"
    CM = "CM"
    CAM = "CAM"
    LM = "LM"
    RM = "RM"
    LW = "LW"
    RW = "RW"
    CF = "CF"
    ST = "ST"

POSITION_GROUPS = {
    'GK': [Position.GK],
    'DEF': [Position.LB, Position.CB, Position.RB, Position.LWB, Position.RWB],
    'MID': [Position.CDM, Position.CM, Position.CAM, Position.LM, Position.RM, Position.LW, Position.RW],
    'FWD': [Position.CF, Position.ST],
}

# =============================================================================
# MATCH SETTINGS
# =============================================================================
MATCH_HALF_DURATION = 270.0  # 4.5 minutes per half (real time)
MATCH_EXTRA_TIME_MAX = 30.0
MATCH_HALFTIME_DURATION = 5.0
MATCH_KICKOFF_DELAY = 2.0
MATCH_GOAL_CELEBRATION_TIME = 4.0
MATCH_SUBSTITUTION_LIMIT = 5
MATCH_INJURY_TIME_BASE = 30.0

# =============================================================================
# REFEREE SETTINGS
# =============================================================================
FOUL_SEVERITY_THRESHOLD_YELLOW = 0.5
FOUL_SEVERITY_THRESHOLD_RED = 0.85
FOUL_ADVANTAGE_DURATION = 3.0
FOUL_ADVANTAGE_DISTANCE = 15.0
FOUL_FREE_KICK_WALL_DISTANCE = 9.15
OFFSIDE_TOLERANCE = 0.5
HANDBALL_CHECK_DISTANCE = 2.0

class FoulType(Enum):
    NO_FOUL = auto()
    FOUL_TACKLE = auto()
    FOUL_PUSH = auto()
    FOUL_TRIP = auto()
    FOUL_HOLD = auto()
    FOUL_HANDBALL = auto()
    DANGEROUS_PLAY = auto()
    PROFESSIONAL_FOUL = auto()

class CardType(Enum):
    NONE = auto()
    YELLOW = auto()
    SECOND_YELLOW = auto()
    RED = auto()

class SetPieceType(Enum):
    NONE = auto()
    KICKOFF = auto()
    FREE_KICK = auto()
    PENALTY = auto()
    CORNER_KICK = auto()
    GOAL_KICK = auto()
    THROW_IN = auto()
    DROP_BALL = auto()

# =============================================================================
# AI SETTINGS
# =============================================================================
class AIState(Enum):
    IDLE = auto()
    CHASE_BALL = auto()
    SUPPORT_ATTACK = auto()
    MAKE_RUN = auto()
    HOLD_POSITION = auto()
    PRESS_OPPONENT = auto()
    MARK_PLAYER = auto()
    COVER_SPACE = auto()
    TRACK_BACK = auto()
    DRIBBLE = auto()
    PASS = auto()
    SHOOT = auto()
    CROSS = auto()
    CLEAR = auto()
    TACKLE = auto()
    INTERCEPT = auto()
    SET_PIECE_POSITION = auto()
    CELEBRATE = auto()
    RETURN_TO_POSITION = auto()

class TeamTactic(Enum):
    BALANCED = auto()
    ATTACKING = auto()
    DEFENSIVE = auto()
    COUNTER_ATTACK = auto()
    HIGH_PRESS = auto()
    PARK_THE_BUS = auto()
    TIKI_TAKA = auto()
    LONG_BALL = auto()
    WING_PLAY = auto()

class MentalityLevel(Enum):
    ULTRA_DEFENSIVE = 1
    DEFENSIVE = 2
    BALANCED = 3
    ATTACKING = 4
    ULTRA_ATTACKING = 5

AI_DECISION_INTERVAL = 0.5
AI_PASS_DECISION_INTERVAL = 0.25
AI_REACTION_TIME_MIN = 0.1
AI_REACTION_TIME_MAX = 0.4
AI_VISION_RANGE = 40.0
AI_PRESS_DISTANCE = 8.0
AI_MARK_DISTANCE = 2.0
AI_SUPPORT_DISTANCE = 15.0
AI_THROUGH_BALL_ANTICIPATION = 1.5
AI_OFFSIDE_TRAP_LINE = 5.0
AI_DEFENSIVE_LINE_DEPTH = 0.3
AI_ATTACKING_LINE_DEPTH = 0.7

# AI difficulty scaling (0.0 = amateur, 1.0 = legendary)
AI_DIFFICULTY_DEFAULT = 0.6
AI_DIFFICULTY_LEVELS = {
    'amateur': 0.2,
    'semi_pro': 0.4,
    'professional': 0.6,
    'world_class': 0.8,
    'legendary': 1.0,
}

# =============================================================================
# CAMERA SETTINGS
# =============================================================================
class CameraMode(Enum):
    BROADCAST = auto()
    DYNAMIC = auto()
    END_TO_END = auto()
    PLAYER_FOLLOW = auto()
    TACTICAL = auto()
    REPLAY = auto()

CAMERA_BROADCAST_HEIGHT = 25.0
CAMERA_BROADCAST_DISTANCE = 35.0
CAMERA_BROADCAST_ANGLE = -45.0
CAMERA_FOLLOW_SPEED = 5.0
CAMERA_FOLLOW_OFFSET_Y = 20.0
CAMERA_FOLLOW_OFFSET_Z = -25.0
CAMERA_DYNAMIC_ZOOM_MIN = 20.0
CAMERA_DYNAMIC_ZOOM_MAX = 45.0
CAMERA_SHAKE_INTENSITY = 0.1
CAMERA_SHAKE_DURATION = 0.3
CAMERA_REPLAY_SPEED = 0.5
CAMERA_TRANSITION_SPEED = 3.0
CAMERA_TACTICAL_HEIGHT = 50.0

# =============================================================================
# HUD & UI SETTINGS
# =============================================================================
HUD_SCOREBOARD_OPACITY = 0.85
HUD_MINIMAP_SIZE = 200
HUD_MINIMAP_OPACITY = 0.75
HUD_MINIMAP_POSITION = (0.75, 0.75)
HUD_PLAYER_INDICATOR_HEIGHT = 2.5
HUD_ARROW_SIZE = 0.5
HUD_POWER_BAR_WIDTH = 100
HUD_POWER_BAR_HEIGHT = 10
HUD_COMMENTARY_DURATION = 4.0
HUD_RADAR_DOT_SIZE = 4
HUD_STAMINA_BAR_WIDTH = 40
HUD_STAMINA_BAR_HEIGHT = 4

MENU_TRANSITION_SPEED = 0.3
MENU_BACKGROUND_BLUR = 5

# =============================================================================
# VISUAL EFFECTS
# =============================================================================
PARTICLE_GRASS_ON_SLIDE = True
PARTICLE_GRASS_COUNT = 15
PARTICLE_GOAL_CELEBRATION_COUNT = 50
PARTICLE_RAIN_COUNT = 200
PARTICLE_SNOW_COUNT = 100

SHADOW_ENABLED = True
SHADOW_QUALITY = 2048
SHADOW_DISTANCE = 60.0

# Weather
class WeatherType(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    RAIN = auto()
    HEAVY_RAIN = auto()
    SNOW = auto()
    FOG = auto()
    NIGHT = auto()

WEATHER_RAIN_SPEED_PENALTY = 0.95
WEATHER_RAIN_BALL_FRICTION = 0.97
WEATHER_SNOW_SPEED_PENALTY = 0.90
WEATHER_SNOW_BALL_FRICTION = 0.96
WEATHER_FOG_VISIBILITY = 40.0

# =============================================================================
# STADIUM SETTINGS
# =============================================================================
STADIUM_STAND_HEIGHT = 15.0
STADIUM_STAND_DEPTH = 25.0
STADIUM_STAND_ROWS = 20
STADIUM_CROWD_DENSITY = 0.8
STADIUM_LIGHT_HEIGHT = 45.0
STADIUM_AMBIENT_LIGHT = 0.4
STADIUM_DIRECTIONAL_LIGHT = 0.8
STADIUM_CROWD_COLORS = [
    (1.0, 0.2, 0.2),
    (0.2, 0.2, 1.0),
    (1.0, 1.0, 1.0),
    (0.2, 0.8, 0.2),
    (1.0, 1.0, 0.2),
]

# =============================================================================
# SOUND SETTINGS
# =============================================================================
SOUND_MASTER_VOLUME = 0.8
SOUND_CROWD_VOLUME = 0.5
SOUND_EFFECTS_VOLUME = 0.7
SOUND_SFX_VOLUME = 0.7
SOUND_COMMENTARY_VOLUME = 0.9
SOUND_MUSIC_VOLUME = 0.4

# =============================================================================
# CONTROLS MAPPING
# =============================================================================
class ControlAction(Enum):
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    PASS_BALL = auto()
    SHOOT = auto()
    THROUGH_BALL = auto()
    CROSS = auto()
    LOB_PASS = auto()
    SPRINT = auto()
    SKILL_MOVE = auto()
    SWITCH_PLAYER = auto()
    SLIDE_TACKLE = auto()
    CONTAIN = auto()
    TEAM_PRESS = auto()
    PAUSE = auto()
    CAMERA_1 = auto()
    CAMERA_2 = auto()
    CAMERA_3 = auto()
    CAMERA_4 = auto()
    MINIMAP_TOGGLE = auto()
    REPLAY = auto()

DEFAULT_CONTROLS = {
    ControlAction.MOVE_UP: ['w', 'up arrow'],
    ControlAction.MOVE_DOWN: ['s', 'down arrow'],
    ControlAction.MOVE_LEFT: ['a', 'left arrow'],
    ControlAction.MOVE_RIGHT: ['d', 'right arrow'],
    ControlAction.PASS_BALL: ['space'],
    ControlAction.SHOOT: ['q'],
    ControlAction.THROUGH_BALL: ['e'],
    ControlAction.CROSS: ['c'],
    ControlAction.LOB_PASS: ['r'],
    ControlAction.SPRINT: ['left shift', 'right shift'],
    ControlAction.SKILL_MOVE: ['f'],
    ControlAction.SWITCH_PLAYER: ['space'],
    ControlAction.SLIDE_TACKLE: ['q'],
    ControlAction.CONTAIN: ['f'],
    ControlAction.TEAM_PRESS: ['tab'],
    ControlAction.PAUSE: ['escape'],
    ControlAction.CAMERA_1: ['1'],
    ControlAction.CAMERA_2: ['2'],
    ControlAction.CAMERA_3: ['3'],
    ControlAction.CAMERA_4: ['4'],
    ControlAction.MINIMAP_TOGGLE: ['m'],
    ControlAction.REPLAY: ['v'],
}

# =============================================================================
# GAME STATES
# =============================================================================
class GameState(Enum):
    MAIN_MENU = auto()
    TEAM_SELECT = auto()
    FORMATION_SELECT = auto()
    MATCH_LOADING = auto()
    MATCH_INTRO = auto()
    MATCH_PLAYING = auto()
    MATCH_PAUSED = auto()
    MATCH_GOAL = auto()
    MATCH_HALFTIME = auto()
    MATCH_FULLTIME = auto()
    MATCH_EXTRA_TIME = auto()
    MATCH_PENALTIES = auto()
    SET_PIECE = auto()
    REPLAY_VIEW = auto()
    SETTINGS = auto()
    TOURNAMENT_MENU = auto()
    TOURNAMENT_BRACKET = auto()
    TOURNAMENT_TABLE = auto()
    CAREER_MENU = auto()

# =============================================================================
# TOURNAMENT SETTINGS
# =============================================================================
class TournamentType(Enum):
    FRIENDLY = auto()
    LEAGUE = auto()
    CUP = auto()
    CHAMPIONS_LEAGUE = auto()
    WORLD_CUP = auto()

LEAGUE_POINTS_WIN = 3
LEAGUE_POINTS_DRAW = 1
LEAGUE_POINTS_LOSS = 0

# =============================================================================
# COLOR DEFINITIONS
# =============================================================================
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_BLACK = (0.0, 0.0, 0.0)
COLOR_RED = (1.0, 0.15, 0.15)
COLOR_BLUE = (0.15, 0.15, 1.0)
COLOR_GREEN = (0.15, 0.8, 0.15)
COLOR_YELLOW = (1.0, 1.0, 0.15)
COLOR_ORANGE = (1.0, 0.6, 0.1)
COLOR_GOLD = (1.0, 0.84, 0.0)
COLOR_GRAY = (0.5, 0.5, 0.5)
COLOR_DARK_GRAY = (0.2, 0.2, 0.2)
COLOR_LIGHT_GRAY = (0.8, 0.8, 0.8)
COLOR_PITCH_GREEN = (0.18, 0.55, 0.15)
COLOR_PITCH_DARK = (0.14, 0.45, 0.12)
COLOR_SKY_BLUE = (0.53, 0.81, 0.92)
COLOR_NIGHT_SKY = (0.05, 0.05, 0.15)
COLOR_NET_WHITE = (0.95, 0.95, 0.95)
COLOR_BALL_WHITE = (1.0, 1.0, 1.0)

# =============================================================================
# DIFFICULTY MODIFIERS
# =============================================================================
DIFFICULTY_MODIFIERS = {
    'amateur': {
        'ai_speed': 0.80,
        'ai_accuracy': 0.65,
        'ai_reaction': 1.5,
        'ai_aggression': 0.5,
        'ai_positioning': 0.6,
        'player_speed_bonus': 1.1,
        'player_accuracy_bonus': 1.15,
        'gk_skill': 0.6,
        'foul_leniency': 1.3,
    },
    'semi_pro': {
        'ai_speed': 0.90,
        'ai_accuracy': 0.78,
        'ai_reaction': 1.2,
        'ai_aggression': 0.7,
        'ai_positioning': 0.75,
        'player_speed_bonus': 1.05,
        'player_accuracy_bonus': 1.08,
        'gk_skill': 0.75,
        'foul_leniency': 1.15,
    },
    'professional': {
        'ai_speed': 1.0,
        'ai_accuracy': 0.88,
        'ai_reaction': 1.0,
        'ai_aggression': 0.85,
        'ai_positioning': 0.88,
        'player_speed_bonus': 1.0,
        'player_accuracy_bonus': 1.0,
        'gk_skill': 0.88,
        'foul_leniency': 1.0,
    },
    'world_class': {
        'ai_speed': 1.05,
        'ai_accuracy': 0.94,
        'ai_reaction': 0.8,
        'ai_aggression': 0.95,
        'ai_positioning': 0.95,
        'player_speed_bonus': 0.97,
        'player_accuracy_bonus': 0.95,
        'gk_skill': 0.95,
        'foul_leniency': 0.9,
    },
    'legendary': {
        'ai_speed': 1.10,
        'ai_accuracy': 0.98,
        'ai_reaction': 0.6,
        'ai_aggression': 1.0,
        'ai_positioning': 1.0,
        'player_speed_bonus': 0.95,
        'player_accuracy_bonus': 0.90,
        'gk_skill': 1.0,
        'foul_leniency': 0.8,
    },
}

# =============================================================================
# ANIMATION TIMINGS
# =============================================================================
ANIM_KICK_DURATION = 0.3
ANIM_PASS_DURATION = 0.25
ANIM_HEADER_DURATION = 0.4
ANIM_SLIDE_DURATION = 0.7
ANIM_DIVE_DURATION = 0.8
ANIM_CELEBRATION_DURATION = 3.0
ANIM_THROW_IN_DURATION = 1.0
ANIM_CORNER_RUN_DURATION = 1.5
