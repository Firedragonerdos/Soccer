"""
Ultimate Soccer 3D - Camera System
Multiple camera modes: broadcast, dynamic, tactical, player follow, replay.
"""
import math
from ursina import Vec3, camera, time as ursina_time
from config import (
    CameraMode,
    CAMERA_BROADCAST_HEIGHT, CAMERA_BROADCAST_DISTANCE, CAMERA_BROADCAST_ANGLE,
    CAMERA_FOLLOW_SPEED, CAMERA_FOLLOW_OFFSET_Y, CAMERA_FOLLOW_OFFSET_Z,
    CAMERA_DYNAMIC_ZOOM_MIN, CAMERA_DYNAMIC_ZOOM_MAX,
    CAMERA_SHAKE_INTENSITY, CAMERA_SHAKE_DURATION,
    CAMERA_REPLAY_SPEED, CAMERA_TRANSITION_SPEED, CAMERA_TACTICAL_HEIGHT,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH,
)
from utils import (
    vec3_lerp, vec3_length_xz, vec3_normalize_xz, vec3_distance_xz,
    clamp, lerp, smooth_step, ease_in_out,
)
import random


class CameraSystem:
    """Manages the game camera with multiple modes."""

    def __init__(self):
        self.mode = CameraMode.BROADCAST
        self.previous_mode = CameraMode.BROADCAST

        # Current camera state
        self.position = Vec3(0, CAMERA_BROADCAST_HEIGHT, -CAMERA_BROADCAST_DISTANCE)
        self.target_position = Vec3(0, CAMERA_BROADCAST_HEIGHT, -CAMERA_BROADCAST_DISTANCE)
        self.look_at_target = Vec3(0, 0, 0)
        self.target_look_at = Vec3(0, 0, 0)

        # Smooth follow
        self.velocity = Vec3(0, 0, 0)
        self.smooth_time = 0.5

        # Camera shake
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = Vec3(0, 0, 0)

        # Transition
        self.transitioning = False
        self.transition_timer = 0.0
        self.transition_duration = 0.5
        self.transition_start_pos = Vec3(0, 0, 0)
        self.transition_start_look = Vec3(0, 0, 0)

        # Replay
        self.replay_positions = []
        self.replay_index = 0
        self.replay_speed = CAMERA_REPLAY_SPEED

        # Dynamic zoom
        self.current_zoom = CAMERA_BROADCAST_HEIGHT
        self.target_zoom = CAMERA_BROADCAST_HEIGHT

        # Broadcast mode settings
        self.broadcast_side_offset = 0.0
        self.broadcast_height = CAMERA_BROADCAST_HEIGHT
        self.broadcast_distance = CAMERA_BROADCAST_DISTANCE

        # Player follow
        self.follow_target = None

        # Cinematic
        self.cinematic_timer = 0.0
        self.cinematic_path = []

    def set_mode(self, mode: CameraMode, transition: bool = True):
        """Switch camera mode."""
        if mode == self.mode:
            return

        self.previous_mode = self.mode
        self.mode = mode

        if transition:
            self.transitioning = True
            self.transition_timer = 0.0
            self.transition_start_pos = Vec3(self.position.x, self.position.y, self.position.z)
            self.transition_start_look = Vec3(self.look_at_target.x, self.look_at_target.y,
                                                self.look_at_target.z)

    def update(self, dt: float, ball_pos: Vec3, ball_vel: Vec3 = None):
        """Update camera position and rotation."""
        # Calculate target based on mode
        if self.mode == CameraMode.BROADCAST:
            self._update_broadcast(dt, ball_pos, ball_vel)
        elif self.mode == CameraMode.DYNAMIC:
            self._update_dynamic(dt, ball_pos, ball_vel)
        elif self.mode == CameraMode.END_TO_END:
            self._update_end_to_end(dt, ball_pos)
        elif self.mode == CameraMode.PLAYER_FOLLOW:
            self._update_player_follow(dt, ball_pos)
        elif self.mode == CameraMode.TACTICAL:
            self._update_tactical(dt, ball_pos)
        elif self.mode == CameraMode.REPLAY:
            self._update_replay(dt)

        # Handle transition
        if self.transitioning:
            self.transition_timer += dt
            t = clamp(self.transition_timer / self.transition_duration, 0, 1)
            t = ease_in_out(t)

            self.position = vec3_lerp(self.transition_start_pos, self.target_position, t)
            self.look_at_target = vec3_lerp(self.transition_start_look, self.target_look_at, t)

            if t >= 1.0:
                self.transitioning = False
        else:
            # Smooth follow
            self.position = vec3_lerp(self.position, self.target_position,
                                       min(1.0, CAMERA_FOLLOW_SPEED * dt))
            self.look_at_target = vec3_lerp(self.look_at_target, self.target_look_at,
                                             min(1.0, CAMERA_FOLLOW_SPEED * 1.5 * dt))

        # Apply camera shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            shake_factor = self.shake_timer / CAMERA_SHAKE_DURATION
            self.shake_offset = Vec3(
                random.uniform(-1, 1) * self.shake_intensity * shake_factor,
                random.uniform(-1, 1) * self.shake_intensity * shake_factor * 0.5,
                random.uniform(-1, 1) * self.shake_intensity * shake_factor,
            )
        else:
            self.shake_offset = Vec3(0, 0, 0)

        # Apply to Ursina camera
        final_pos = Vec3(
            self.position.x + self.shake_offset.x,
            self.position.y + self.shake_offset.y,
            self.position.z + self.shake_offset.z,
        )
        camera.position = final_pos
        camera.look_at(self.look_at_target)

    def _update_broadcast(self, dt: float, ball_pos: Vec3, ball_vel: Vec3 = None):
        """Classic TV broadcast camera - side view following play."""
        # Follow ball along X axis
        target_x = clamp(ball_pos.x, -FIELD_HALF_LENGTH + 10, FIELD_HALF_LENGTH - 10)

        # Slight Z offset based on ball Z position
        z_offset = -self.broadcast_distance
        z_factor = ball_pos.z / FIELD_HALF_WIDTH * 5.0
        z_offset += z_factor

        # Height adjusts slightly based on action
        height = self.broadcast_height
        if ball_vel and vec3_length_xz(ball_vel) > 15:
            height -= 2  # Zoom in during fast play

        self.target_position = Vec3(target_x, height, z_offset)
        self.target_look_at = Vec3(
            ball_pos.x,
            max(0.5, ball_pos.y * 0.5),
            clamp(ball_pos.z * 0.3, -5, 5)
        )

    def _update_dynamic(self, dt: float, ball_pos: Vec3, ball_vel: Vec3 = None):
        """Dynamic camera that zooms based on action."""
        # Calculate zoom based on ball speed and distance from goals
        ball_speed = vec3_length_xz(ball_vel) if ball_vel else 0
        dist_to_goal = min(
            abs(ball_pos.x - FIELD_HALF_LENGTH),
            abs(ball_pos.x + FIELD_HALF_LENGTH)
        )

        # Zoom in near goals
        zoom_factor = clamp(dist_to_goal / FIELD_HALF_LENGTH, 0.3, 1.0)
        self.target_zoom = lerp(CAMERA_DYNAMIC_ZOOM_MIN, CAMERA_DYNAMIC_ZOOM_MAX, zoom_factor)
        self.current_zoom = lerp(self.current_zoom, self.target_zoom, dt * 2)

        # Position
        target_x = clamp(ball_pos.x * 0.8, -FIELD_HALF_LENGTH + 10, FIELD_HALF_LENGTH - 10)
        self.target_position = Vec3(target_x, self.current_zoom, -self.current_zoom * 0.8)
        self.target_look_at = Vec3(ball_pos.x, max(0.5, ball_pos.y * 0.5), ball_pos.z * 0.5)

    def _update_end_to_end(self, dt: float, ball_pos: Vec3):
        """End-to-end camera behind the attacking goal."""
        # Position behind the goal the ball is heading towards
        if ball_pos.x > 0:
            cam_x = FIELD_HALF_LENGTH + 15
        else:
            cam_x = -(FIELD_HALF_LENGTH + 15)

        self.target_position = Vec3(cam_x, 12, 0)
        self.target_look_at = Vec3(ball_pos.x, max(0.5, ball_pos.y * 0.5), ball_pos.z)

    def _update_player_follow(self, dt: float, ball_pos: Vec3):
        """Follow a specific player."""
        if self.follow_target:
            target_pos = self.follow_target.position
        else:
            target_pos = ball_pos

        offset_y = CAMERA_FOLLOW_OFFSET_Y * 0.6
        offset_z = CAMERA_FOLLOW_OFFSET_Z * 0.6

        self.target_position = Vec3(
            target_pos.x,
            offset_y,
            target_pos.z + offset_z
        )
        self.target_look_at = Vec3(target_pos.x, 1.0, target_pos.z)

    def _update_tactical(self, dt: float, ball_pos: Vec3):
        """Top-down tactical view."""
        self.target_position = Vec3(0, CAMERA_TACTICAL_HEIGHT, -5)
        self.target_look_at = Vec3(0, 0, 0)

    def _update_replay(self, dt: float):
        """Replay camera following recorded positions."""
        if not self.replay_positions:
            return

        if self.replay_index < len(self.replay_positions):
            target = self.replay_positions[self.replay_index]
            self.target_position = target['cam_pos']
            self.target_look_at = target['look_at']
            self.replay_index += 1
        else:
            self.set_mode(self.previous_mode)

    def trigger_shake(self, intensity: float = CAMERA_SHAKE_INTENSITY,
                       duration: float = CAMERA_SHAKE_DURATION):
        """Trigger camera shake effect."""
        self.shake_intensity = intensity
        self.shake_timer = duration

    def trigger_goal_camera(self, ball_pos: Vec3, scorer_pos: Vec3):
        """Trigger special camera for goal celebration."""
        self.shake_intensity = 0.3
        self.shake_timer = 0.5

        # Zoom to scorer
        self.follow_target = type('obj', (object,), {'position': scorer_pos})()
        self.set_mode(CameraMode.PLAYER_FOLLOW, transition=True)
        self.transition_duration = 1.0

    def record_replay_frame(self, ball_pos: Vec3):
        """Record current frame for replay."""
        self.replay_positions.append({
            'cam_pos': Vec3(self.position.x, self.position.y, self.position.z),
            'look_at': Vec3(self.look_at_target.x, self.look_at_target.y, self.look_at_target.z),
            'ball_pos': Vec3(ball_pos.x, ball_pos.y, ball_pos.z),
        })
        # Keep last 300 frames (~5 seconds)
        if len(self.replay_positions) > 300:
            self.replay_positions.pop(0)

    def start_replay(self):
        """Start replay of recent action."""
        if self.replay_positions:
            self.replay_index = 0
            self.set_mode(CameraMode.REPLAY, transition=True)

    def set_follow_target(self, player):
        """Set player to follow."""
        self.follow_target = player

    def cycle_mode(self):
        """Cycle through camera modes."""
        modes = [CameraMode.BROADCAST, CameraMode.DYNAMIC,
                 CameraMode.END_TO_END, CameraMode.TACTICAL]
        current_idx = modes.index(self.mode) if self.mode in modes else 0
        next_idx = (current_idx + 1) % len(modes)
        self.set_mode(modes[next_idx])

    def setup_kickoff_camera(self):
        """Set camera for kickoff."""
        self.target_position = Vec3(0, 30, -40)
        self.target_look_at = Vec3(0, 0, 0)
        self.position = Vec3(0, 50, -50)

    def setup_celebration_camera(self, scorer_pos: Vec3):
        """Set camera for goal celebration."""
        offset_x = 5 if scorer_pos.x > 0 else -5
        self.target_position = Vec3(
            scorer_pos.x + offset_x,
            3,
            scorer_pos.z - 8
        )
        self.target_look_at = Vec3(scorer_pos.x, 1.5, scorer_pos.z)

    def get_screen_direction(self, input_dir: Vec3) -> Vec3:
        """Convert screen-relative input to world direction based on camera."""
        # Get camera forward and right vectors projected on XZ plane
        cam_forward = Vec3(
            self.look_at_target.x - self.position.x,
            0,
            self.look_at_target.z - self.position.z
        )
        cam_forward = vec3_normalize_xz(cam_forward)
        cam_right = Vec3(cam_forward.z, 0, -cam_forward.x)

        world_dir = Vec3(
            cam_forward.x * input_dir.z + cam_right.x * input_dir.x,
            0,
            cam_forward.z * input_dir.z + cam_right.z * input_dir.x
        )

        length = vec3_length_xz(world_dir)
        if length > 0.01:
            world_dir = Vec3(world_dir.x / length, 0, world_dir.z / length)

        return world_dir
