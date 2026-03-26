"""
Ultimate Soccer 3D - Formation Data
All formation definitions with player positions for attack, defense, and transitions.
Positions are normalized (-1 to 1) relative to the team's half.
"""
from config import Position

# =============================================================================
# FORMATION DEFINITIONS
# Each formation maps 10 outfield positions (GK is always fixed)
# Positions are (x_normalized, z_normalized) where:
#   x: -1.0 = own goal line, 1.0 = opponent goal line
#   z: -1.0 = left touchline, 1.0 = right touchline
# =============================================================================

FORMATIONS = {
    '4-4-2': {
        'name': '4-4-2',
        'description': 'Classic balanced formation',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.2, -0.8), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.35, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.35, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.2, 0.8), 'defense': (-0.8, 0.6)},
            {'role': Position.LM, 'base': (-0.15, -0.75), 'attack': (0.2, -0.85), 'defense': (-0.55, -0.7)},
            {'role': Position.CM, 'base': (-0.2, -0.2), 'attack': (0.1, -0.15), 'defense': (-0.5, -0.2)},
            {'role': Position.CM, 'base': (-0.2, 0.2), 'attack': (0.1, 0.15), 'defense': (-0.5, 0.2)},
            {'role': Position.RM, 'base': (-0.15, 0.75), 'attack': (0.2, 0.85), 'defense': (-0.55, 0.7)},
            {'role': Position.ST, 'base': (0.4, -0.2), 'attack': (0.7, -0.15), 'defense': (0.0, -0.2)},
            {'role': Position.ST, 'base': (0.4, 0.2), 'attack': (0.7, 0.15), 'defense': (0.0, 0.2)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.08,
            'ultra_attacking': 0.15,
        },
    },

    '4-3-3': {
        'name': '4-3-3',
        'description': 'Attacking formation with wingers',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.1, -0.85), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.35, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.35, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.1, 0.85), 'defense': (-0.8, 0.6)},
            {'role': Position.CM, 'base': (-0.25, -0.25), 'attack': (0.05, -0.2), 'defense': (-0.55, -0.25)},
            {'role': Position.CDM, 'base': (-0.35, 0.0), 'attack': (-0.1, 0.0), 'defense': (-0.6, 0.0)},
            {'role': Position.CM, 'base': (-0.25, 0.25), 'attack': (0.05, 0.2), 'defense': (-0.55, 0.25)},
            {'role': Position.LW, 'base': (0.25, -0.75), 'attack': (0.55, -0.8), 'defense': (-0.3, -0.75)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
            {'role': Position.RW, 'base': (0.25, 0.75), 'attack': (0.55, 0.8), 'defense': (-0.3, 0.75)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },

    '4-2-3-1': {
        'name': '4-2-3-1',
        'description': 'Modern balanced formation with CAM',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.15, -0.85), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.4, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.4, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.15, 0.85), 'defense': (-0.8, 0.6)},
            {'role': Position.CDM, 'base': (-0.35, -0.15), 'attack': (-0.15, -0.12), 'defense': (-0.6, -0.15)},
            {'role': Position.CDM, 'base': (-0.35, 0.15), 'attack': (-0.15, 0.12), 'defense': (-0.6, 0.15)},
            {'role': Position.LW, 'base': (0.15, -0.7), 'attack': (0.45, -0.75), 'defense': (-0.35, -0.7)},
            {'role': Position.CAM, 'base': (0.15, 0.0), 'attack': (0.4, 0.0), 'defense': (-0.2, 0.0)},
            {'role': Position.RW, 'base': (0.15, 0.7), 'attack': (0.45, 0.75), 'defense': (-0.35, 0.7)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.17,
        },
    },

    '3-5-2': {
        'name': '3-5-2',
        'description': 'Wing-back formation with 3 CBs',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.CB, 'base': (-0.65, -0.35), 'attack': (-0.4, -0.3), 'defense': (-0.82, -0.3)},
            {'role': Position.CB, 'base': (-0.7, 0.0), 'attack': (-0.45, 0.0), 'defense': (-0.85, 0.0)},
            {'role': Position.CB, 'base': (-0.65, 0.35), 'attack': (-0.4, 0.3), 'defense': (-0.82, 0.3)},
            {'role': Position.LWB, 'base': (-0.2, -0.85), 'attack': (0.2, -0.9), 'defense': (-0.65, -0.75)},
            {'role': Position.CM, 'base': (-0.2, -0.2), 'attack': (0.1, -0.15), 'defense': (-0.5, -0.2)},
            {'role': Position.CDM, 'base': (-0.3, 0.0), 'attack': (-0.05, 0.0), 'defense': (-0.55, 0.0)},
            {'role': Position.CM, 'base': (-0.2, 0.2), 'attack': (0.1, 0.15), 'defense': (-0.5, 0.2)},
            {'role': Position.RWB, 'base': (-0.2, 0.85), 'attack': (0.2, 0.9), 'defense': (-0.65, 0.75)},
            {'role': Position.ST, 'base': (0.4, -0.15), 'attack': (0.7, -0.12), 'defense': (0.0, -0.15)},
            {'role': Position.ST, 'base': (0.4, 0.15), 'attack': (0.7, 0.12), 'defense': (0.0, 0.15)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.12,
            'defensive': -0.06,
            'balanced': 0.0,
            'attacking': 0.08,
            'ultra_attacking': 0.15,
        },
    },

    '4-1-4-1': {
        'name': '4-1-4-1',
        'description': 'Defensive midfield anchor',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.15, -0.85), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.4, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.4, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.15, 0.85), 'defense': (-0.8, 0.6)},
            {'role': Position.CDM, 'base': (-0.4, 0.0), 'attack': (-0.2, 0.0), 'defense': (-0.65, 0.0)},
            {'role': Position.LM, 'base': (-0.1, -0.7), 'attack': (0.25, -0.8), 'defense': (-0.5, -0.65)},
            {'role': Position.CM, 'base': (-0.15, -0.15), 'attack': (0.15, -0.1), 'defense': (-0.45, -0.15)},
            {'role': Position.CM, 'base': (-0.15, 0.15), 'attack': (0.15, 0.1), 'defense': (-0.45, 0.15)},
            {'role': Position.RM, 'base': (-0.1, 0.7), 'attack': (0.25, 0.8), 'defense': (-0.5, 0.65)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },

    '4-3-2-1': {
        'name': '4-3-2-1 (Christmas Tree)',
        'description': 'Narrow attacking formation',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.2, -0.8), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.4, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.4, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.2, 0.8), 'defense': (-0.8, 0.6)},
            {'role': Position.CM, 'base': (-0.3, -0.25), 'attack': (-0.05, -0.2), 'defense': (-0.55, -0.25)},
            {'role': Position.CDM, 'base': (-0.35, 0.0), 'attack': (-0.1, 0.0), 'defense': (-0.6, 0.0)},
            {'role': Position.CM, 'base': (-0.3, 0.25), 'attack': (-0.05, 0.2), 'defense': (-0.55, 0.25)},
            {'role': Position.CAM, 'base': (0.1, -0.3), 'attack': (0.35, -0.25), 'defense': (-0.25, -0.3)},
            {'role': Position.CAM, 'base': (0.1, 0.3), 'attack': (0.35, 0.25), 'defense': (-0.25, 0.3)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },

    '5-3-2': {
        'name': '5-3-2',
        'description': 'Ultra-defensive with wing-backs',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LWB, 'base': (-0.45, -0.8), 'attack': (0.05, -0.85), 'defense': (-0.75, -0.7)},
            {'role': Position.CB, 'base': (-0.7, -0.3), 'attack': (-0.5, -0.25), 'defense': (-0.85, -0.28)},
            {'role': Position.CB, 'base': (-0.72, 0.0), 'attack': (-0.5, 0.0), 'defense': (-0.88, 0.0)},
            {'role': Position.CB, 'base': (-0.7, 0.3), 'attack': (-0.5, 0.25), 'defense': (-0.85, 0.28)},
            {'role': Position.RWB, 'base': (-0.45, 0.8), 'attack': (0.05, 0.85), 'defense': (-0.75, 0.7)},
            {'role': Position.CM, 'base': (-0.25, -0.25), 'attack': (0.05, -0.2), 'defense': (-0.5, -0.25)},
            {'role': Position.CM, 'base': (-0.25, 0.0), 'attack': (0.05, 0.0), 'defense': (-0.5, 0.0)},
            {'role': Position.CM, 'base': (-0.25, 0.25), 'attack': (0.05, 0.2), 'defense': (-0.5, 0.25)},
            {'role': Position.ST, 'base': (0.35, -0.15), 'attack': (0.65, -0.12), 'defense': (-0.05, -0.15)},
            {'role': Position.ST, 'base': (0.35, 0.15), 'attack': (0.65, 0.12), 'defense': (-0.05, 0.15)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.1,
            'defensive': -0.05,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },

    '4-4-1-1': {
        'name': '4-4-1-1',
        'description': 'Second striker behind lone forward',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.2, -0.8), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.4, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.4, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.2, 0.8), 'defense': (-0.8, 0.6)},
            {'role': Position.LM, 'base': (-0.15, -0.75), 'attack': (0.2, -0.85), 'defense': (-0.55, -0.7)},
            {'role': Position.CM, 'base': (-0.2, -0.15), 'attack': (0.1, -0.1), 'defense': (-0.5, -0.15)},
            {'role': Position.CM, 'base': (-0.2, 0.15), 'attack': (0.1, 0.1), 'defense': (-0.5, 0.15)},
            {'role': Position.RM, 'base': (-0.15, 0.75), 'attack': (0.2, 0.85), 'defense': (-0.55, 0.7)},
            {'role': Position.CF, 'base': (0.25, 0.0), 'attack': (0.5, 0.0), 'defense': (-0.1, 0.0)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },

    '3-4-3': {
        'name': '3-4-3',
        'description': 'Ultra-attacking with three forwards',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.CB, 'base': (-0.65, -0.35), 'attack': (-0.4, -0.3), 'defense': (-0.82, -0.3)},
            {'role': Position.CB, 'base': (-0.7, 0.0), 'attack': (-0.45, 0.0), 'defense': (-0.85, 0.0)},
            {'role': Position.CB, 'base': (-0.65, 0.35), 'attack': (-0.4, 0.3), 'defense': (-0.82, 0.3)},
            {'role': Position.LM, 'base': (-0.15, -0.8), 'attack': (0.15, -0.85), 'defense': (-0.55, -0.75)},
            {'role': Position.CM, 'base': (-0.25, -0.15), 'attack': (0.05, -0.1), 'defense': (-0.5, -0.15)},
            {'role': Position.CM, 'base': (-0.25, 0.15), 'attack': (0.05, 0.1), 'defense': (-0.5, 0.15)},
            {'role': Position.RM, 'base': (-0.15, 0.8), 'attack': (0.15, 0.85), 'defense': (-0.55, 0.75)},
            {'role': Position.LW, 'base': (0.3, -0.7), 'attack': (0.55, -0.75), 'defense': (-0.15, -0.7)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
            {'role': Position.RW, 'base': (0.3, 0.7), 'attack': (0.55, 0.75), 'defense': (-0.15, 0.7)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.18,
            'defensive': -0.1,
            'balanced': 0.0,
            'attacking': 0.08,
            'ultra_attacking': 0.15,
        },
    },

    '4-5-1': {
        'name': '4-5-1',
        'description': 'Packed midfield, lone striker',
        'positions': [
            {'role': Position.GK, 'base': (-0.95, 0.0), 'attack': (-0.88, 0.0), 'defense': (-0.97, 0.0)},
            {'role': Position.LB, 'base': (-0.6, -0.7), 'attack': (-0.2, -0.8), 'defense': (-0.8, -0.6)},
            {'role': Position.CB, 'base': (-0.65, -0.2), 'attack': (-0.4, -0.15), 'defense': (-0.82, -0.18)},
            {'role': Position.CB, 'base': (-0.65, 0.2), 'attack': (-0.4, 0.15), 'defense': (-0.82, 0.18)},
            {'role': Position.RB, 'base': (-0.6, 0.7), 'attack': (-0.2, 0.8), 'defense': (-0.8, 0.6)},
            {'role': Position.LM, 'base': (-0.15, -0.75), 'attack': (0.2, -0.85), 'defense': (-0.55, -0.7)},
            {'role': Position.CM, 'base': (-0.2, -0.2), 'attack': (0.1, -0.15), 'defense': (-0.5, -0.2)},
            {'role': Position.CAM, 'base': (-0.05, 0.0), 'attack': (0.3, 0.0), 'defense': (-0.35, 0.0)},
            {'role': Position.CM, 'base': (-0.2, 0.2), 'attack': (0.1, 0.15), 'defense': (-0.5, 0.2)},
            {'role': Position.RM, 'base': (-0.15, 0.75), 'attack': (0.2, 0.85), 'defense': (-0.55, 0.7)},
            {'role': Position.ST, 'base': (0.45, 0.0), 'attack': (0.75, 0.0), 'defense': (0.05, 0.0)},
        ],
        'mentality_offsets': {
            'ultra_defensive': -0.15,
            'defensive': -0.08,
            'balanced': 0.0,
            'attacking': 0.1,
            'ultra_attacking': 0.18,
        },
    },
}

