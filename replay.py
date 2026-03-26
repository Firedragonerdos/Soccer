"""
Ultimate Soccer 3D - Replay System
Records and replays key match moments with multi-angle cameras.
"""
import math
from ursina import Vec3
from config import CAMERA_REPLAY_SPEED
from utils import vec3_lerp, clamp


class ReplayFrame:
    """Single frame of replay data."""
    __slots__ = ['ball_pos', 'ball_vel', 'player_positions', 'player_states',
                 'player_facings', 'timestamp']

    def __init__(self, timestamp, ball_pos, ball_vel, player_positions,
                 player_states, player_facings):
        self.timestamp = timestamp
        self.ball_pos = Vec3(ball_pos.x, ball_pos.y, ball_pos.z)
        self.ball_vel = Vec3(ball_vel.x, ball_vel.y, ball_vel.z)
        self.player_positions = {pid: Vec3(p.x, p.y, p.z) for pid, p in player_positions.items()}
        self.player_states = dict(player_states)
        self.player_facings = dict(player_facings)


class ReplayBuffer:
    """Circular buffer for recording replay frames."""

    def __init__(self, max_frames=600):
        self.max_frames = max_frames
        self.frames = []
        self.recording = True
        self.record_interval = 1.0 / 60.0  # 60fps recording
        self.record_timer = 0.0

    def record(self, dt, timestamp, ball, all_players):
        """Record a frame if interval has passed."""
        if not self.recording:
            return

        self.record_timer += dt
        if self.record_timer < self.record_interval:
            return
        self.record_timer = 0.0

        positions = {}
        states = {}
        facings = {}
        for p in all_players:
            positions[p.id] = Vec3(p.position.x, p.position.y, p.position.z)
            states[p.id] = p.state
            facings[p.id] = p.facing_angle

        frame = ReplayFrame(
            timestamp, ball.position, ball.velocity,
            positions, states, facings
        )
        self.frames.append(frame)

        if len(self.frames) > self.max_frames:
            self.frames.pop(0)

    def get_last_n_seconds(self, seconds: float) -> list:
        """Get frames from the last N seconds."""
        if not self.frames:
            return []
        target_time = self.frames[-1].timestamp - seconds
        result = [f for f in self.frames if f.timestamp >= target_time]
        return result

    def clear(self):
        self.frames.clear()


class ReplayPlayer:
    """Plays back recorded replay frames."""

    def __init__(self):
        self.frames = []
        self.current_index = 0
        self.playing = False
        self.speed = CAMERA_REPLAY_SPEED
        self.paused = False
        self.timer = 0.0
        self.frame_interval = 1.0 / 60.0

        # Camera angles for replay
        self.camera_angles = [
            'broadcast', 'close_up', 'behind_goal', 'side_angle', 'top_down'
        ]
        self.current_angle = 0
        self.angle_switch_timer = 0.0
        self.angle_switch_interval = 2.0

    def start(self, frames: list, speed: float = 0.5):
        """Start replay playback."""
        self.frames = frames
        self.current_index = 0
        self.playing = True
        self.paused = False
        self.speed = speed
        self.timer = 0.0
        self.current_angle = 0

    def stop(self):
        self.playing = False
        self.frames = []
        self.current_index = 0

    def update(self, dt: float) -> ReplayFrame:
        """Advance replay and return current frame."""
        if not self.playing or self.paused or not self.frames:
            return None

        self.timer += dt * self.speed
        self.angle_switch_timer += dt

        if self.angle_switch_timer > self.angle_switch_interval:
            self.angle_switch_timer = 0.0
            self.current_angle = (self.current_angle + 1) % len(self.camera_angles)

        if self.timer >= self.frame_interval:
            self.timer = 0.0
            self.current_index += 1

            if self.current_index >= len(self.frames):
                self.stop()
                return None

        if self.current_index < len(self.frames):
            return self.frames[self.current_index]
        return None

    def get_camera_position(self, ball_pos: Vec3) -> tuple:
        """Get camera position and look-at for current replay angle."""
        angle_name = self.camera_angles[self.current_angle]

        if angle_name == 'broadcast':
            pos = Vec3(ball_pos.x, 20, ball_pos.z - 35)
            look = ball_pos
        elif angle_name == 'close_up':
            pos = Vec3(ball_pos.x + 5, 3, ball_pos.z - 8)
            look = Vec3(ball_pos.x, 1.5, ball_pos.z)
        elif angle_name == 'behind_goal':
            side = 1 if ball_pos.x > 0 else -1
            pos = Vec3(side * 60, 8, 0)
            look = ball_pos
        elif angle_name == 'side_angle':
            pos = Vec3(ball_pos.x, 5, ball_pos.z - 15)
            look = Vec3(ball_pos.x, 1, ball_pos.z)
        elif angle_name == 'top_down':
            pos = Vec3(ball_pos.x, 40, ball_pos.z - 5)
            look = ball_pos
        else:
            pos = Vec3(0, 25, -35)
            look = ball_pos

        return pos, look

    def toggle_pause(self):
        self.paused = not self.paused

    def set_speed(self, speed: float):
        self.speed = clamp(speed, 0.1, 2.0)

    @property
    def progress(self) -> float:
        if not self.frames:
            return 0.0
        return self.current_index / max(len(self.frames) - 1, 1)

    @property
    def is_active(self) -> bool:
        return self.playing
