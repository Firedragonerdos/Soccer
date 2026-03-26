"""
Ultimate Soccer 3D - Team Manager
Team-level AI, formation management, tactics, and player coordination.
"""
import math
import random
from ursina import Vec3
from config import (
    Position, PlayerAttribute, TeamTactic, MentalityLevel, AIState,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, PENALTY_AREA_LENGTH,
    DIFFICULTY_MODIFIERS, AI_OFFSIDE_TRAP_LINE,
)
from formations import (
    get_formation, normalized_to_field, get_position_for_player,
    get_kickoff_positions, get_set_piece_positions, FORMATIONS,
)
from player import Player, PlayerState
from ai_brain import AIBrain
from goalkeeper import GoalkeeperAI
from teams_data import get_team, get_player_attribute
from utils import (
    vec3_distance_xz, vec3_normalize_xz, clamp, lerp,
    find_nearest_player, find_players_in_radius,
)


class TeamManager:
    """Manages a team of players, their formation, tactics, and AI."""

    def __init__(self, team_id: str, attacking_direction: int,
                 is_human: bool = False, difficulty: str = 'professional'):
        self.team_id = team_id
        self.attacking_direction = attacking_direction  # 1=right, -1=left
        self.is_human = is_human
        self.difficulty = difficulty
        self.modifiers = DIFFICULTY_MODIFIERS.get(difficulty, DIFFICULTY_MODIFIERS['professional'])

        # Load team data
        self.team_data = get_team(team_id)
        self.team_name = self.team_data['name'] if self.team_data else 'Unknown'
        self.team_color = self.team_data.get('home_color', (1, 1, 1)) if self.team_data else (1, 1, 1)
        self.gk_color = self.team_data.get('gk_color', (0.2, 0.8, 0.2)) if self.team_data else (0.2, 0.8, 0.2)

        # Formation
        formation_name = self.team_data.get('formation', '4-4-2') if self.team_data else '4-4-2'
        self.formation = get_formation(formation_name)
        self.formation_name = formation_name

        # Tactics
        tactic_name = self.team_data.get('tactic', 'balanced') if self.team_data else 'balanced'
        self.tactic = TeamTactic.BALANCED
        tactic_map = {
            'balanced': TeamTactic.BALANCED,
            'attacking': TeamTactic.ATTACKING,
            'defensive': TeamTactic.DEFENSIVE,
            'counter_attack': TeamTactic.COUNTER_ATTACK,
            'high_press': TeamTactic.HIGH_PRESS,
            'park_the_bus': TeamTactic.PARK_THE_BUS,
            'tiki_taka': TeamTactic.TIKI_TAKA,
            'long_ball': TeamTactic.LONG_BALL,
            'wing_play': TeamTactic.WING_PLAY,
        }
        self.tactic = tactic_map.get(tactic_name, TeamTactic.BALANCED)
        self.mentality = MentalityLevel.BALANCED

        # Players
        self.players = []
        self.goalkeeper = None
        self.captain = None
        self.selected_player = None  # Human controlled player
        self.ai_brains = {}
        self.gk_ai = None

        # Substitutions
        self.substitutes = []
        self.subs_made = 0
        self.max_subs = 5

        # Team state
        self.has_possession = False
        self.possession_time = 0.0
        self.total_time = 0.0
        self.defensive_line = 0.0

        # Match stats
        self.goals_scored = 0
        self.goals_conceded = 0
        self.shots_total = 0
        self.shots_on_target = 0
        self.passes_total = 0
        self.passes_completed = 0
        self.fouls = 0
        self.corners = 0
        self.offsides = 0
        self.yellow_cards = 0
        self.red_cards = 0

        # Tactical adjustments
        self.pressing_intensity = 0.5
        self.defensive_width = 0.5
        self.attacking_width = 0.5
        self.tempo = 0.5

        self._apply_tactic_settings()

    def _apply_tactic_settings(self):
        """Apply tactic-specific settings."""
        if self.tactic == TeamTactic.HIGH_PRESS:
            self.pressing_intensity = 0.9
            self.defensive_width = 0.6
            self.tempo = 0.8
        elif self.tactic == TeamTactic.PARK_THE_BUS:
            self.pressing_intensity = 0.2
            self.defensive_width = 0.3
            self.tempo = 0.3
        elif self.tactic == TeamTactic.TIKI_TAKA:
            self.pressing_intensity = 0.7
            self.defensive_width = 0.5
            self.attacking_width = 0.4
            self.tempo = 0.7
        elif self.tactic == TeamTactic.COUNTER_ATTACK:
            self.pressing_intensity = 0.4
            self.defensive_width = 0.4
            self.tempo = 0.9
        elif self.tactic == TeamTactic.LONG_BALL:
            self.pressing_intensity = 0.5
            self.tempo = 0.6
        elif self.tactic == TeamTactic.WING_PLAY:
            self.attacking_width = 0.9
            self.defensive_width = 0.6
        elif self.tactic == TeamTactic.ATTACKING:
            self.pressing_intensity = 0.6
            self.tempo = 0.7
            self.mentality = MentalityLevel.ATTACKING
        elif self.tactic == TeamTactic.DEFENSIVE:
            self.pressing_intensity = 0.4
            self.tempo = 0.4
            self.mentality = MentalityLevel.DEFENSIVE

    def create_players(self):
        """Create all player entities from team data."""
        if not self.team_data:
            return

        player_list = self.team_data.get('players', [])[:11]

        for i, pdata in enumerate(player_list):
            is_gk = pdata['position'] == Position.GK
            team_col = self.gk_color if is_gk else self.team_color

            player = Player(
                name=pdata['name'],
                number=pdata['number'],
                position=pdata['position'],
                team_id=self.team_id,
                team_color=team_col,
                rating=pdata.get('rating', 70),
                attrs=pdata.get('attrs', {}),
                is_gk=is_gk,
            )
            player.attacking_direction = self.attacking_direction
            self.players.append(player)

            if is_gk:
                self.goalkeeper = player
                self.gk_ai = GoalkeeperAI(player, self.difficulty)
                self.gk_ai.setup(self.attacking_direction)
            else:
                brain = AIBrain(player, self.difficulty)
                self.ai_brains[player.id] = brain

        # Set captain
        if self.players:
            self.captain = self.players[0]
            for p in self.players:
                if p.role in [Position.CB, Position.CM, Position.CDM]:
                    self.captain = p
                    break

        # Load substitutes
        for sdata in self.team_data.get('subs', []):
            self.substitutes.append(sdata)

        # Select first outfield player for human
        if self.is_human and len(self.players) > 1:
            self.select_player(self.players[1])

    def set_formation_positions(self, phase: str = 'base'):
        """Place all players at their formation positions."""
        mentality_str = 'balanced'
        if self.mentality == MentalityLevel.ULTRA_DEFENSIVE:
            mentality_str = 'ultra_defensive'
        elif self.mentality == MentalityLevel.DEFENSIVE:
            mentality_str = 'defensive'
        elif self.mentality == MentalityLevel.ATTACKING:
            mentality_str = 'attacking'
        elif self.mentality == MentalityLevel.ULTRA_ATTACKING:
            mentality_str = 'ultra_attacking'

        for i, player in enumerate(self.players):
            if i >= len(self.formation['positions']):
                break

            x_norm, z_norm = get_position_for_player(
                self.formation, i, self.attacking_direction, phase, mentality_str
            )
            x, z = normalized_to_field(x_norm, z_norm)

            player.formation_position = Vec3(x, 0, z)
            player.set_position(Vec3(x, 0, z))

            # Face the right direction
            player.set_facing(math.pi / 2 * self.attacking_direction if self.attacking_direction > 0 else -math.pi / 2)

    def set_kickoff_positions(self, has_kickoff: bool):
        """Place players for kickoff."""
        positions = get_kickoff_positions(self.formation, self.attacking_direction, has_kickoff)
        for i, player in enumerate(self.players):
            if i < len(positions):
                x, z = positions[i]
                player.formation_position = Vec3(x, 0, z)
                player.set_position(Vec3(x, 0, z))
                facing = 0 if has_kickoff else math.pi
                player.set_facing(facing)

    def update(self, dt: float, ball, opponent_team, match_state=None):
        """Update all team systems."""
        self.total_time += dt

        # Update possession tracking
        had_possession = self.has_possession
        if ball.last_touched_team == self.team_id:
            self.has_possession = True
            self.possession_time += dt
        else:
            self.has_possession = False

        # Auto-switch to nearest player when possession is lost (human team)
        if self.is_human and had_possession and not self.has_possession:
            self.select_nearest_to_ball(ball)

        # Also auto-switch if selected player is too far from ball and doesn't have it
        if (self.is_human and self.selected_player
                and not self.selected_player.has_ball
                and not self.has_possession):
            dist_to_ball = vec3_distance_xz(self.selected_player.position, ball.position)
            if dist_to_ball > 25.0:
                self.select_nearest_to_ball(ball)

        opponents = opponent_team.players if opponent_team else []

        # Update formation positions based on ball position
        self._update_formation_shift(ball)

        # Update GK AI
        if self.gk_ai and self.goalkeeper and not self.goalkeeper.is_sent_off:
            self.gk_ai.update(dt, ball, self.players, opponents, match_state)

        # Update outfield AI
        for player in self.players:
            if player.is_goalkeeper or player.is_sent_off:
                continue

            brain = self.ai_brains.get(player.id)
            if brain and not player.is_human_controlled:
                brain.update(dt, ball, self.players, opponents, match_state, self.tactic)

            # Update player physics
            player.update(dt)

        # Update goalkeeper
        if self.goalkeeper and not self.goalkeeper.is_sent_off:
            self.goalkeeper.update(dt)

    def _update_formation_shift(self, ball):
        """Shift formation based on ball position."""
        # Lateral shift
        lateral_shift = clamp(ball.position.z / FIELD_HALF_WIDTH * 0.3, -0.3, 0.3)

        # Vertical shift based on possession
        if self.has_possession:
            vertical_shift = 0.1  # Push up
        else:
            vertical_shift = -0.05  # Drop back

        mentality_str = 'balanced'
        if self.mentality == MentalityLevel.ULTRA_DEFENSIVE:
            mentality_str = 'ultra_defensive'
        elif self.mentality == MentalityLevel.DEFENSIVE:
            mentality_str = 'defensive'
        elif self.mentality == MentalityLevel.ATTACKING:
            mentality_str = 'attacking'
        elif self.mentality == MentalityLevel.ULTRA_ATTACKING:
            mentality_str = 'ultra_attacking'

        phase = 'attack' if self.has_possession else 'defense'

        for i, player in enumerate(self.players):
            if player.is_goalkeeper or player.is_human_controlled:
                continue
            if i >= len(self.formation['positions']):
                break

            x_norm, z_norm = get_position_for_player(
                self.formation, i, self.attacking_direction, phase, mentality_str
            )

            # Apply shifts
            x_norm += vertical_shift * self.attacking_direction
            z_norm += lateral_shift

            x_norm = clamp(x_norm, -0.95, 0.95)
            z_norm = clamp(z_norm, -0.95, 0.95)

            x, z = normalized_to_field(x_norm, z_norm)
            player.formation_position = Vec3(x, 0, z)

    def select_player(self, player: Player):
        """Select a player for human control."""
        if self.selected_player:
            self.selected_player.select(False)
        self.selected_player = player
        if player:
            player.select(True)

    def select_nearest_to_ball(self, ball):
        """Select the player nearest to the ball."""
        nearest = None
        nearest_dist = float('inf')
        for p in self.players:
            if p.is_goalkeeper or p.is_sent_off:
                continue
            d = vec3_distance_xz(p.position, ball.position)
            if d < nearest_dist:
                nearest = p
                nearest_dist = d
        if nearest:
            self.select_player(nearest)

    def cycle_selected_player(self, ball):
        """Cycle to next player nearest to ball."""
        if not self.selected_player:
            self.select_nearest_to_ball(ball)
            return

        players_by_dist = sorted(
            [(p, vec3_distance_xz(p.position, ball.position))
             for p in self.players if not p.is_goalkeeper and not p.is_sent_off],
            key=lambda x: x[1]
        )

        current_idx = -1
        for i, (p, d) in enumerate(players_by_dist):
            if p == self.selected_player:
                current_idx = i
                break

        next_idx = (current_idx + 1) % len(players_by_dist)
        self.select_player(players_by_dist[next_idx][0])

    def get_ball_holder(self):
        """Get the player who currently has the ball."""
        for p in self.players:
            if p.has_ball:
                return p
        return None

    def change_tactic(self, tactic: TeamTactic):
        """Change team tactic mid-game."""
        self.tactic = tactic
        self._apply_tactic_settings()

    def change_mentality(self, mentality: MentalityLevel):
        """Change team mentality."""
        self.mentality = mentality

    def change_formation(self, formation_name: str):
        """Change formation mid-game."""
        self.formation = get_formation(formation_name)
        self.formation_name = formation_name

    def make_substitution(self, player_out_idx: int, sub_idx: int) -> bool:
        """Make a substitution."""
        if self.subs_made >= self.max_subs:
            return False
        if player_out_idx >= len(self.players) or sub_idx >= len(self.substitutes):
            return False

        player_out = self.players[player_out_idx]
        sub_data = self.substitutes[sub_idx]

        # Create new player entity
        is_gk = sub_data['position'] == Position.GK
        team_col = self.gk_color if is_gk else self.team_color

        new_player = Player(
            name=sub_data['name'],
            number=sub_data['number'],
            position=sub_data['position'],
            team_id=self.team_id,
            team_color=team_col,
            rating=sub_data.get('rating', 70),
            attrs=sub_data.get('attrs', {}),
            is_gk=is_gk,
        )
        new_player.attacking_direction = self.attacking_direction
        new_player.set_position(player_out.position)
        new_player.formation_position = player_out.formation_position

        # Remove old player
        player_out.cleanup()
        if player_out == self.selected_player:
            self.selected_player = None

        # Remove old brain
        if player_out.id in self.ai_brains:
            del self.ai_brains[player_out.id]

        # Add new player
        self.players[player_out_idx] = new_player
        brain = AIBrain(new_player, self.difficulty)
        self.ai_brains[new_player.id] = brain

        if is_gk:
            self.goalkeeper = new_player
            self.gk_ai = GoalkeeperAI(new_player, self.difficulty)
            self.gk_ai.setup(self.attacking_direction)

        self.substitutes.pop(sub_idx)
        self.subs_made += 1
        return True

    def set_piece_positions(self, piece_type: str, is_attacking: bool, ball_pos: Vec3):
        """Position players for a set piece."""
        positions = get_set_piece_positions(
            piece_type, self.formation, self.attacking_direction, is_attacking
        )
        for i, player in enumerate(self.players):
            if i < len(positions):
                x, z = positions[i]
                brain = self.ai_brains.get(player.id)
                if brain:
                    brain.force_state(AIState.SET_PIECE_POSITION, Vec3(x, 0, z))

    def celebrate_goal(self, scorer=None):
        """All players celebrate a goal."""
        for player in self.players:
            if player.is_sent_off:
                continue
            player.celebrate()
            brain = self.ai_brains.get(player.id)
            if brain:
                brain.force_state(AIState.CELEBRATE)

    def get_defensive_line_x(self) -> float:
        """Get the x-position of the defensive line."""
        defenders = [p for p in self.players
                     if p.role in [Position.CB, Position.LB, Position.RB, Position.LWB, Position.RWB]
                     and not p.is_sent_off]
        if not defenders:
            return -self.attacking_direction * FIELD_HALF_LENGTH * 0.7

        positions = [p.position.x for p in defenders]
        if self.attacking_direction > 0:
            return min(positions)
        else:
            return max(positions)

    def get_stats(self) -> dict:
        """Get team match statistics."""
        stats = {
            'goals': self.goals_scored,
            'goals_conceded': self.goals_conceded,
            'possession': self.possession_time / max(self.total_time, 1) * 100,
            'shots': sum(p.shots for p in self.players),
            'shots_on_target': self.shots_on_target,
            'passes': sum(p.passes_attempted for p in self.players),
            'passes_completed': sum(p.passes_completed for p in self.players),
            'tackles': sum(p.tackles_attempted for p in self.players),
            'tackles_won': sum(p.tackles_won for p in self.players),
            'fouls': sum(p.fouls_committed for p in self.players),
            'yellow_cards': sum(p.yellow_cards for p in self.players),
            'red_cards': sum(p.red_cards for p in self.players),
            'corners': self.corners,
            'offsides': self.offsides,
        }
        return stats

    def cleanup(self):
        """Clean up all player entities."""
        for player in self.players:
            player.cleanup()
        self.players.clear()
        self.ai_brains.clear()