# =============================================================================
# SET PIECE FORMATIONS
# =============================================================================

SET_PIECE_POSITIONS = {
    'corner_kick_attack': {
        'positions': [
            (-0.95, 0.0),    # GK stays
            (-0.3, -0.3),    # defender 1
            (-0.3, 0.3),     # defender 2
            (-0.2, 0.0),     # defender 3
            (-0.1, -0.5),    # defender 4
            (0.85, -0.15),   # near post
            (0.85, 0.15),    # far post
            (0.8, 0.0),      # center box
            (0.75, -0.3),    # edge of box
            (0.7, 0.3),      # edge of box
            (0.9, 0.0),      # penalty spot area
        ]
    },
    'corner_kick_defend': {
        'positions': [
            (-0.95, 0.0),    # GK on line
            (-0.88, -0.12),  # near post
            (-0.88, 0.12),   # far post
            (-0.85, 0.0),    # center
            (-0.82, -0.25),  # zone 1
            (-0.82, 0.25),   # zone 2
            (-0.78, 0.0),    # zone 3
            (-0.75, -0.15),  # edge
            (-0.75, 0.15),   # edge
            (-0.6, 0.0),     # outlet
            (-0.5, 0.3),     # counter outlet
        ]
    },
    'free_kick_attack': {
        'positions': [
            (-0.95, 0.0),
            (-0.4, -0.3),
            (-0.4, 0.3),
            (-0.35, 0.0),
            (-0.2, -0.4),
            (0.6, -0.15),   # near wall
            (0.6, 0.15),    # far wall
            (0.55, 0.0),    # center
            (0.65, -0.3),   # run in
            (0.65, 0.3),    # run in
            (0.5, 0.0),     # taker
        ]
    },
    'free_kick_defend_wall': {
        'count': 4,
        'spacing': 0.8,
    },
    'penalty_kick': {
        'taker': (0.85, 0.0),
        'gk': (-0.98, 0.0),
        'others_attack': [
            (-0.3, -0.3), (-0.3, 0.3), (-0.2, 0.0),
            (0.7, -0.5), (0.7, 0.5), (0.75, -0.3),
            (0.75, 0.3), (0.65, 0.0), (0.6, -0.4),
        ],
        'others_defend': [
            (-0.85, -0.5), (-0.85, 0.5), (-0.8, -0.3),
            (-0.8, 0.3), (-0.75, 0.0), (-0.7, -0.4),
            (-0.7, 0.4), (-0.65, -0.2), (-0.65, 0.2),
        ],
    },
    'goal_kick': {
        'positions': [
            (-0.95, 0.0),    # GK takes it
            (-0.5, -0.5),    # spread wide
            (-0.5, 0.5),
            (-0.45, -0.15),
            (-0.45, 0.15),
            (-0.1, -0.6),
            (-0.1, 0.6),
            (-0.05, -0.15),
            (-0.05, 0.15),
            (0.3, -0.2),
            (0.3, 0.2),
        ]
    },
    'throw_in': {
        'positions_near': [
            (-0.95, 0.0),
            (-0.5, -0.2),
            (-0.5, 0.2),
            (-0.3, 0.0),
            (-0.15, -0.4),
            (0.0, -0.7),     # short option
            (0.05, -0.5),    # medium option
            (0.1, -0.3),     # long option
            (0.0, 0.0),
            (0.3, -0.3),
            (0.3, 0.0),
        ]
    },
}

