"""
Ultimate Soccer 3D - Sound Manager
Handles all game audio: ambient, effects, crowd, whistle.
Uses Ursina's built-in audio system with fallback for missing files.
"""
import random
from ursina import Audio, Entity
from config import (
    SOUND_MASTER_VOLUME, SOUND_MUSIC_VOLUME, SOUND_SFX_VOLUME,
    SOUND_CROWD_VOLUME, SOUND_COMMENTARY_VOLUME,
)


class SoundManager:
    """Manages all game sounds."""

    def __init__(self):
        self.master_volume = SOUND_MASTER_VOLUME
        self.music_volume = SOUND_MUSIC_VOLUME
        self.sfx_volume = SOUND_SFX_VOLUME
        self.crowd_volume = SOUND_CROWD_VOLUME
        self.enabled = True
        self.sounds = {}
        self.crowd_state = 'normal'  # normal, excited, roar, quiet
        self.crowd_timer = 0.0
        self.crowd_intensity = 0.5

    def play(self, sound_name: str, volume: float = 1.0, pitch: float = 1.0):
        """Play a sound effect. Silently fails if sound file doesn't exist."""
        if not self.enabled:
            return None
        try:
            vol = volume * self.sfx_volume * self.master_volume
            s = Audio(sound_name, volume=vol, pitch=pitch, autoplay=True)
            return s
        except Exception:
            return None

    def play_kick(self, power: float = 0.5):
        pitch = 0.8 + power * 0.4
        return self.play('kick', volume=0.6 + power * 0.4, pitch=pitch)

    def play_whistle(self, whistle_type: str = 'short'):
        if whistle_type == 'long':
            return self.play('whistle_long', volume=0.8)
        return self.play('whistle', volume=0.7)

    def play_crowd_roar(self):
        self.crowd_state = 'roar'
        self.crowd_timer = 3.0
        return self.play('crowd_roar', volume=self.crowd_volume * self.master_volume)

    def play_crowd_groan(self):
        return self.play('crowd_groan', volume=self.crowd_volume * 0.6 * self.master_volume)

    def play_goal_sound(self):
        self.crowd_state = 'roar'
        self.crowd_timer = 5.0
        self.play('goal_horn', volume=0.8)
        return self.play_crowd_roar()

    def play_card_sound(self):
        return self.play('card', volume=0.5)

    def play_bounce(self, intensity: float = 0.5):
        return self.play('bounce', volume=0.3 * intensity, pitch=0.9 + intensity * 0.3)

    def play_tackle(self):
        return self.play('tackle', volume=0.5)

    def play_header(self):
        return self.play('header', volume=0.4, pitch=0.7)

    def play_post_hit(self):
        return self.play('post_hit', volume=0.7)

    def play_net_ripple(self):
        return self.play('net', volume=0.5)

    def update(self, dt: float, match=None):
        """Update sound state."""
        if not self.enabled:
            return

        self.crowd_timer -= dt
        if self.crowd_timer <= 0:
            self.crowd_state = 'normal'

        # Adjust crowd intensity based on match state
        if match:
            ball_speed = match.ball.speed
            if ball_speed > 15:
                self.crowd_intensity = min(1.0, self.crowd_intensity + dt * 0.5)
            else:
                self.crowd_intensity = max(0.3, self.crowd_intensity - dt * 0.2)

    def set_master_volume(self, volume: float):
        self.master_volume = max(0.0, min(1.0, volume))

    def set_sfx_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))

    def set_crowd_volume(self, volume: float):
        self.crowd_volume = max(0.0, min(1.0, volume))

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def cleanup(self):
        """Clean up all sounds."""
        for key, sound in self.sounds.items():
            try:
                sound.stop()
            except Exception:
                pass
        self.sounds.clear()
