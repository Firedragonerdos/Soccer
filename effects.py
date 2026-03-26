"""
Ultimate Soccer 3D - Visual Effects
Particle systems, weather effects, goal celebrations, and visual FX.
"""
import math
import random
from ursina import Entity, Vec3, color, camera, time as ursina_time, destroy
from config import (
    WeatherType, FIELD_HALF_LENGTH, FIELD_HALF_WIDTH,
    PARTICLE_GRASS_COUNT, PARTICLE_GOAL_CELEBRATION_COUNT,
    PARTICLE_RAIN_COUNT, PARTICLE_SNOW_COUNT, rgb, rgba,
)
from utils import clamp, lerp


class Particle:
    """Single particle entity."""
    def __init__(self, position, velocity, lifetime, size, particle_color,
                 gravity=-5.0, fade=True, model='quad'):
        self.entity = Entity(
            model=model,
            color=particle_color,
            scale=size,
            position=position,
            billboard=True if model == 'quad' else False,
        )
        self.velocity = Vec3(velocity.x, velocity.y, velocity.z)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.fade = fade
        self.alive = True
        self.size = size

    def update(self, dt):
        if not self.alive:
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            self.entity.disable()
            return

        # Apply gravity
        self.velocity = Vec3(
            self.velocity.x,
            self.velocity.y + self.gravity * dt,
            self.velocity.z
        )

        # Update position
        pos = self.entity.position
        self.entity.position = Vec3(
            pos.x + self.velocity.x * dt,
            max(0.01, pos.y + self.velocity.y * dt),
            pos.z + self.velocity.z * dt,
        )

        # Fade out
        if self.fade:
            alpha = clamp(self.lifetime / self.max_lifetime, 0, 1)
            c = self.entity.color
            self.entity.color = rgba(
                int(c.r * 255) if hasattr(c, 'r') else 255,
                int(c.g * 255) if hasattr(c, 'g') else 255,
                int(c.b * 255) if hasattr(c, 'b') else 255,
                int(alpha * 255)
            )

        # Shrink
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        scale = self.size * (1.0 - progress * 0.5)
        self.entity.scale = scale

    def destroy(self):
        try:
            self.entity.disable()
        except Exception:
            pass


