"""
Ultimate Soccer 3D - AI Brain
Decision-making system for computer-controlled players.
"""
import math
import random
from ursina import Vec3
from config import (
    AIState, Position, PlayerAttribute, TeamTactic, MentalityLevel,
    AI_DECISION_INTERVAL, AI_PASS_DECISION_INTERVAL, AI_REACTION_TIME_MIN,
    AI_REACTION_TIME_MAX, AI_VISION_RANGE, AI_PRESS_DISTANCE, AI_MARK_DISTANCE,
    AI_SUPPORT_DISTANCE, AI_THROUGH_BALL_ANTICIPATION,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH, GOAL_HEIGHT,
    PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH,
    PLAYER_RUN_SPEED, PLAYER_SPRINT_SPEED,
    SHOOT_POWER_MAX, DRIBBLE_TOUCH_DISTANCE,
    DIFFICULTY_MODIFIERS,
)
from utils import (
    vec3_distance_xz, vec3_normalize_xz, vec3_normalize, vec3_length_xz,
    vec3_angle_xz, vec3_from_angle_xz, vec3_rotate_y,
    point_in_penalty_area, point_in_field, passing_lane_clear,
    find_nearest_player, find_players_in_radius, find_open_space,
    calculate_pass_target, calculate_intercept_point, expected_goals,
    goal_angle, is_offside_position,
    clamp, lerp, probability_check, attr_to_multiplier, gaussian_random,
    get_best_pass_target,
)
from player import PlayerState


