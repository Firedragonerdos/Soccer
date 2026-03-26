"""
Ultimate Soccer 3D - Ball Entity
Full ball physics with spin, bounce, friction, and trajectory.
"""
import math
import random
from ursina import Entity, Vec3, color, time as ursina_time
from config import (
    BALL_RADIUS, BALL_MASS, BALL_BOUNCE_COEFFICIENT, BALL_FRICTION_GROUND,
    BALL_FRICTION_AIR, BALL_GRAVITY, BALL_MAX_SPEED, BALL_SPIN_DECAY,
    BALL_SPIN_EFFECT, BALL_ROLL_FRICTION, BALL_BOUNCE_MIN_VELOCITY,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH, GOAL_HEIGHT,
    GOAL_DEPTH, WeatherType, rgba,
)
from utils import vec3_length, vec3_normalize, vec3_clamp_length, vec3_reflect, clamp


class Ball:
    """Football with full physics simulation."""

    def __init__(self):
        self.entity = Entity(
            model='sphere',
            color=color.white,
            scale=BALL_RADIUS * 2,
            position=(0, BALL_RADIUS, 0),
        )
        # Add black pentagons pattern indicator
        self.shadow = Entity(
            model='quad',
            color=rgba(0, 0, 0, 80),
            scale=(BALL_RADIUS * 4, BALL_RADIUS * 4),
            position=(0, 0.005, 0),
            rotation=(90, 0, 0),
            double_sided=True,
        )

        # Physics state
        self.position = Vec3(0, BALL_RADIUS, 0)
        self.velocity = Vec3(0, 0, 0)
        self.spin = Vec3(0, 0, 0)  # Angular velocity (spin)
        self.angular_velocity = Vec3(0, 0, 0)

        # State flags
        self.is_on_ground = True
        self.is_in_play = True
        self.is_held = False  # GK holding
        self.last_touched_by = None
        self.last_touched_team = None
        self.owner = None  # Player currently controlling
        self.out_of_bounds = False
        self.in_goal = 0  # 0=no, 1=right goal, -1=left goal

        # Trail for visual effect
        self.trail_positions = []
        self.trail_max = 10
        self.trail_timer = 0

        # Weather effects
        self.weather = WeatherType.CLEAR
        self.weather_friction_mod = 1.0
        self.weather_speed_mod = 1.0

        # Shot/pass tracking
        self.shot_active = False
        self.pass_active = False
        self.cross_active = False
        self.set_piece_ball = False
        self.frames_since_touch = 0

    @property
    def pos(self) -> Vec3:
        return self.position

    @property
    def vel(self) -> Vec3:
        return self.velocity

    @property
    def speed(self) -> float:
        return vec3_length(self.velocity)

    @property
    def ground_speed(self) -> float:
        return math.sqrt(self.velocity.x ** 2 + self.velocity.z ** 2)

    def set_weather(self, weather: WeatherType):
        self.weather = weather
        if weather in [WeatherType.RAIN, WeatherType.HEAVY_RAIN]:
            self.weather_friction_mod = 0.97
            self.weather_speed_mod = 0.95
        elif weather == WeatherType.SNOW:
            self.weather_friction_mod = 0.96
            self.weather_speed_mod = 0.90
        else:
            self.weather_friction_mod = 1.0
            self.weather_speed_mod = 1.0

    def reset(self, position: Vec3 = None):
        """Reset ball to position."""
        if position is None:
            position = Vec3(0, BALL_RADIUS, 0)
        self.position = Vec3(position.x, max(BALL_RADIUS, position.y), position.z)
        self.velocity = Vec3(0, 0, 0)
        self.spin = Vec3(0, 0, 0)
        self.angular_velocity = Vec3(0, 0, 0)
        self.is_on_ground = True
        self.is_in_play = True
        self.is_held = False
        self.owner = None
        self.out_of_bounds = False
        self.in_goal = 0
        self.shot_active = False
        self.pass_active = False
        self.cross_active = False
        self.set_piece_ball = False
        self.frames_since_touch = 0
        self.trail_positions.clear()
        self._update_entity()

    def kick(self, direction: Vec3, power: float, spin: Vec3 = None,
             kicker=None, is_shot=False, is_pass=False, is_cross=False):
        """Apply a kick to the ball."""
        self.velocity = Vec3(
            direction.x * power * self.weather_speed_mod,
            direction.y * power * self.weather_speed_mod,
            direction.z * power * self.weather_speed_mod
        )
        self.velocity = vec3_clamp_length(self.velocity, BALL_MAX_SPEED)

        if spin:
            self.spin = Vec3(spin.x, spin.y, spin.z)
        else:
            self.spin = Vec3(0, 0, 0)

        if self.velocity.y > 0.5:
            self.is_on_ground = False

        self.is_held = False
        self.owner = None
        self.last_touched_by = kicker
        if kicker:
            self.last_touched_team = getattr(kicker, 'team_id', None)

        self.shot_active = is_shot
        self.pass_active = is_pass
        self.cross_active = is_cross
        self.frames_since_touch = 0

    def header(self, direction: Vec3, power: float, header_player=None):
        """Apply a header to the ball."""
        self.velocity = Vec3(
            direction.x * power,
            direction.y * power * 0.5,
            direction.z * power
        )
        self.spin = Vec3(
            random.uniform(-1, 1),
            0,
            random.uniform(-1, 1)
        )
        self.is_on_ground = False
        self.last_touched_by = header_player
        if header_player:
            self.last_touched_team = getattr(header_player, 'team_id', None)
        self.frames_since_touch = 0

    def deflect(self, normal: Vec3, speed_retain: float = 0.6):
        """Deflect ball off a surface/player."""
        reflected = vec3_reflect(self.velocity, vec3_normalize(normal))
        self.velocity = Vec3(
            reflected.x * speed_retain,
            reflected.y * speed_retain,
            reflected.z * speed_retain
        )
        self.spin = Vec3(
            self.spin.x * 0.5 + random.uniform(-1, 1),
            self.spin.y * 0.5,
            self.spin.z * 0.5 + random.uniform(-1, 1)
        )

    def hold(self, holder):
        """GK catches the ball."""
        self.is_held = True
        self.owner = holder
        self.velocity = Vec3(0, 0, 0)
        self.spin = Vec3(0, 0, 0)
        self.shot_active = False
        self.pass_active = False
        self.cross_active = False
        self.last_touched_by = holder
        if holder:
            self.last_touched_team = getattr(holder, 'team_id', None)

    def update(self, dt: float):
        """Update ball physics."""
        if self.is_held:
            if self.owner:
                hold_offset = Vec3(0.5, 0.8, 0)
                self.position = Vec3(
                    self.owner.position.x + hold_offset.x,
                    self.owner.position.y + hold_offset.y,
                    self.owner.position.z + hold_offset.z
                )
            self._update_entity()
            return

        self.frames_since_touch += 1
        if self.frames_since_touch > 30:
            self.shot_active = False
            self.pass_active = False
            self.cross_active = False

        # Apply gravity
        if not self.is_on_ground:
            self.velocity = Vec3(
                self.velocity.x,
                self.velocity.y + BALL_GRAVITY * dt,
                self.velocity.z
            )

        # Apply spin effect (Magnus effect)
        if vec3_length(self.spin) > 0.1:
            spin_force = Vec3(
                self.spin.z * BALL_SPIN_EFFECT * dt,
                0,
                -self.spin.x * BALL_SPIN_EFFECT * dt
            )
            self.velocity = Vec3(
                self.velocity.x + spin_force.x,
                self.velocity.y + spin_force.y,
                self.velocity.z + spin_force.z
            )
            # Decay spin
            self.spin = Vec3(
                self.spin.x * BALL_SPIN_DECAY,
                self.spin.y * BALL_SPIN_DECAY,
                self.spin.z * BALL_SPIN_DECAY
            )

        # Apply friction
        if self.is_on_ground:
            friction = BALL_ROLL_FRICTION * self.weather_friction_mod
            self.velocity = Vec3(
                self.velocity.x * friction,
                self.velocity.y,
                self.velocity.z * friction
            )
        else:
            air_friction = BALL_FRICTION_AIR
            self.velocity = Vec3(
                self.velocity.x * air_friction,
                self.velocity.y,
                self.velocity.z * air_friction
            )

        # Wind effect in weather
        if self.weather == WeatherType.HEAVY_RAIN:
            wind = Vec3(random.uniform(-0.3, 0.3) * dt, 0, random.uniform(-0.3, 0.3) * dt)
            self.velocity = Vec3(
                self.velocity.x + wind.x,
                self.velocity.y,
                self.velocity.z + wind.z
            )
        elif self.weather == WeatherType.SNOW:
            wind = Vec3(random.uniform(-0.2, 0.2) * dt, 0, random.uniform(-0.2, 0.2) * dt)
            self.velocity = Vec3(
                self.velocity.x + wind.x,
                self.velocity.y,
                self.velocity.z + wind.z
            )

        # Clamp velocity
        self.velocity = vec3_clamp_length(self.velocity, BALL_MAX_SPEED)

        # Stop very slow balls
        if self.is_on_ground and self.ground_speed < 0.05:
            self.velocity = Vec3(0, self.velocity.y, 0)

        # Update position
        self.position = Vec3(
            self.position.x + self.velocity.x * dt,
            self.position.y + self.velocity.y * dt,
            self.position.z + self.velocity.z * dt
        )

        # Ground collision
        if self.position.y <= BALL_RADIUS:
            self.position = Vec3(self.position.x, BALL_RADIUS, self.position.z)
            if self.velocity.y < -BALL_BOUNCE_MIN_VELOCITY:
                self.velocity = Vec3(
                    self.velocity.x * BALL_FRICTION_GROUND,
                    abs(self.velocity.y) * BALL_BOUNCE_COEFFICIENT,
                    self.velocity.z * BALL_FRICTION_GROUND
                )
                if abs(self.velocity.y) < BALL_BOUNCE_MIN_VELOCITY:
                    self.velocity = Vec3(self.velocity.x, 0, self.velocity.z)
                    self.is_on_ground = True
            else:
                self.velocity = Vec3(self.velocity.x, 0, self.velocity.z)
                self.is_on_ground = True
        else:
            self.is_on_ground = False

        # Goal post collision
        self._check_post_collision()

        # Check out of bounds
        self._check_bounds()

        # Update trail
        self.trail_timer += dt
        if self.trail_timer > 0.03 and self.speed > 5:
            self.trail_positions.append(Vec3(self.position.x, self.position.y, self.position.z))
            if len(self.trail_positions) > self.trail_max:
                self.trail_positions.pop(0)
            self.trail_timer = 0

        # Update visual
        self._update_entity()

        # Update angular velocity for visual rotation
        if self.ground_speed > 0.1:
            rotation_speed = self.ground_speed * 100
            self.entity.rotation_x += rotation_speed * dt
            self.entity.rotation_z += self.spin.x * 50 * dt

    def _check_post_collision(self):
        """Check collision with goal posts and crossbar."""
        for side in [-1, 1]:
            goal_x = side * FIELD_HALF_LENGTH
            post_positions = [
                Vec3(goal_x, 0, -GOAL_WIDTH / 2),
                Vec3(goal_x, 0, GOAL_WIDTH / 2),
            ]

            for post_pos in post_positions:
                dx = self.position.x - post_pos.x
                dz = self.position.z - post_pos.z
                dist_xz = math.sqrt(dx * dx + dz * dz)
                post_radius = 0.12

                if dist_xz < post_radius + BALL_RADIUS and self.position.y < GOAL_HEIGHT:
                    normal = vec3_normalize(Vec3(dx, 0, dz))
                    self.deflect(normal, 0.5)
                    overlap = (post_radius + BALL_RADIUS) - dist_xz
                    self.position = Vec3(
                        self.position.x + normal.x * overlap,
                        self.position.y,
                        self.position.z + normal.z * overlap
                    )

            # Crossbar
            if (abs(self.position.x - goal_x) < BALL_RADIUS + 0.12 and
                abs(self.position.z) < GOAL_WIDTH / 2 and
                abs(self.position.y - GOAL_HEIGHT) < BALL_RADIUS + 0.12):
                if self.velocity.y > 0:
                    self.velocity = Vec3(
                        self.velocity.x,
                        -abs(self.velocity.y) * BALL_BOUNCE_COEFFICIENT,
                        self.velocity.z
                    )

    def _check_bounds(self):
        """Check if ball is out of the field."""
        margin = 2.0
        if abs(self.position.x) > FIELD_HALF_LENGTH + margin:
            goal_side = 1 if self.position.x > 0 else -1
            if (abs(self.position.z) <= GOAL_WIDTH / 2 and
                self.position.y <= GOAL_HEIGHT):
                self.in_goal = goal_side
                self.is_in_play = False
            else:
                self.out_of_bounds = True
                self.is_in_play = False

        if abs(self.position.z) > FIELD_HALF_WIDTH + 1.5:
            self.out_of_bounds = True
            self.is_in_play = False

        # Stop ball if out of play
        if not self.is_in_play:
            self.velocity = Vec3(0, 0, 0)
            self.spin = Vec3(0, 0, 0)

    def _update_entity(self):
        """Sync Ursina entity with physics state."""
        self.entity.position = self.position
        # Shadow follows on ground
        self.shadow.position = Vec3(self.position.x, 0.005, self.position.z)
        shadow_scale = max(0.1, BALL_RADIUS * 4 * (1.0 - self.position.y / 20.0))
        self.shadow.scale = (shadow_scale, shadow_scale)

    def get_predicted_position(self, time_ahead: float) -> Vec3:
        """Predict where the ball will be in `time_ahead` seconds."""
        px, py, pz = self.position.x, self.position.y, self.position.z
        vx, vy, vz = self.velocity.x, self.velocity.y, self.velocity.z
        steps = int(time_ahead / 0.02)
        for _ in range(steps):
            if py > BALL_RADIUS + 0.01:
                vy += BALL_GRAVITY * 0.02
            else:
                vx *= BALL_ROLL_FRICTION
                vz *= BALL_ROLL_FRICTION
            px += vx * 0.02
            py += vy * 0.02
            pz += vz * 0.02
            if py < BALL_RADIUS:
                py = BALL_RADIUS
                vy = abs(vy) * BALL_BOUNCE_COEFFICIENT
                if abs(vy) < BALL_BOUNCE_MIN_VELOCITY:
                    vy = 0
        return Vec3(px, max(BALL_RADIUS, py), pz)

    def time_to_reach(self, target: Vec3) -> float:
        """Estimate time for ball to reach target position."""
        dist = math.sqrt((target.x - self.position.x) ** 2 + (target.z - self.position.z) ** 2)
        speed = max(self.ground_speed, 0.1)
        return dist / speed

    def is_heading_towards(self, target: Vec3, angle_threshold: float = 0.8) -> bool:
        """Check if ball is moving towards a target."""
        if self.ground_speed < 0.5:
            return False
        to_target = Vec3(target.x - self.position.x, 0, target.z - self.position.z)
        to_target_norm = vec3_normalize(to_target)
        vel_norm = vec3_normalize(Vec3(self.velocity.x, 0, self.velocity.z))
        dot = to_target_norm.x * vel_norm.x + to_target_norm.z * vel_norm.z
        return dot > angle_threshold

    def distance_to(self, pos: Vec3) -> float:
        dx = self.position.x - pos.x
        dz = self.position.z - pos.z
        return math.sqrt(dx * dx + dz * dz)

    def cleanup(self):
        try:
            self.entity.disable()
            self.shadow.disable()
        except Exception:
            pass