# =============================================================================
# FORMATION HELPER FUNCTIONS
# =============================================================================

def get_formation(name: str) -> dict:
    return FORMATIONS.get(name, FORMATIONS['4-4-2'])

def get_formation_names() -> list:
    return list(FORMATIONS.keys())

def get_position_for_player(formation: dict, player_index: int,
                             attacking_direction: int, phase: str = 'base',
                             mentality: str = 'balanced') -> tuple:
    if player_index >= len(formation['positions']):
        return (0, 0)

    pos_data = formation['positions'][player_index]
    if phase in pos_data:
        x, z = pos_data[phase]
    else:
        x, z = pos_data['base']

    mentality_offset = formation.get('mentality_offsets', {}).get(mentality, 0.0)
    x += mentality_offset

    x = max(-0.95, min(0.95, x))
    z = max(-0.95, min(0.95, z))

    if attacking_direction < 0:
        x = -x
        z = -z

    return (x, z)

def normalized_to_field(x_norm: float, z_norm: float) -> tuple:
    from config import FIELD_HALF_LENGTH, FIELD_HALF_WIDTH
    return (x_norm * FIELD_HALF_LENGTH, z_norm * FIELD_HALF_WIDTH)

def field_to_normalized(x: float, z: float) -> tuple:
    from config import FIELD_HALF_LENGTH, FIELD_HALF_WIDTH
    return (x / FIELD_HALF_LENGTH, z / FIELD_HALF_WIDTH)

