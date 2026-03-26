"""
Ultimate Soccer 3D - Referee System
Foul detection, cards, set pieces, offside, advantage play.
"""
import math
import random
from ursina import Vec3
from config import (
    FoulType, CardType, SetPieceType,
    FOUL_SEVERITY_THRESHOLD_YELLOW, FOUL_SEVERITY_THRESHOLD_RED,
    FOUL_ADVANTAGE_DURATION, FOUL_ADVANTAGE_DISTANCE,
    FOUL_FREE_KICK_WALL_DISTANCE, OFFSIDE_TOLERANCE,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH,
    PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH,
    Position, DIFFICULTY_MODIFIERS,
)
from utils import (
    vec3_distance_xz, vec3_normalize_xz, clamp,
    point_in_penalty_area, is_offside_position,
    probability_check,
)
from player import PlayerState


class FoulEvent:
    """Represents a foul event."""
    def __init__(self, foul_type, offender, victim, position, severity, card=CardType.NONE):
        self.foul_type = foul_type
        self.offender = offender
        self.victim = victim
        self.position = position
        self.severity = severity
        self.card = card
        self.advantage_playing = False
        self.advantage_timer = 0.0
        self.set_piece_type = SetPieceType.FREE_KICK
        self.set_piece_position = position
        self.is_penalty = False


class OffsideEvent:
    """Represents an offside call."""
    def __init__(self, player, position, pass_position):
        self.player = player
        self.position = position
        self.pass_position = pass_position