class ParticleSystem:
    """Manages particle effects."""

    def __init__(self):
        self.particles = []
        self.weather_particles = []
        self.current_weather = WeatherType.CLEAR

    def update(self, dt):
        """Update all active particles."""
        # Update gameplay particles
        alive = []
        for p in self.particles:
            p.update(dt)
            if p.alive:
                alive.append(p)
            else:
                p.destroy()
        self.particles = alive

        # Update weather particles
        alive_weather = []
        for p in self.weather_particles:
            p.update(dt)
            if p.alive:
                alive_weather.append(p)
            else:
                p.destroy()
        self.weather_particles = alive_weather

        # Spawn weather particles
        if self.current_weather == WeatherType.RAIN:
            self._spawn_rain(dt, PARTICLE_RAIN_COUNT)
        elif self.current_weather == WeatherType.HEAVY_RAIN:
            self._spawn_rain(dt, PARTICLE_RAIN_COUNT * 2)
        elif self.current_weather == WeatherType.SNOW:
            self._spawn_snow(dt, PARTICLE_SNOW_COUNT)

    def spawn_grass_particles(self, position: Vec3, count: int = None):
        """Spawn grass particles (for slide tackles, etc.)."""
        if count is None:
            count = PARTICLE_GRASS_COUNT

        for _ in range(count):
            vel = Vec3(
                random.uniform(-3, 3),
                random.uniform(2, 6),
                random.uniform(-3, 3)
            )
            lifetime = random.uniform(0.3, 0.8)
            size = random.uniform(0.03, 0.08)
            grass_color = rgba(
                random.randint(40, 80),
                random.randint(140, 200),
                random.randint(30, 60),
                200
            )
            p = Particle(
                Vec3(position.x + random.uniform(-0.3, 0.3),
                     0.1,
                     position.z + random.uniform(-0.3, 0.3)),
                vel, lifetime, size, grass_color, gravity=-8.0
            )
            self.particles.append(p)

    def spawn_goal_celebration(self, position: Vec3):
        """Spawn celebration particles."""
        count = PARTICLE_GOAL_CELEBRATION_COUNT
        colors = [
            rgba(255, 215, 0, 255),   # Gold
            rgba(255, 255, 255, 255),  # White
            rgba(255, 50, 50, 255),    # Red
            rgba(50, 50, 255, 255),    # Blue
            rgba(50, 255, 50, 255),    # Green
        ]

        for _ in range(count):
            vel = Vec3(
                random.uniform(-8, 8),
                random.uniform(5, 15),
                random.uniform(-8, 8)
            )
            lifetime = random.uniform(1.0, 3.0)
            size = random.uniform(0.05, 0.15)
            c = random.choice(colors)
            p = Particle(
                Vec3(position.x + random.uniform(-2, 2),
                     random.uniform(1, 5),
                     position.z + random.uniform(-2, 2)),
                vel, lifetime, size, c, gravity=-4.0
            )
            self.particles.append(p)

    def spawn_ball_trail(self, position: Vec3, ball_speed: float):
        """Spawn trail particles behind a fast-moving ball."""
        if ball_speed < 15:
            return

        intensity = clamp((ball_speed - 15) / 20, 0, 1)
        count = int(intensity * 3) + 1

        for _ in range(count):
            vel = Vec3(
                random.uniform(-0.5, 0.5),
                random.uniform(0, 1),
                random.uniform(-0.5, 0.5)
            )
            lifetime = random.uniform(0.1, 0.3)
            size = random.uniform(0.02, 0.05) * intensity
            trail_color = rgba(255, 255, 255, int(150 * intensity))
            p = Particle(
                Vec3(position.x, position.y, position.z),
                vel, lifetime, size, trail_color, gravity=0, fade=True
            )
            self.particles.append(p)

    def spawn_impact(self, position: Vec3, intensity: float = 1.0):
        """Spawn impact particles (ball hitting ground/post)."""
        count = int(8 * intensity)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6) * intensity
            vel = Vec3(
                math.cos(angle) * speed,
                random.uniform(1, 4) * intensity,
                math.sin(angle) * speed
            )
            lifetime = random.uniform(0.2, 0.5)
            size = random.uniform(0.02, 0.06)
            c = rgba(200, 200, 200, 200)
            p = Particle(position, vel, lifetime, size, c, gravity=-10.0)
            self.particles.append(p)

    def spawn_dust(self, position: Vec3, count: int = 5):
        """Spawn dust cloud particles."""
        for _ in range(count):
            vel = Vec3(
                random.uniform(-1, 1),
                random.uniform(0.5, 2),
                random.uniform(-1, 1)
            )
            lifetime = random.uniform(0.5, 1.0)
            size = random.uniform(0.1, 0.3)
            c = rgba(160, 140, 100, 100)
            p = Particle(
                Vec3(position.x, 0.1, position.z),
                vel, lifetime, size, c, gravity=-1.0
            )
            self.particles.append(p)

    def _spawn_rain(self, dt: float, target_count: int):
        """Spawn rain particles around the camera."""
        current_count = len(self.weather_particles)
        spawn_count = max(0, int((target_count - current_count) * dt * 10))
        spawn_count = min(spawn_count, 20)  # Cap per frame

        cam_pos = camera.position if hasattr(camera, 'position') else Vec3(0, 20, 0)

        for _ in range(spawn_count):
            x = cam_pos.x + random.uniform(-40, 40)
            z = cam_pos.z + random.uniform(-40, 40)
            y = random.uniform(20, 40)

            vel = Vec3(random.uniform(-1, 1), -20, random.uniform(-1, 1))
            lifetime = random.uniform(1.0, 2.0)
            size = random.uniform(0.01, 0.03)
            rain_color = rgba(150, 180, 220, 150)

            p = Particle(Vec3(x, y, z), vel, lifetime, size, rain_color,
                         gravity=-5.0, fade=False)
            self.weather_particles.append(p)

    def _spawn_snow(self, dt: float, target_count: int):
        """Spawn snow particles."""
        current_count = len(self.weather_particles)
        spawn_count = max(0, int((target_count - current_count) * dt * 5))
        spawn_count = min(spawn_count, 10)

        cam_pos = camera.position if hasattr(camera, 'position') else Vec3(0, 20, 0)

        for _ in range(spawn_count):
            x = cam_pos.x + random.uniform(-40, 40)
            z = cam_pos.z + random.uniform(-40, 40)
            y = random.uniform(15, 35)

            vel = Vec3(
                random.uniform(-2, 2),
                random.uniform(-3, -1),
                random.uniform(-2, 2)
            )
            lifetime = random.uniform(3.0, 8.0)
            size = random.uniform(0.03, 0.08)
            snow_color = rgba(240, 245, 255, 200)

            p = Particle(Vec3(x, y, z), vel, lifetime, size, snow_color,
                         gravity=-0.5, fade=False)
            self.weather_particles.append(p)

    def set_weather(self, weather: WeatherType):
        """Change weather effect."""
        if weather != self.current_weather:
            # Clear old weather particles
            for p in self.weather_particles:
                p.destroy()
            self.weather_particles.clear()
            self.current_weather = weather

    def clear_all(self):
        """Remove all particles."""
        for p in self.particles:
            p.destroy()
        self.particles.clear()
        for p in self.weather_particles:
            p.destroy()
        self.weather_particles.clear()

    def cleanup(self):
        self.clear_all()


class ScreenFlash:
    """Full screen flash effect for goals etc."""

    def __init__(self):
        self.flash_entity = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(255, 255, 255, 0),
            scale=(3, 3),
            z=-10,
            enabled=False,
        )
        self.flash_timer = 0
        self.flash_duration = 0

    def flash(self, flash_color=color.white, duration=0.3):
        self.flash_entity.color = flash_color
        self.flash_entity.enabled = True
        self.flash_timer = duration
        self.flash_duration = duration

    def update(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
            alpha = clamp(self.flash_timer / self.flash_duration, 0, 1)
            c = self.flash_entity.color
            self.flash_entity.color = rgba(
                int(c.r * 255) if hasattr(c, 'r') else 255,
                int(c.g * 255) if hasattr(c, 'g') else 255,
                int(c.b * 255) if hasattr(c, 'b') else 255,
                int(alpha * 200)
            )
            if self.flash_timer <= 0:
                self.flash_entity.enabled = False

    def cleanup(self):
        try:
            self.flash_entity.disable()
        except Exception:
            pass


class SlowMotion:
    """Slow motion effect for replays and dramatic moments."""

    def __init__(self):
        self.active = False
        self.time_scale = 1.0
        self.target_scale = 1.0
        self.duration = 0.0
        self.timer = 0.0

    def activate(self, time_scale=0.3, duration=2.0):
        self.active = True
        self.target_scale = time_scale
        self.duration = duration
        self.timer = duration

    def deactivate(self):
        self.active = False
        self.target_scale = 1.0

    def update(self, dt):
        if self.active:
            self.timer -= dt
            if self.timer <= 0:
                self.deactivate()

            # Smooth transition
            self.time_scale = lerp(self.time_scale, self.target_scale, dt * 5)
        else:
            self.time_scale = lerp(self.time_scale, 1.0, dt * 5)

    def get_dt(self, dt):
        return dt * self.time_scale