def get_kickoff_positions(formation: dict, attacking_direction: int, has_kickoff: bool) -> list:
    positions = []
    for i, pos_data in enumerate(formation['positions']):
        x, z = pos_data['base']
        if has_kickoff:
            x = min(x, 0.02)
        else:
            x = min(x, -0.02)
        if attacking_direction < 0:
            x = -x
            z = -z
        positions.append(normalized_to_field(x, z))
    return positions

def get_set_piece_positions(piece_type: str, formation: dict,
                             attacking_direction: int, is_attacking: bool) -> list:
    key = piece_type
    if key not in SET_PIECE_POSITIONS:
        return get_kickoff_positions(formation, attacking_direction, False)

    sp = SET_PIECE_POSITIONS[key]
    positions = []
    for x, z in sp['positions']:
        if attacking_direction < 0:
            x = -x
            z = -z
        positions.append(normalized_to_field(x, z))
    return positions

def interpolate_formation_positions(base_positions: list, target_positions: list,
                                     t: float) -> list:
    result = []
    for i in range(min(len(base_positions), len(target_positions))):
        bx, bz = base_positions[i]
        tx, tz = target_positions[i]
        x = bx + (tx - bx) * t
        z = bz + (tz - bz) * t
        result.append((x, z))
    return result

def calculate_compactness(positions: list) -> float:
    if len(positions) < 2:
        return 0.0
    total_dist = 0.0
    count = 0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dx = positions[i][0] - positions[j][0]
            dz = positions[i][1] - positions[j][1]
            total_dist += (dx * dx + dz * dz) ** 0.5
            count += 1
    return total_dist / max(count, 1)

def get_defensive_line(formation: dict, attacking_direction: int) -> float:
    positions = formation['positions']
    defender_xs = []
    for pos_data in positions[1:]:
        if pos_data['role'] in [Position.CB, Position.LB, Position.RB, Position.LWB, Position.RWB]:
            x, _ = pos_data['defense']
            defender_xs.append(x)
    if not defender_xs:
        return -0.7
    avg_x = sum(defender_xs) / len(defender_xs)
    return avg_x * attacking_direction
