"""
Ultimate Soccer 3D - Goalkeeper AI
Specialized AI for goalkeeper positioning, diving, and distribution.
"""
import math
import random
from ursina import Vec3
from config import (
    Position, PlayerAttribute, AIState,
    GK_DIVE_SPEED, GK_DIVE_RANGE, GK_DIVE_DURATION, GK_DIVE_RECOVERY,
    GK_REACTION_TIME, GK_POSITIONING_SPEED, GK_RUSH_SPEED,
    GK_CATCH_RANGE, GK_PUNCH_RANGE, GK_PARRY_RANGE,
    GK_ONE_ON_ONE_RUSH_DISTANCE, GK_BOX_LIMIT_X, GK_BOX_LIMIT_Z,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH, GOAL_HEIGHT,
    PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH,
    DIFFICULTY_MODIFIERS, BALL_RADIUS,
)
from utils import (
    vec3_distance_xz, vec3_normalize, vec3_normalize_xz, vec3_length,
    vec3_length_xz, vec3_angle_xz, vec3_from_angle_xz,
    clamp, lerp, probability_check, attr_to_multiplier,
    point_in_penalty_area, predict_ball_position, calculate_intercept_point,
)
from player import PlayerState


class GoalkeeperAI:
    """Specialized AI controller for goalkeepers."""

    def __init__(self, player, difficulty: str = 'professional'):
        self.player = player
        self.difficulty = difficulty
        self.modifiers = DIFFICULTY_MODIFIERS.get(difficulty, DIFFICULTY_MODIFIERS['professional'])

        # State
        self.state = 'positioning'  # positioning, diving, rushing, holding, distributing
        self.state_timer = 0.0

        # Positioning
        self.ideal_position = Vec3(0, 0, 0)
        self.goal_center = Vec3(0, 0, 0)
        self.goal_line_x = 0.0
        self.side = 1  # 1 or -1

        # Shot detection
        self.shot_detected = False
        self.shot_direction = Vec3(0, 0, 0)
        self.reaction_timer = 0.0
        self.has_reacted = False

        # Distribution
        self.hold_timer = 0.0
        self.max_hold_time = 6.0

        # Rush
        self.rush_target = None
        self.is_rushing = False

        # Dive tracking
        self.dive_cooldown = 0.0
        self.last_dive_time = 0.0

    def setup(self, attacking_direction: int):
        """Setup GK for a match."""
        self.side = attacking_direction
        self.goal_line_x = -attacking_direction * FIELD_HALF_LENGTH
        self.goal_center = Vec3(self.goal_line_x, 0, 0)

    def update(self, dt: float, ball, teammates: list, opponents: list, match_state=None):
        """Main GK AI update."""
        if self.player.is_sent_off or self.player.is_human_controlled:
            return

        self.state_timer += dt
        if self.dive_cooldown > 0:
            self.dive_cooldown -= dt

        # Update ideal position
        self._calculate_ideal_position(ball, opponents)

        # State machine
        if self.player.state == PlayerState.GK_HOLDING:
            self._handle_holding(dt, ball, teammates, opponents)
        elif self.player.state == PlayerState.GK_DIVING:
            pass  # Let dive animation play out
        elif self.player.state_locked:
            pass  # Locked in animation
        elif self.state == 'rushing':
            self._handle_rushing(dt, ball, opponents)
        else:
            self._handle_positioning(dt, ball, teammates, opponents)

    def _calculate_ideal_position(self, ball, opponents):
        """Calculate where the GK should be standing."""
        # Base position on goal line
        base_x = self.goal_line_x + self.side * 2.0

        # Angle bisector between ball and goal posts
        ball_to_left_post = Vec3(
            self.goal_line_x - ball.position.x, 0,
            -GOAL_WIDTH / 2 - ball.position.z
        )
        ball_to_right_post = Vec3(
            self.goal_line_x - ball.position.x, 0,
            GOAL_WIDTH / 2 - ball.position.z
        )

        # Bisector direction
        norm_left = vec3_normalize_xz(ball_to_left_post)
        norm_right = vec3_normalize_xz(ball_to_right_post)
        bisector = vec3_normalize_xz(Vec3(
            norm_left.x + norm_right.x, 0,
            norm_left.z + norm_right.z
        ))

        # Distance from goal based on ball distance
        ball_dist = vec3_distance_xz(ball.position, self.goal_center)
        come_out_dist = clamp(ball_dist * 0.08, 0.5, 5.0)

        # If ball is close, come out more
        if ball_dist < 20:
            come_out_dist = clamp(ball_dist * 0.15, 1.0, 8.0)

        ideal_x = self.goal_line_x + self.side * come_out_dist
        ideal_z = clamp(ball.position.z * 0.3, -GOAL_WIDTH / 2 + 0.5, GOAL_WIDTH / 2 - 0.5)

        # Limit to penalty area
        if self.side > 0:
            ideal_x = clamp(ideal_x, -FIELD_HALF_LENGTH, -FIELD_HALF_LENGTH + PENALTY_AREA_LENGTH)
        else:
            ideal_x = clamp(ideal_x, FIELD_HALF_LENGTH - PENALTY_AREA_LENGTH, FIELD_HALF_LENGTH)

        self.ideal_position = Vec3(ideal_x, 0, ideal_z)

    def _handle_positioning(self, dt: float, ball, teammates, opponents):
        """Normal GK positioning."""
        # Move towards ideal position
        direction = vec3_normalize_xz(Vec3(
            self.ideal_position.x - self.player.position.x, 0,
            self.ideal_position.z - self.player.position.z
        ))
        dist = vec3_distance_xz(self.player.position, self.ideal_position)

        if dist > 0.5:
            speed_factor = min(1.0, dist / 5.0)
            self.player.move(Vec3(direction.x * speed_factor, 0, direction.z * speed_factor), dist > 5)
        else:
            self.player.stop()
            # Face the ball
            to_ball = vec3_normalize_xz(Vec3(
                ball.position.x - self.player.position.x, 0,
                ball.position.z - self.player.position.z
            ))
            self.player.facing_angle = vec3_angle_xz(to_ball)
            self.player.facing_direction = to_ball

        # Check for shots
        self._check_for_shots(ball, opponents)

        # Check for one-on-one rush
        self._check_rush_opportunity(ball, opponents)

        # Check for crosses
        self._check_for_crosses(ball, opponents)

    def _check_for_shots(self, ball, opponents):
        """Detect incoming shots and react."""
        if ball.shot_active and ball.speed > 8:
            # Ball heading towards goal?
            ball_heading = ball.is_heading_towards(self.goal_center, 0.5)
            if ball_heading:
                self._react_to_shot(ball)
                return

        # Check if ball is fast and heading this way
        if ball.speed > 12:
            predicted = ball.get_predicted_position(0.5)
            if abs(predicted.x - self.goal_line_x) < 5 and abs(predicted.z) < GOAL_WIDTH / 2 + 2:
                self._react_to_shot(ball)

    def _react_to_shot(self, ball):
        """React to an incoming shot."""
        if self.dive_cooldown > 0 or self.player.state_locked:
            return

        # Predict where ball will cross the goal line
        predicted = self._predict_shot_target(ball)
        if predicted is None:
            return

        # Calculate required dive
        dist_to_target = vec3_distance_xz(self.player.position, predicted)
        height_diff = predicted.y - self.player.position.y if predicted.y > 0 else 0

        # Reaction time based on difficulty and reflexes
        reflexes = self.player.get_attr(PlayerAttribute.GK_REFLEXES)
        reaction = GK_REACTION_TIME * (1.0 - attr_to_multiplier(reflexes) * 0.5)
        reaction *= self.modifiers.get('ai_reaction', 1.0)

        gk_skill = self.modifiers.get('gk_skill', 0.88)

        # Can we reach it?
        dive_range = GK_DIVE_RANGE * attr_to_multiplier(
            self.player.get_attr(PlayerAttribute.GK_DIVING))
        time_to_ball = ball.time_to_reach(Vec3(self.goal_line_x, 0, predicted.z))

        if time_to_ball < reaction:
            # Too fast to react
            if probability_check(0.1 * gk_skill):
                # Lucky reflex save
                pass
            else:
                return

        if dist_to_target < 1.5:
            # Just shift position and catch
            direction = vec3_normalize_xz(Vec3(
                predicted.x - self.player.position.x, 0,
                predicted.z - self.player.position.z
            ))
            self.player.move(direction, True)
        elif dist_to_target < dive_range:
            # Dive!
            dive_dir = vec3_normalize(Vec3(
                predicted.x - self.player.position.x,
                max(0, predicted.y - 0.5),
                predicted.z - self.player.position.z
            ))

            # Add difficulty-based accuracy
            if probability_check(gk_skill):
                self.player.gk_dive(dive_dir)
                self.dive_cooldown = GK_DIVE_RECOVERY
            else:
                # Dive slightly off
                offset = Vec3(
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.3, 0.3),
                    random.uniform(-0.5, 0.5)
                )
                adjusted_dir = vec3_normalize(Vec3(
                    dive_dir.x + offset.x,
                    dive_dir.y + offset.y,
                    dive_dir.z + offset.z
                ))
                self.player.gk_dive(adjusted_dir)
                self.dive_cooldown = GK_DIVE_RECOVERY

    def _predict_shot_target(self, ball) -> Vec3:
        """Predict where a shot will cross the goal line."""
        if abs(ball.velocity.x) < 0.5:
            return None

        # Time for ball to reach goal line
        dx = self.goal_line_x - ball.position.x
        if abs(ball.velocity.x) < 0.1:
            return None
        time_to_line = dx / ball.velocity.x

        if time_to_line < 0 or time_to_line > 3.0:
            return None

        predicted = ball.get_predicted_position(time_to_line)

        # Check if it would be on target
        if abs(predicted.z) > GOAL_WIDTH / 2 + 1.0:
            return None
        if predicted.y > GOAL_HEIGHT + 1.0 or predicted.y < -0.5:
            return None

        return predicted

    def _check_rush_opportunity(self, ball, opponents):
        """Check if GK should rush out for 1-on-1."""
        if self.player.state_locked:
            return

        ball_dist = vec3_distance_xz(ball.position, self.goal_center)

        # Is ball in dangerous zone and heading towards goal?
        if ball_dist < GK_ONE_ON_ONE_RUSH_DISTANCE:
            ball_carrier = None
            for opp in opponents:
                if opp.has_ball:
                    ball_carrier = opp
                    break

            if ball_carrier:
                carrier_dist = vec3_distance_xz(ball_carrier.position, self.goal_center)
                if carrier_dist < GK_ONE_ON_ONE_RUSH_DISTANCE:
                    # Check if it's a 1-on-1 (no defenders nearby)
                    from utils import find_players_in_radius
                    defenders_near = find_players_in_radius(
                        ball_carrier.position,
                        [t for t in self._get_team_players(ball_carrier) if not t.is_goalkeeper],
                        10.0
                    )
                    # Actually need teammates (not opponents) between carrier and goal
                    # This is the GK's teammates = defenders
                    # We approximate: if carrier is close and no one else is closer...
                    if carrier_dist < 18 and probability_check(0.3):
                        self.state = 'rushing'
                        self.rush_target = ball_carrier
                        self.player.is_rushing = True

    def _get_team_players(self, exclude_player):
        """Get other players on the same team. Simplified helper."""
        return []  # Team manager handles this

    def _handle_rushing(self, dt: float, ball, opponents):
        """Handle rushing out to close down attacker."""
        if self.rush_target is None or self.rush_target.is_sent_off:
            self.state = 'positioning'
            self.player.is_rushing = False
            return

        # Move towards ball/carrier
        target = ball.position
        direction = vec3_normalize_xz(Vec3(
            target.x - self.player.position.x, 0,
            target.z - self.player.position.z
        ))
        self.player.move(direction, True)

        # Close enough to make save?
        dist = vec3_distance_xz(self.player.position, ball.position)
        if dist < GK_CATCH_RANGE + 1.0:
            if ball.speed < 10:
                self.player.gk_catch(ball)
            else:
                self.player.gk_dive(direction)
            self.state = 'positioning'
            self.player.is_rushing = False
            return

        # Abort if too far from goal
        goal_dist = vec3_distance_xz(self.player.position, self.goal_center)
        if goal_dist > PENALTY_AREA_LENGTH + 3:
            self.state = 'positioning'
            self.player.is_rushing = False

    def _check_for_crosses(self, ball, opponents):
        """Check for incoming crosses and position to collect."""
        if not ball.cross_active:
            return

        # Predict where cross will land
        predicted = ball.get_predicted_position(1.0)

        # Is it coming into the box?
        if point_in_penalty_area(predicted, -self.side):
            dist = vec3_distance_xz(self.player.position, predicted)
            if dist < GK_PUNCH_RANGE + 3:
                # Come out for the cross
                direction = vec3_normalize_xz(Vec3(
                    predicted.x - self.player.position.x, 0,
                    predicted.z - self.player.position.z
                ))
                self.player.move(direction, True)

                # Close enough - punch or catch
                if dist < GK_PUNCH_RANGE:
                    # Decide catch vs punch
                    handling = self.player.get_attr(PlayerAttribute.GK_HANDLING)
                    if ball.speed < 15 and probability_check(attr_to_multiplier(handling)):
                        self.player.gk_catch(ball)
                    else:
                        self.player.gk_punch(ball)

    def _handle_holding(self, dt: float, ball, teammates, opponents):
        """Handle when GK is holding the ball."""
        self.hold_timer += dt

        # Wait a moment then distribute (must be less than GK_HOLDING lock duration of 1.0s)
        if self.hold_timer > 0.5:
            # Find best distribution target
            best_target = None
            best_score = -999

            for t in teammates:
                if t == self.player or t.is_goalkeeper:
                    continue

                dist = vec3_distance_xz(self.player.position, t.position)
                if dist < 5 or dist > 60:
                    continue

                # Score based on distance from opponents and forward position
                score = 0
                nearest_opp, opp_dist = find_nearest_player(t.position, opponents)
                if nearest_opp:
                    score += opp_dist * 2

                # Prefer players up field
                forward = t.position.x * self.side
                score += forward * 0.5

                if score > best_score:
                    best_score = score
                    best_target = t

            if best_target:
                dist = vec3_distance_xz(self.player.position, best_target.position)
                is_throw = dist < 25
                self.player.gk_distribute(best_target.position, ball, is_throw)
                self.hold_timer = 0
                self.state = 'positioning'
            elif self.hold_timer > 2.0:
                # Just boot it upfield
                target = Vec3(
                    self.side * 30,
                    0,
                    random.uniform(-15, 15)
                )
                self.player.gk_distribute(target, ball, is_throw=False)
                self.hold_timer = 0
                self.state = 'positioning'

    def force_position(self, pos: Vec3):
        """Force GK to a specific position (for set pieces)."""
        self.ideal_position = pos

    def on_goal_kick(self, ball, teammates):
        """Handle goal kick."""
        # Find a target
        best_target = None
        best_dist = 0
        for t in teammates:
            if t == self.player:
                continue
            dist = vec3_distance_xz(self.player.position, t.position)
            if 15 < dist < 45:
                if not best_target or dist > best_dist:
                    best_target = t
                    best_dist = dist

        if best_target:
            self.player.gk_distribute(best_target.position, ball, is_throw=False)
        else:
            # Boot it upfield
            target = Vec3(self.side * 35, 0, random.uniform(-15, 15))
            self.player.gk_distribute(target, ball, is_throw=False)

    def on_penalty_save(self, ball):
        """React to penalty kick."""
        # Random dive direction (simplified - in reality would read shooter)
        gk_skill = self.modifiers.get('gk_skill', 0.88)
        positioning = self.player.get_attr(PlayerAttribute.GK_POSITIONING)

        # Decide direction
        dive_z = random.choice([-1, 0, 1])
        dive_y = random.uniform(0, 1.5)

        if probability_check(gk_skill * 0.4):
            # "Read" the penalty - dive correct way
            pass  # Ball direction not known yet at dive time

        dive_dir = vec3_normalize(Vec3(0, dive_y, dive_z * GK_DIVE_RANGE))
        self.player.gk_dive(dive_dir)


def find_nearest_player(position, players, exclude=None, max_distance=999):
    """Find nearest player to a position."""
    nearest = None
    nearest_dist = max_distance
    for p in players:
        if p == exclude or p.is_sent_off:
            continue
        d = vec3_distance_xz(position, p.position)
        if d < nearest_dist:
            nearest = p
            nearest_dist = d
    return nearest, nearest_dist
