"""
Ultimate Soccer 3D - Player Controller
Human input handling for controlling players.
"""
import math
from ursina import Vec3, held_keys, time as ursina_time
from config import (
    ControlAction, DEFAULT_CONTROLS, GameState, SetPieceType,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH, GOAL_HEIGHT,
    DRIBBLE_TOUCH_DISTANCE,
)
from utils import (
    vec3_distance_xz, vec3_normalize_xz, vec3_normalize, vec3_length_xz,
    vec3_angle_xz, clamp, find_nearest_player,
)
from player import PlayerState


class PlayerController:
    """Handles human input for controlling a team's players."""

    def __init__(self, team_manager, camera_system):
        self.team = team_manager
        self.camera = camera_system

        # Input state
        self.move_input = Vec3(0, 0, 0)
        self.is_sprinting = False
        self.is_charging_pass = False
        self.is_charging_shot = False
        self.charge_timer = 0.0

        # Action cooldowns
        self.switch_cooldown = 0.0
        self.tackle_cooldown = 0.0
        self.skill_cooldown = 0.0
        self.action_cooldown = 0.0

        # Context
        self.has_ball = False
        self.nearest_opponent = None
        self.nearest_opponent_dist = 999.0

        # Double-tap tracking
        self.last_key_time = {}
        self.double_tap_window = 0.3

    @property
    def controlled_player(self):
        return self.team.selected_player

    def update(self, dt: float, ball, opponent_team):
        """Process input and control selected player."""
        if not self.controlled_player:
            return

        # Update cooldowns
        self.switch_cooldown = max(0, self.switch_cooldown - dt)
        self.tackle_cooldown = max(0, self.tackle_cooldown - dt)
        self.skill_cooldown = max(0, self.skill_cooldown - dt)
        self.action_cooldown = max(0, self.action_cooldown - dt)

        player = self.controlled_player
        self.has_ball = player.has_ball

        # Find nearest opponent
        if opponent_team:
            self.nearest_opponent, self.nearest_opponent_dist = find_nearest_player(
                player.position, opponent_team.players, max_distance=20.0
            )

        # Process movement input
        self._process_movement(dt, player)

        # Process action input based on context
        if self.has_ball:
            self._process_offense_input(dt, player, ball, opponent_team)
        else:
            self._process_defense_input(dt, player, ball, opponent_team)

        # Update charging
        if self.is_charging_pass or self.is_charging_shot:
            self.charge_timer += dt

    def _process_movement(self, dt: float, player):
        """Process WASD/Arrow movement."""
        raw_x = 0.0
        raw_z = 0.0

        if held_keys['w'] or held_keys['up arrow']:
            raw_z += 1.0
        if held_keys['s'] or held_keys['down arrow']:
            raw_z -= 1.0
        if held_keys['a'] or held_keys['left arrow']:
            raw_x -= 1.0
        if held_keys['d'] or held_keys['right arrow']:
            raw_x += 1.0

        # Normalize diagonal
        raw_input = Vec3(raw_x, 0, raw_z)
        length = vec3_length_xz(raw_input)
        if length > 1.0:
            raw_input = Vec3(raw_input.x / length, 0, raw_input.z / length)

        # Convert to world direction based on camera
        if length > 0.1:
            world_dir = self.camera.get_screen_direction(raw_input)
            self.move_input = world_dir
        else:
            self.move_input = Vec3(0, 0, 0)

        # Sprint
        self.is_sprinting = held_keys['left shift'] or held_keys['right shift']

        # Apply movement
        player.move(self.move_input, self.is_sprinting)

    def _process_offense_input(self, dt: float, player, ball, opponent_team):
        """Process input when player has the ball."""
        if not player.can_act():
            return

        opponents = opponent_team.players if opponent_team else []

        # SHOOT (Q) - charge and release
        if held_keys['q']:
            if not self.is_charging_shot:
                self.is_charging_shot = True
                self.charge_timer = 0.0
                player.start_charge('shoot')
        elif self.is_charging_shot:
            # Release shot
            self.is_charging_shot = False
            power = min(1.0, self.charge_timer / 1.2)

            # Aim at goal
            atk_dir = self.team.attacking_direction
            goal_pos = Vec3(
                atk_dir * FIELD_HALF_LENGTH,
                clamp(power * 2.5, 0.3, GOAL_HEIGHT - 0.3),
                clamp(self.move_input.z * 3, -GOAL_WIDTH / 2 + 0.5, GOAL_WIDTH / 2 - 0.5)
            )

            # Finesse shot if not sprinting
            is_finesse = not self.is_sprinting and power < 0.6
            player.initiate_shot(goal_pos, ball, power, is_finesse=is_finesse)
            player.release_charge()
            self.action_cooldown = 0.3

        # PASS (Space) - charge and release
        if held_keys['space']:
            if not self.is_charging_pass:
                self.is_charging_pass = True
                self.charge_timer = 0.0
                player.start_charge('pass')
        elif self.is_charging_pass:
            # Release pass
            self.is_charging_pass = False
            power = min(1.0, self.charge_timer / 1.0)

            # Find best pass target
            from utils import get_best_pass_target
            target = get_best_pass_target(player, self.team.players, opponents, ball.position)

            if target:
                from utils import calculate_pass_target
                target_pos = calculate_pass_target(
                    player.position, target.position, target.velocity, 15.0
                )
                player.initiate_pass(target_pos, ball, power)
            else:
                # Pass in facing direction
                forward = Vec3(
                    player.facing_direction.x * 15 * power,
                    0,
                    player.facing_direction.z * 15 * power
                )
                target_pos = Vec3(
                    player.position.x + forward.x,
                    0,
                    player.position.z + forward.z
                )
                player.initiate_pass(target_pos, ball, power)

            player.release_charge()
            self.action_cooldown = 0.3

        # THROUGH BALL (E)
        if held_keys['e'] and self.action_cooldown <= 0:
            from utils import get_best_pass_target
            target = get_best_pass_target(player, self.team.players, opponents, ball.position)
            if target:
                atk_dir = self.team.attacking_direction
                lead = Vec3(
                    target.velocity.x * 1.5 + atk_dir * 8,
                    0,
                    target.velocity.z * 1.5
                )
                target_pos = Vec3(
                    target.position.x + lead.x,
                    0,
                    target.position.z + lead.z
                )
                player.initiate_pass(target_pos, ball, 0.7, is_through=True)
                self.action_cooldown = 0.5

        # CROSS (C)
        if held_keys['c'] and self.action_cooldown <= 0:
            atk_dir = self.team.attacking_direction
            target_pos = Vec3(
                atk_dir * (FIELD_HALF_LENGTH - 10),
                0,
                self.move_input.z * 5 if vec3_length_xz(self.move_input) > 0.1 else 0
            )
            player.initiate_cross(target_pos, ball, 0.6)
            self.action_cooldown = 0.5

        # LOB PASS (R)
        if held_keys['r'] and self.action_cooldown <= 0:
            from utils import get_best_pass_target
            target = get_best_pass_target(player, self.team.players, opponents, ball.position)
            if target:
                player.initiate_pass(target.position, ball, 0.6, is_lob=True)
                self.action_cooldown = 0.5

        # SKILL MOVE (F)
        if held_keys['f'] and self.skill_cooldown <= 0:
            direction = self.move_input if vec3_length_xz(self.move_input) > 0.1 else player.facing_direction
            player.initiate_skill_move(direction)
            self.skill_cooldown = 1.0

    def _process_defense_input(self, dt: float, player, ball, opponent_team):
        """Process input when player doesn't have the ball."""
        if not player.can_act():
            return

        # SWITCH PLAYER (Space)
        if held_keys['space'] and self.switch_cooldown <= 0:
            self.team.select_nearest_to_ball(ball)
            self.switch_cooldown = 0.3

        # SLIDE TACKLE (Q)
        if held_keys['q'] and self.tackle_cooldown <= 0:
            target_pos = ball.position
            if self.nearest_opponent and self.nearest_opponent_dist < 5:
                target_pos = self.nearest_opponent.position
            player.initiate_tackle(target_pos, is_slide=True)
            self.tackle_cooldown = 1.5

        # STANDING TACKLE / PRESS (E)
        if held_keys['e'] and self.tackle_cooldown <= 0:
            if self.nearest_opponent and self.nearest_opponent_dist < 3:
                player.initiate_tackle(self.nearest_opponent.position, is_slide=False)
                self.tackle_cooldown = 0.5
            else:
                # Press towards ball
                direction = vec3_normalize_xz(Vec3(
                    ball.position.x - player.position.x, 0,
                    ball.position.z - player.position.z
                ))
                player.move(direction, True)

        # CONTAIN / JOCKEY (F)
        if held_keys['f']:
            if self.nearest_opponent and self.nearest_opponent_dist < 8:
                # Face opponent and back off slowly
                to_opp = vec3_normalize_xz(Vec3(
                    self.nearest_opponent.position.x - player.position.x, 0,
                    self.nearest_opponent.position.z - player.position.z
                ))
                player.facing_angle = vec3_angle_xz(to_opp)
                # Slowly approach
                if self.nearest_opponent_dist > 2:
                    player.move(Vec3(to_opp.x * 0.5, 0, to_opp.z * 0.5), False)

        # TEAM PRESS (Tab)
        if held_keys['tab']:
            # Tell nearby AI teammates to press
            from utils import find_players_in_radius
            nearby = find_players_in_radius(ball.position, self.team.players, 20, exclude=player)
            for teammate in nearby[:3]:
                brain = self.team.ai_brains.get(teammate.id)
                if brain:
                    from config import AIState
                    brain.force_state(AIState.PRESS_OPPONENT, ball.position)

    def on_key_press(self, key: str, ball, match):
        """Handle single key press events."""
        # Camera modes
        if key == '1':
            from config import CameraMode
            self.camera.set_mode(CameraMode.BROADCAST)
        elif key == '2':
            from config import CameraMode
            self.camera.set_mode(CameraMode.DYNAMIC)
        elif key == '3':
            from config import CameraMode
            self.camera.set_mode(CameraMode.END_TO_END)
        elif key == '4':
            from config import CameraMode
            self.camera.set_mode(CameraMode.TACTICAL)

        # Minimap toggle
        elif key == 'm':
            pass  # Handled by HUD

        # Replay
        elif key == 'v':
            self.camera.start_replay()

        # Pause
        elif key == 'escape':
            if match:
                match.toggle_pause()

    def handle_set_piece_input(self, ball, match):
        """Handle input during set pieces."""
        if not self.controlled_player:
            return False

        player = self.controlled_player

        # During set piece, space takes it
        if held_keys['space'] or held_keys['q']:
            sp_type = match.referee.current_set_piece

            if sp_type == SetPieceType.PENALTY:
                # Aim with movement, shoot with Q
                if held_keys['q']:
                    power = 0.85
                    atk_dir = self.team.attacking_direction
                    z_aim = self.move_input.z * 3 if vec3_length_xz(self.move_input) > 0.1 else 0
                    goal_pos = Vec3(
                        atk_dir * FIELD_HALF_LENGTH,
                        clamp(1.0 + self.move_input.z * 0.5, 0.3, 2.0),
                        z_aim
                    )
                    player.initiate_shot(goal_pos, ball, power)
                    return True

            elif sp_type in [SetPieceType.FREE_KICK, SetPieceType.CORNER_KICK]:
                if held_keys['q']:
                    # Shoot
                    atk_dir = self.team.attacking_direction
                    goal_pos = Vec3(
                        atk_dir * FIELD_HALF_LENGTH,
                        1.5,
                        self.move_input.z * 3 if vec3_length_xz(self.move_input) > 0.1 else 0
                    )
                    player.initiate_shot(goal_pos, ball, 0.8)
                    return True
                elif held_keys['space']:
                    # Pass/Cross
                    from utils import get_best_pass_target
                    opponents = match.away_team.players if self.team == match.home_team else match.home_team.players
                    target = get_best_pass_target(player, self.team.players, opponents, ball.position)
                    if target:
                        if sp_type == SetPieceType.CORNER_KICK:
                            player.initiate_cross(target.position, ball, 0.7)
                        else:
                            player.initiate_pass(target.position, ball, 0.6)
                    return True

            elif sp_type in [SetPieceType.THROW_IN, SetPieceType.GOAL_KICK]:
                if held_keys['space']:
                    from utils import get_best_pass_target
                    opponents = match.away_team.players if self.team == match.home_team else match.home_team.players
                    target = get_best_pass_target(player, self.team.players, opponents, ball.position)
                    if target:
                        player.initiate_pass(target.position, ball, 0.5)
                    return True

        return False