class AIBrain:
    """AI decision-making for a single player."""

    def __init__(self, player, difficulty: str = 'professional'):
        self.player = player
        self.difficulty = difficulty
        self.modifiers = DIFFICULTY_MODIFIERS.get(difficulty, DIFFICULTY_MODIFIERS['professional'])

        # Decision timers
        self.decision_timer = 0.0
        self.decision_interval = AI_DECISION_INTERVAL
        self.reaction_delay = lerp(AI_REACTION_TIME_MAX, AI_REACTION_TIME_MIN,
                                    self.modifiers['ai_reaction'])
        self.pending_action = None
        self.pending_timer = 0.0

        # Current AI state
        self.state = AIState.IDLE
        self.previous_state = AIState.IDLE
        self.state_timer = 0.0

        # Targets
        self.target_position = None
        self.target_player = None
        self.mark_target = None

        # Awareness
        self.nearby_teammates = []
        self.nearby_opponents = []
        self.ball_distance = 999.0
        self.is_closest_to_ball = False
        self.is_closest_teammate = False

        # Tactical
        self.pressing_intensity = 0.5
        self.defensive_depth = 0.5
        self.width = 0.5
        self.risk_taking = 0.5

    def update(self, dt: float, ball, teammates: list, opponents: list,
               match_state, team_tactic: TeamTactic = TeamTactic.BALANCED):
        """Main AI update loop."""
        if self.player.is_sent_off:
            return
        if self.player.is_human_controlled:
            return
        if self.player.state_locked:
            return

        self.state_timer += dt
        self.decision_timer += dt

        # Update awareness
        self._update_awareness(ball, teammates, opponents)

        # Check if it's time to make a new decision
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0.0
            self._make_decision(ball, teammates, opponents, match_state, team_tactic)

        # Execute current state
        self._execute_state(dt, ball, teammates, opponents, match_state)

    def _update_awareness(self, ball, teammates, opponents):
        """Update what the AI player is aware of."""
        self.ball_distance = vec3_distance_xz(self.player.position, ball.position)

        vision = AI_VISION_RANGE * self.modifiers['ai_positioning']
        self.nearby_teammates = find_players_in_radius(
            self.player.position, teammates, vision, exclude=self.player)
        self.nearby_opponents = find_players_in_radius(
            self.player.position, opponents, vision)

        # Check if closest to ball
        min_dist = self.ball_distance
        self.is_closest_to_ball = True
        self.is_closest_teammate = True
        for t in teammates:
            if t == self.player or t.is_sent_off:
                continue
            d = vec3_distance_xz(t.position, ball.position)
            if d < min_dist:
                self.is_closest_to_ball = False
                if t.team_id == self.player.team_id:
                    self.is_closest_teammate = False
                min_dist = d

    def _make_decision(self, ball, teammates, opponents, match_state, tactic):
        """Main decision-making logic."""
        team_has_ball = ball.last_touched_team == self.player.team_id
        player_has_ball = self.player.has_ball

        if player_has_ball:
            self._decide_with_ball(ball, teammates, opponents, match_state, tactic)
        elif team_has_ball:
            self._decide_team_has_ball(ball, teammates, opponents, match_state, tactic)
        else:
            self._decide_defending(ball, teammates, opponents, match_state, tactic)

    def _decide_with_ball(self, ball, teammates, opponents, match_state, tactic):
        """Decision when player has the ball."""
        atk_dir = self.player.attacking_direction
        goal_pos = Vec3(atk_dir * FIELD_HALF_LENGTH, 1.0, 0)
        dist_to_goal = vec3_distance_xz(self.player.position, goal_pos)
        angle = goal_angle(self.player.position, atk_dir * FIELD_HALF_LENGTH)

        # In shooting range?
        in_box = point_in_penalty_area(self.player.position, atk_dir)
        xg = expected_goals(self.player.position, atk_dir * FIELD_HALF_LENGTH,
                            len(self.nearby_opponents))

        # Count nearby opponents
        close_opponents = find_players_in_radius(self.player.position, opponents, 4.0)
        pressure = len(close_opponents)

        # Shooting decision
        shoot_threshold = 0.12 * self.modifiers['ai_accuracy']
        if xg > shoot_threshold and dist_to_goal < 30:
            # Check if clear line to goal
            goal_target = Vec3(
                atk_dir * FIELD_HALF_LENGTH,
                random.uniform(0.5, GOAL_HEIGHT - 0.3),
                random.uniform(-GOAL_WIDTH / 2 + 0.5, GOAL_WIDTH / 2 - 0.5)
            )
            self._set_state(AIState.SHOOT)
            self.target_position = goal_target
            return

        # In box with good angle - shoot
        if in_box and angle > 0.15:
            goal_target = Vec3(
                atk_dir * FIELD_HALF_LENGTH,
                random.uniform(0.3, GOAL_HEIGHT - 0.3),
                random.uniform(-GOAL_WIDTH / 2 + 0.5, GOAL_WIDTH / 2 - 0.5)
            )
            self._set_state(AIState.SHOOT)
            self.target_position = goal_target
            return

        # Under pressure - pass
        if pressure >= 2:
            target = get_best_pass_target(self.player, teammates, opponents, ball.position)
            if target:
                self._set_state(AIState.PASS)
                self.target_player = target
                self.target_position = calculate_pass_target(
                    self.player.position, target.position,
                    target.velocity, 15.0
                )
                return

        # Cross opportunity (wide position near goal)
        if (abs(self.player.position.z) > 20 and
            abs(self.player.position.x - atk_dir * FIELD_HALF_LENGTH) < 25):
            # Look for players in box
            box_players = [t for t in teammates if t != self.player and
                          point_in_penalty_area(t.position, atk_dir)]
            if box_players:
                self._set_state(AIState.CROSS)
                self.target_player = random.choice(box_players)
                self.target_position = self.target_player.position
                return

        # Through ball opportunity
        if tactic in [TeamTactic.COUNTER_ATTACK, TeamTactic.ATTACKING]:
            for t in teammates:
                if t == self.player or t.is_goalkeeper:
                    continue
                if (t.position.x * atk_dir > self.player.position.x * atk_dir and
                    not is_offside_position(t.position, ball.position,
                                           [o.position for o in opponents], atk_dir)):
                    run_space = vec3_distance_xz(
                        t.position,
                        find_nearest_player(t.position, opponents, exclude=t)[0].position
                        if find_nearest_player(t.position, opponents)[0] else Vec3(999, 0, 999)
                    )
                    if run_space > 5 and probability_check(0.3 * self.modifiers['ai_accuracy']):
                        self._set_state(AIState.PASS)
                        self.target_player = t
                        lead = Vec3(
                            t.velocity.x * AI_THROUGH_BALL_ANTICIPATION + atk_dir * 5,
                            0,
                            t.velocity.z * AI_THROUGH_BALL_ANTICIPATION
                        )
                        self.target_position = Vec3(
                            t.position.x + lead.x,
                            0,
                            t.position.z + lead.z
                        )
                        return

        # Dribble forward if space
        forward_space = True
        check_pos = Vec3(
            self.player.position.x + atk_dir * 5,
            0,
            self.player.position.z
        )
        for opp in opponents:
            if vec3_distance_xz(check_pos, opp.position) < 3:
                forward_space = False
                break

        if forward_space and dist_to_goal > 15:
            dribble_attr = self.player.get_attr(PlayerAttribute.DRIBBLING)
            if probability_check(attr_to_multiplier(dribble_attr) * 0.6):
                self._set_state(AIState.DRIBBLE)
                self.target_position = Vec3(
                    self.player.position.x + atk_dir * 10,
                    0,
                    self.player.position.z + random.uniform(-5, 5)
                )
                return

        # Default: safe pass
        target = get_best_pass_target(self.player, teammates, opponents, ball.position)
        if target:
            self._set_state(AIState.PASS)
            self.target_player = target
            self.target_position = calculate_pass_target(
                self.player.position, target.position,
                target.velocity, 15.0
            )
        else:
            # No good pass - dribble
            self._set_state(AIState.DRIBBLE)
            self.target_position = Vec3(
                self.player.position.x + atk_dir * 8,
                0,
                self.player.position.z + random.uniform(-8, 8)
            )

    def _decide_team_has_ball(self, ball, teammates, opponents, match_state, tactic):
        """Decision when team has ball but this player doesn't."""
        atk_dir = self.player.attacking_direction
        ball_holder = next((t for t in teammates if t.has_ball), None)

        if not ball_holder:
            self._decide_defending(ball, teammates, opponents, match_state, tactic)
            return

        dist_to_ball = self.ball_distance
        dist_holder_to_goal = vec3_distance_xz(
            ball_holder.position,
            Vec3(atk_dir * FIELD_HALF_LENGTH, 0, 0)
        )

        # Make a run if attacker
        if self.player.role in [Position.ST, Position.CF, Position.LW, Position.RW]:
            if probability_check(0.5):
                self._set_state(AIState.MAKE_RUN)
                # Run into space
                target_x = self.player.formation_position.x + atk_dir * random.uniform(5, 15)
                target_z = self.player.position.z + random.uniform(-10, 10)
                target_x = clamp(target_x, -FIELD_HALF_LENGTH + 5, FIELD_HALF_LENGTH - 5)
                target_z = clamp(target_z, -FIELD_HALF_WIDTH + 3, FIELD_HALF_WIDTH - 3)

                # Check offside
                if not is_offside_position(
                    Vec3(target_x, 0, target_z), ball.position,
                    [o.position for o in opponents], atk_dir
                ):
                    self.target_position = Vec3(target_x, 0, target_z)
                    return

        # Support attack
        if dist_to_ball < AI_SUPPORT_DISTANCE:
            self._set_state(AIState.SUPPORT_ATTACK)
            # Find open space near ball
            space = find_open_space(ball.position, opponents + teammates, 15.0, 12)
            if point_in_field(space, -3):
                self.target_position = space
                return

        # Return to formation position
        self._set_state(AIState.HOLD_POSITION)
        # Shift formation forward
        shift = 0.3 if tactic in [TeamTactic.ATTACKING, TeamTactic.HIGH_PRESS] else 0.15
        self.target_position = Vec3(
            self.player.formation_position.x + atk_dir * shift * FIELD_HALF_LENGTH,
            0,
            self.player.formation_position.z
        )

    def _decide_defending(self, ball, teammates, opponents, match_state, tactic):
        """Decision when opponent has the ball."""
        atk_dir = self.player.attacking_direction
        own_goal = Vec3(-atk_dir * FIELD_HALF_LENGTH, 0, 0)

        # GK handled separately
        if self.player.is_goalkeeper:
            return

        # Closest to ball? Chase it
        if self.is_closest_teammate and self.ball_distance < AI_PRESS_DISTANCE * 2:
            self._set_state(AIState.PRESS_OPPONENT)
            self.target_position = ball.position
            return

        # High pressing tactic
        if tactic == TeamTactic.HIGH_PRESS:
            if self.ball_distance < AI_PRESS_DISTANCE * 1.5:
                self._set_state(AIState.PRESS_OPPONENT)
                self.target_position = ball.position
                return

        # Defender - track back
        if self.player.role in [Position.CB, Position.LB, Position.RB, Position.LWB, Position.RWB]:
            # Stay between ball and goal
            goal_to_ball = vec3_normalize_xz(Vec3(
                ball.position.x - own_goal.x, 0,
                ball.position.z - own_goal.z
            ))
            intercept_dist = min(
                vec3_distance_xz(own_goal, ball.position) * 0.4,
                vec3_distance_xz(self.player.position, own_goal)
            )
            target = Vec3(
                own_goal.x + goal_to_ball.x * intercept_dist,
                0,
                own_goal.z + goal_to_ball.z * intercept_dist
            )

            # Mark nearest opponent attacker
            nearest_opp, dist = find_nearest_player(
                self.player.position, opponents, max_distance=AI_MARK_DISTANCE * 3
            )
            if nearest_opp and dist < AI_MARK_DISTANCE * 2:
                self._set_state(AIState.MARK_PLAYER)
                self.mark_target = nearest_opp
                # Stay between opponent and goal
                to_goal = vec3_normalize_xz(Vec3(
                    own_goal.x - nearest_opp.position.x, 0,
                    own_goal.z - nearest_opp.position.z
                ))
                self.target_position = Vec3(
                    nearest_opp.position.x + to_goal.x * AI_MARK_DISTANCE,
                    0,
                    nearest_opp.position.z + to_goal.z * AI_MARK_DISTANCE
                )
                return

            self._set_state(AIState.TRACK_BACK)
            self.target_position = target
            return

        # Midfielder - help defend or cover space
        if self.player.role in [Position.CDM, Position.CM, Position.LM, Position.RM]:
            if self.ball_distance < AI_PRESS_DISTANCE:
                self._set_state(AIState.PRESS_OPPONENT)
                self.target_position = ball.position
                return
            else:
                self._set_state(AIState.COVER_SPACE)
                # Position between ball and formation pos
                mid_x = (self.player.formation_position.x + ball.position.x) * 0.5
                mid_z = (self.player.formation_position.z + ball.position.z) * 0.5
                self.target_position = Vec3(mid_x, 0, mid_z)
                return

        # Attackers - stay high for counter
        if tactic == TeamTactic.COUNTER_ATTACK:
            self._set_state(AIState.HOLD_POSITION)
            self.target_position = Vec3(
                self.player.formation_position.x,
                0,
                self.player.formation_position.z
            )
        else:
            # Come back to help
            self._set_state(AIState.TRACK_BACK)
            self.target_position = Vec3(
                self.player.formation_position.x - atk_dir * 8,
                0,
                self.player.formation_position.z
            )

    def _execute_state(self, dt: float, ball, teammates, opponents, match_state):
        """Execute the current AI state."""
        p = self.player

        if self.state == AIState.SHOOT:
            if p.has_ball and self.target_position:
                power = random.uniform(0.6, 0.95) * self.modifiers['ai_accuracy']
                p.initiate_shot(self.target_position, ball, power)
                self._set_state(AIState.IDLE)

        elif self.state == AIState.PASS:
            if p.has_ball and self.target_position:
                dist = vec3_distance_xz(p.position, self.target_position)
                power = clamp(dist / 40.0, 0.3, 0.9) * self.modifiers['ai_accuracy']
                p.initiate_pass(self.target_position, ball, power)
                self._set_state(AIState.IDLE)

        elif self.state == AIState.CROSS:
            if p.has_ball and self.target_position:
                power = random.uniform(0.5, 0.8) * self.modifiers['ai_accuracy']
                p.initiate_cross(self.target_position, ball, power)
                self._set_state(AIState.IDLE)

        elif self.state == AIState.DRIBBLE:
            if p.has_ball and self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                sprint = dist > 5.0
                p.move(direction, sprint)

                # Check if we should do a skill move
                close_opp = find_players_in_radius(p.position, opponents, 3.0)
                if close_opp and probability_check(0.02 * attr_to_multiplier(
                    p.get_attr(PlayerAttribute.DRIBBLING))):
                    p.initiate_skill_move(direction)

                if dist < 2.0:
                    self._set_state(AIState.IDLE)

        elif self.state in [AIState.CHASE_BALL, AIState.PRESS_OPPONENT]:
            target = self.target_position or ball.position
            # Predict ball position
            intercept = calculate_intercept_point(
                p.position, p.get_max_speed(), ball.position, ball.velocity
            )
            if intercept:
                target = intercept

            direction = vec3_normalize_xz(Vec3(
                target.x - p.position.x, 0, target.z - p.position.z
            ))
            dist = vec3_distance_xz(p.position, target)
            sprint = dist > 3.0

            p.move(direction, sprint)

            # Attempt tackle when close enough
            if dist < 2.5 and self.state == AIState.PRESS_OPPONENT:
                ball_holder = next((o for o in opponents if o.has_ball), None)
                if ball_holder and vec3_distance_xz(p.position, ball_holder.position) < 2.5:
                    should_slide = probability_check(0.2 * self.modifiers['ai_aggression'])
                    if probability_check(0.4 * self.modifiers['ai_aggression']):
                        p.initiate_tackle(ball_holder.position, is_slide=should_slide)

        elif self.state in [AIState.HOLD_POSITION, AIState.RETURN_TO_POSITION]:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                if dist > 2.0:
                    sprint = dist > 10.0
                    p.move(direction, sprint)
                else:
                    p.stop()

        elif self.state == AIState.SUPPORT_ATTACK:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                sprint = dist > 8.0
                p.move(direction, sprint)

        elif self.state == AIState.MAKE_RUN:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                p.move(direction, True)  # Always sprint on runs
                if dist < 3.0:
                    self._set_state(AIState.SUPPORT_ATTACK)
                    self.target_position = p.position

        elif self.state == AIState.MARK_PLAYER:
            if self.mark_target and self.target_position:
                # Update target pos to stay between opponent and goal
                atk_dir = p.attacking_direction
                own_goal = Vec3(-atk_dir * FIELD_HALF_LENGTH, 0, 0)
                to_goal = vec3_normalize_xz(Vec3(
                    own_goal.x - self.mark_target.position.x, 0,
                    own_goal.z - self.mark_target.position.z
                ))
                self.target_position = Vec3(
                    self.mark_target.position.x + to_goal.x * AI_MARK_DISTANCE,
                    0,
                    self.mark_target.position.z + to_goal.z * AI_MARK_DISTANCE
                )

                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                sprint = dist > 5.0
                p.move(direction, sprint)

        elif self.state == AIState.TRACK_BACK:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                sprint = dist > 8.0
                p.move(direction, sprint)

        elif self.state == AIState.COVER_SPACE:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                if dist > 2.0:
                    p.move(direction, dist > 8.0)
                else:
                    p.stop()

        elif self.state == AIState.INTERCEPT:
            intercept = calculate_intercept_point(
                p.position, p.get_max_speed(), ball.position, ball.velocity
            )
            if intercept:
                direction = vec3_normalize_xz(Vec3(
                    intercept.x - p.position.x, 0,
                    intercept.z - p.position.z
                ))
                p.move(direction, True)
            else:
                self._set_state(AIState.CHASE_BALL)

        elif self.state == AIState.CLEAR:
            if p.has_ball:
                # Clear ball upfield
                atk_dir = p.attacking_direction
                clear_target = Vec3(
                    atk_dir * 30 + p.position.x,
                    0,
                    random.uniform(-15, 15)
                )
                p.initiate_pass(clear_target, ball, 0.9, is_lob=True)
                self._set_state(AIState.IDLE)

        elif self.state == AIState.CELEBRATE:
            if not p.state == PlayerState.CELEBRATING:
                p.celebrate()

        elif self.state == AIState.SET_PIECE_POSITION:
            if self.target_position:
                direction = vec3_normalize_xz(Vec3(
                    self.target_position.x - p.position.x, 0,
                    self.target_position.z - p.position.z
                ))
                dist = vec3_distance_xz(p.position, self.target_position)
                if dist > 1.0:
                    p.move(direction, False)
                else:
                    p.stop()

        elif self.state == AIState.IDLE:
            p.stop()

    def _set_state(self, new_state: AIState):
        self.previous_state = self.state
        self.state = new_state
        self.state_timer = 0.0

    def force_state(self, state: AIState, target_pos: Vec3 = None, target_player=None):
        """Force a specific AI state (used for set pieces etc)."""
        self._set_state(state)
        self.target_position = target_pos
        self.target_player = target_player
        self.mark_target = target_player