class Referee:
    """Manages all referee decisions during a match."""

    def __init__(self, difficulty: str = 'professional'):
        self.difficulty = difficulty
        self.modifiers = DIFFICULTY_MODIFIERS.get(difficulty, DIFFICULTY_MODIFIERS['professional'])
        self.leniency = self.modifiers.get('foul_leniency', 1.0)

        # Current state
        self.is_active = True
        self.whistle_blown = False
        self.current_set_piece = SetPieceType.NONE
        self.set_piece_position = Vec3(0, 0, 0)
        self.set_piece_team = None  # Team that gets the set piece
        self.set_piece_ready = False

        # Advantage
        self.advantage_active = False
        self.advantage_timer = 0.0
        self.advantage_team = None
        self.pending_foul = None

        # Offside tracking
        self.offside_check_active = False
        self.last_pass_positions = {}  # team_id -> list of defender positions at pass time
        self.last_pass_ball_pos = {}

        # Match events
        self.foul_log = []
        self.card_log = []
        self.offside_log = []

        # VAR (delayed review for tight calls)
        self.var_review_active = False
        self.var_timer = 0.0
        self.var_event = None

        # Stats
        self.total_fouls = 0
        self.total_yellows = 0
        self.total_reds = 0
        self.total_offsides = 0

    def update(self, dt: float, ball, home_team, away_team, match_state):
        """Main referee update loop."""
        if not self.is_active:
            return None

        events = []

        # Update advantage play
        if self.advantage_active:
            self.advantage_timer += dt
            if self.advantage_timer > FOUL_ADVANTAGE_DURATION:
                # Advantage over - was it beneficial?
                if self.pending_foul:
                    events.append(self._end_advantage(ball))
                self.advantage_active = False

        # Check for offside on passes
        if ball.pass_active and ball.frames_since_touch < 3:
            offside_event = self._check_offside(ball, home_team, away_team)
            if offside_event:
                events.append({'type': 'offside', 'event': offside_event})

        # VAR review
        if self.var_review_active:
            self.var_timer += dt
            if self.var_timer > 2.0:
                self.var_review_active = False
                if self.var_event:
                    events.append(self.var_event)
                    self.var_event = None

        return events if events else None

    def process_foul(self, offender, victim, severity: float, position: Vec3,
                      ball, attacking_team, defending_team) -> dict:
        """Process a foul event and determine punishment."""
        foul_type = self._determine_foul_type(offender, victim, severity)
        card = self._determine_card(offender, severity, position, attacking_team)

        # Apply leniency
        if self.leniency > 1.0 and severity < 0.5:
            if probability_check(0.3 * (self.leniency - 1.0)):
                return {'type': 'play_on', 'foul_type': FoulType.NO_FOUL}

        foul = FoulEvent(foul_type, offender, victim, position, severity, card)

        # Check if in penalty area
        atk_dir = attacking_team.attacking_direction if attacking_team else 1
        if point_in_penalty_area(position, atk_dir):
            foul.is_penalty = True
            foul.set_piece_type = SetPieceType.PENALTY
            foul.set_piece_position = Vec3(
                atk_dir * (FIELD_HALF_LENGTH - 11), 0, 0
            )
        else:
            foul.set_piece_type = SetPieceType.FREE_KICK
            foul.set_piece_position = Vec3(position.x, 0, position.z)

        # Check advantage
        if self._should_play_advantage(ball, attacking_team, position):
            foul.advantage_playing = True
            self.advantage_active = True
            self.advantage_timer = 0.0
            self.advantage_team = attacking_team
            self.pending_foul = foul
            return {
                'type': 'advantage',
                'foul': foul,
                'card': card,
            }

        # Apply card
        self._apply_card(offender, card)

        # Log
        self.foul_log.append(foul)
        self.total_fouls += 1

        # Set up set piece
        self.current_set_piece = foul.set_piece_type
        self.set_piece_position = foul.set_piece_position
        self.set_piece_team = attacking_team
        self.whistle_blown = True

        return {
            'type': 'foul',
            'foul': foul,
            'card': card,
            'set_piece': foul.set_piece_type,
            'position': foul.set_piece_position,
            'is_penalty': foul.is_penalty,
        }

    def _determine_foul_type(self, offender, victim, severity) -> FoulType:
        """Determine the type of foul."""
        if offender.state == PlayerState.SLIDE_TACKLING:
            if severity > 0.7:
                return FoulType.DANGEROUS_PLAY
            return FoulType.FOUL_TACKLE
        elif severity > 0.6:
            return FoulType.FOUL_PUSH
        elif severity > 0.4:
            return FoulType.FOUL_TRIP
        else:
            return FoulType.FOUL_TACKLE

    def _determine_card(self, offender, severity: float, position: Vec3,
                         attacking_team) -> CardType:
        """Determine if a card should be shown."""
        card = CardType.NONE

        # Already has yellow?
        has_yellow = offender.yellow_cards > 0

        # Professional foul (last man / denial of goal scoring opportunity)
        atk_dir = attacking_team.attacking_direction if attacking_team else 1
        is_last_man = abs(position.x - atk_dir * FIELD_HALF_LENGTH) < 25

        if severity >= FOUL_SEVERITY_THRESHOLD_RED:
            card = CardType.RED
        elif severity >= FOUL_SEVERITY_THRESHOLD_YELLOW:
            card = CardType.YELLOW
        elif is_last_man and severity > 0.3:
            card = CardType.YELLOW if not has_yellow else CardType.SECOND_YELLOW

        # Tactical foul (pulling back on counter)
        if offender.state == PlayerState.TACKLING and severity > 0.3:
            if probability_check(0.3):
                card = max(card, CardType.YELLOW, key=lambda x: x.value)

        # Second yellow = red
        if card == CardType.YELLOW and has_yellow:
            card = CardType.SECOND_YELLOW

        # Apply leniency
        if self.leniency > 1.0 and card == CardType.YELLOW:
            if probability_check(0.2 * (self.leniency - 1.0)):
                card = CardType.NONE

        return card

    def _apply_card(self, player, card: CardType):
        """Apply a card to a player."""
        if card == CardType.YELLOW:
            player.yellow_cards += 1
            self.total_yellows += 1
            self.card_log.append({'player': player, 'card': 'yellow'})
        elif card == CardType.SECOND_YELLOW:
            player.yellow_cards += 1
            player.red_cards += 1
            player.is_sent_off = True
            self.total_yellows += 1
            self.total_reds += 1
            self.card_log.append({'player': player, 'card': 'second_yellow'})
        elif card == CardType.RED:
            player.red_cards += 1
            player.is_sent_off = True
            self.total_reds += 1
            self.card_log.append({'player': player, 'card': 'red'})

        if player.is_sent_off:
            player.velocity = Vec3(0, 0, 0)
            player.stop()

    def _should_play_advantage(self, ball, attacking_team, foul_position) -> bool:
        """Determine if advantage should be played."""
        if not attacking_team:
            return False

        ball_holder = attacking_team.get_ball_holder()
        if not ball_holder:
            return False

        # Is ball moving forward towards goal?
        atk_dir = attacking_team.attacking_direction
        ball_moving_forward = ball.velocity.x * atk_dir > 2.0

        # Is holder in a good attacking position?
        dist_to_goal = abs(ball_holder.position.x - atk_dir * FIELD_HALF_LENGTH)
        in_good_position = dist_to_goal < 35

        return ball_moving_forward and in_good_position

    def _end_advantage(self, ball) -> dict:
        """End advantage play - either continue or bring back."""
        if self.pending_foul:
            foul = self.pending_foul
            self._apply_card(foul.offender, foul.card)
            self.foul_log.append(foul)
            self.total_fouls += 1

            # Advantage was not beneficial - bring back
            self.current_set_piece = foul.set_piece_type
            self.set_piece_position = foul.set_piece_position
            self.set_piece_team = self.advantage_team
            self.whistle_blown = True

            self.pending_foul = None
            self.advantage_team = None

            return {
                'type': 'advantage_over',
                'foul': foul,
                'set_piece': foul.set_piece_type,
            }
        return {'type': 'play_on'}

    def _check_offside(self, ball, home_team, away_team) -> OffsideEvent:
        """Check for offside when a pass is made."""
        passer = ball.last_touched_by
        if not passer:
            return None

        passer_team = home_team if passer.team_id == home_team.team_id else away_team
        defending_team = away_team if passer_team == home_team else home_team

        atk_dir = passer_team.attacking_direction

        # Get defender positions (excluding GK)
        defender_positions = [
            p.position for p in defending_team.players
            if not p.is_sent_off
        ]

        # Check each attacking player who might receive the ball
        for player in passer_team.players:
            if player == passer or player.is_goalkeeper or player.is_sent_off:
                continue

            # Is player in offside position?
            if is_offside_position(player.position, ball.position,
                                    defender_positions, atk_dir):
                # Is ball heading towards this player?
                if ball.is_heading_towards(player.position, 0.3):
                    # Is player in opponent's half?
                    in_opp_half = player.position.x * atk_dir > 0

                    if in_opp_half:
                        offside = OffsideEvent(player, player.position, ball.position)
                        self.offside_log.append(offside)
                        self.total_offsides += 1

                        if passer_team == home_team:
                            home_team.offsides += 1
                        else:
                            away_team.offsides += 1

                        # Set up free kick for defending team
                        self.current_set_piece = SetPieceType.FREE_KICK
                        self.set_piece_position = Vec3(player.position.x, 0, player.position.z)
                        self.set_piece_team = defending_team
                        self.whistle_blown = True

                        return offside

        return None

    def check_out_of_play(self, ball, home_team, away_team) -> dict:
        """Check if ball went out of play and determine restart."""
        result = {'restart': False}

        # Goal line
        if abs(ball.position.x) > FIELD_HALF_LENGTH + 1.0:
            side_x = 1 if ball.position.x > 0 else -1

            # Goal check
            if abs(ball.position.z) < GOAL_WIDTH / 2 and ball.position.y < 3.0:
                return {'restart': False, 'goal': True, 'side': side_x}

            # Who touched last?
            last_team = ball.last_touched_team

            if last_team == home_team.team_id:
                attacking_right = home_team.attacking_direction > 0
                if (side_x > 0 and attacking_right) or (side_x < 0 and not attacking_right):
                    # Goal kick for defending team
                    defending = away_team if side_x == home_team.attacking_direction else home_team
                    self.current_set_piece = SetPieceType.GOAL_KICK
                    self.set_piece_team = defending
                else:
                    # Corner for attacking team
                    attacking = home_team
                    self.current_set_piece = SetPieceType.CORNER_KICK
                    self.set_piece_team = attacking
                    if defending:
                        defending.corners += 0
                    attacking.corners += 1
            else:
                attacking_right = away_team.attacking_direction > 0
                if (side_x > 0 and attacking_right) or (side_x < 0 and not attacking_right):
                    defending = home_team if side_x == away_team.attacking_direction else away_team
                    self.current_set_piece = SetPieceType.GOAL_KICK
                    self.set_piece_team = defending
                else:
                    attacking = away_team
                    self.current_set_piece = SetPieceType.CORNER_KICK
                    self.set_piece_team = attacking
                    attacking.corners += 1

            side_z = 1 if ball.position.z > 0 else -1
            if self.current_set_piece == SetPieceType.GOAL_KICK:
                self.set_piece_position = Vec3(side_x * (FIELD_HALF_LENGTH - 5.5), 0, 0)
            elif self.current_set_piece == SetPieceType.CORNER_KICK:
                self.set_piece_position = Vec3(side_x * FIELD_HALF_LENGTH, 0,
                                                side_z * FIELD_HALF_WIDTH)

            self.whistle_blown = True
            result['restart'] = True
            result['type'] = self.current_set_piece
            return result

        # Touchline
        if abs(ball.position.z) > FIELD_HALF_WIDTH + 0.5:
            side_z = 1 if ball.position.z > 0 else -1
            last_team = ball.last_touched_team

            # Throw-in for other team
            if last_team == home_team.team_id:
                self.set_piece_team = away_team
            else:
                self.set_piece_team = home_team

            self.current_set_piece = SetPieceType.THROW_IN
            self.set_piece_position = Vec3(
                clamp(ball.position.x, -FIELD_HALF_LENGTH + 1, FIELD_HALF_LENGTH - 1),
                0,
                side_z * FIELD_HALF_WIDTH
            )
            self.whistle_blown = True
            result['restart'] = True
            result['type'] = SetPieceType.THROW_IN
            return result

        return result

    def setup_set_piece(self, piece_type: SetPieceType, position: Vec3,
                         team, ball) -> dict:
        """Set up a set piece restart."""
        self.current_set_piece = piece_type
        self.set_piece_position = position
        self.set_piece_team = team

        ball.reset(position)
        ball.is_in_play = False

        return {
            'type': piece_type,
            'position': position,
            'team': team,
        }

    def execute_set_piece(self, ball):
        """Mark set piece as ready to be taken."""
        self.set_piece_ready = True
        ball.is_in_play = True
        self.whistle_blown = False

    def clear_set_piece(self):
        """Clear current set piece state."""
        self.current_set_piece = SetPieceType.NONE
        self.set_piece_position = Vec3(0, 0, 0)
        self.set_piece_team = None
        self.set_piece_ready = False
        self.whistle_blown = False

    def get_wall_positions(self, free_kick_pos: Vec3, goal_pos: Vec3,
                            num_players: int = 4) -> list:
        """Calculate positions for a defensive wall."""
        direction = vec3_normalize_xz(Vec3(
            goal_pos.x - free_kick_pos.x, 0,
            goal_pos.z - free_kick_pos.z
        ))

        wall_center = Vec3(
            free_kick_pos.x + direction.x * FOUL_FREE_KICK_WALL_DISTANCE,
            0,
            free_kick_pos.z + direction.z * FOUL_FREE_KICK_WALL_DISTANCE
        )

        # Perpendicular direction
        perp = Vec3(-direction.z, 0, direction.x)
        positions = []
        spacing = 0.8
        start_offset = -(num_players - 1) * spacing / 2

        for i in range(num_players):
            offset = start_offset + i * spacing
            pos = Vec3(
                wall_center.x + perp.x * offset,
                0,
                wall_center.z + perp.z * offset
            )
            positions.append(pos)

        return positions

    def is_dangerous_free_kick(self, position: Vec3, attacking_direction: int) -> bool:
        """Check if a free kick is in a dangerous position."""
        goal_x = attacking_direction * FIELD_HALF_LENGTH
        dist = vec3_distance_xz(position, Vec3(goal_x, 0, 0))
        return dist < 30 and abs(position.z) < FIELD_HALF_WIDTH * 0.6
