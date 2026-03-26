"""
Ultimate Soccer 3D - Main Entry Point
Game initialization, main loop, and system coordination.
"""
import random
from ursina import (
    Ursina, window, camera, color, Vec3, Vec2,
    held_keys, time as ursina_time, application, mouse,
    Entity, Text, input_handler,
)
from config import (
    WINDOW_TITLE, WINDOW_SIZE, WINDOW_FULLSCREEN, WINDOW_FPS_LIMIT,
    GameState, WeatherType, CameraMode, SetPieceType, CardType, rgba,
)

# ── Global game state ──────────────────────────────────────────────
game = None


class Game:
    """Main game class coordinating all systems."""

    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.match = None
        self.field = None
        self.ball = None
        self.home_team = None
        self.away_team = None
        self.physics = None
        self.referee = None
        self.camera_system = None
        self.controller = None
        self.hud = None
        self.effects = None
        self.screen_flash = None
        self.slow_motion = None
        self.commentary = None
        self.sound = None
        self.replay_buffer = None
        self.replay_player = None
        self.weather = WeatherType.CLEAR
        self.frame_count = 0
        self.last_event_check = 0

        # Lazy imports to avoid circular issues
        from menu import MenuSystem
        self.menu = MenuSystem(
            on_start_match=self.start_match,
            on_quit=self.quit_to_menu,
        )

    def start_match(self, home_id: str, away_id: str, difficulty: str = 'professional'):
        """Initialize and start a new match."""
        from field import Field
        from ball import Ball
        from team_manager import TeamManager
        from physics_engine import PhysicsEngine
        from referee import Referee
        from match import Match
        from camera_system import CameraSystem
        from player_controller import PlayerController
        from hud import HUD
        from effects import ParticleSystem, ScreenFlash, SlowMotion
        from commentary import Commentary
        from sound import SoundManager
        from replay import ReplayBuffer, ReplayPlayer

        self._cleanup_match()

        weather_choices = [
            WeatherType.CLEAR, WeatherType.CLEAR, WeatherType.CLEAR,
            WeatherType.CLOUDY, WeatherType.NIGHT,
            WeatherType.RAIN, WeatherType.SNOW,
        ]
        self.weather = random.choice(weather_choices)

        self.field = Field(self.weather)
        self.ball = Ball()
        self.ball.set_weather(self.weather)

        self.home_team = TeamManager(home_id, 1, is_human=True, difficulty=difficulty)
        self.away_team = TeamManager(away_id, -1, is_human=False, difficulty=difficulty)
        self.home_team.create_players()
        self.away_team.create_players()

        self.physics = PhysicsEngine()
        self.referee = Referee(difficulty)
        self.camera_system = CameraSystem()
        self.controller = PlayerController(self.home_team, self.camera_system)
        self.hud = HUD()
        self.effects = ParticleSystem()
        self.effects.set_weather(self.weather)
        self.screen_flash = ScreenFlash()
        self.slow_motion = SlowMotion()
        self.commentary = Commentary()
        self.sound = SoundManager()
        self.replay_buffer = ReplayBuffer()
        self.replay_player = ReplayPlayer()

        self.match = Match(
            self.home_team, self.away_team, self.ball,
            self.field, self.referee, self.physics, difficulty
        )

        self.match.start()
        self.state = GameState.MATCH_INTRO
        self.camera_system.setup_kickoff_camera()

        self.menu.hide()
        mouse.visible = False
        self.last_event_check = 0

        text = self.commentary.on_event('kickoff')
        if text:
            self.hud.show_commentary(text)

    def quit_to_menu(self):
        """Return to main menu."""
        self._cleanup_match()
        self.state = GameState.MAIN_MENU
        self.menu._build_main_menu()
        self.menu.is_visible = True
        mouse.visible = True

    def _cleanup_match(self):
        """Clean up current match resources."""
        for attr in ['match', 'field', 'ball', 'hud', 'effects',
                     'screen_flash', 'sound', 'home_team', 'away_team']:
            obj = getattr(self, attr, None)
            if obj and hasattr(obj, 'cleanup'):
                try:
                    obj.cleanup()
                except Exception:
                    pass
            setattr(self, attr, None)
        self.controller = None
        self.physics = None
        self.referee = None
        self.camera_system = None
        self.slow_motion = None
        self.commentary = None
        self.replay_buffer = None
        self.replay_player = None

    # ── Match event handlers ────────────────────────────────────────

    def _process_match_events(self):
        if not self.match or not self.match.events:
            return
        while self.last_event_check < len(self.match.events):
            event = self.match.events[self.last_event_check]
            self.last_event_check += 1
            handler = getattr(self, f'_on_{event.event_type}', None)
            if handler:
                handler(event)

    def _on_goal(self, event):
        scorer_name = event.data.get('scorer', None)
        if scorer_name and hasattr(scorer_name, 'name'):
            scorer_name = scorer_name.name
        else:
            scorer_name = str(scorer_name) if scorer_name else 'Unknown'
        score = event.data.get('score', '')
        if self.screen_flash:
            self.screen_flash.flash(rgba(255, 255, 200, 200), 0.5)
        if self.camera_system:
            self.camera_system.trigger_shake(0.4, 0.5)
        if self.effects and self.ball:
            self.effects.spawn_goal_celebration(self.ball.position)
        if self.slow_motion:
            self.slow_motion.activate(0.3, 1.5)
        if self.hud:
            self.hud.show_event('GOOOAL!', 3.0)
            text = self.commentary.on_event('goal', scorer=scorer_name,
                                             team=event.data.get('team', ''),
                                             score=score)
            if text:
                self.hud.show_commentary(text)
        if self.sound:
            self.sound.play_goal_sound()
        if self.camera_system and self.match.last_goal_scorer:
            self.camera_system.setup_celebration_camera(self.match.last_goal_scorer.position)

    def _on_foul(self, event):
        offender = event.data.get('offender', '')
        victim = event.data.get('victim', '')
        card_str = event.data.get('card', '')
        if self.hud:
            text = self.commentary.on_event('foul', offender=offender, victim=victim)
            if text:
                self.hud.show_commentary(text)
            self.hud.show_event('FOUL!', 1.5)
        if self.sound:
            self.sound.play_whistle()
        if card_str and 'YELLOW' in card_str.upper():
            if self.hud:
                self.hud.show_card(CardType.YELLOW, offender)
                ct = self.commentary.on_event('yellow_card', player=offender)
                if ct:
                    self.hud.show_commentary(ct)
            if self.sound:
                self.sound.play_card_sound()
        elif card_str and 'RED' in card_str.upper():
            if self.hud:
                self.hud.show_card(CardType.RED, offender)
                ct = self.commentary.on_event('red_card', player=offender)
                if ct:
                    self.hud.show_commentary(ct)
            if self.sound:
                self.sound.play_card_sound()
        if self.effects and self.ball:
            self.effects.spawn_grass_particles(self.ball.position, 8)

    def _on_offside(self, event):
        player_name = event.data.get('player', '')
        if self.hud:
            self.hud.show_event('OFFSIDE!', 2.0)
            text = self.commentary.on_event('offside', player=player_name)
            if text:
                self.hud.show_commentary(text)
        if self.sound:
            self.sound.play_whistle()

    def _on_save(self, event):
        player_name = event.data.get('player', '')
        if self.hud:
            text = self.commentary.on_event('save', player=player_name)
            if text:
                self.hud.show_commentary(text)
        if self.camera_system:
            self.camera_system.trigger_shake(0.15, 0.2)

    def _on_parry(self, event):
        player_name = event.data.get('player', '')
        if self.hud:
            text = self.commentary.on_event('parry', player=player_name)
            if text:
                self.hud.show_commentary(text)

    def _on_tackle(self, event):
        player_name = event.data.get('player', '')
        if self.hud:
            text = self.commentary.on_event('tackle', player=player_name)
            if text:
                self.hud.show_commentary(text)
        if self.effects and self.ball:
            self.effects.spawn_grass_particles(self.ball.position, 5)
        if self.sound:
            self.sound.play_tackle()

    def _on_advantage(self, event):
        if self.hud:
            text = self.commentary.on_event('advantage')
            if text:
                self.hud.show_commentary(text)

    def _on_halftime(self, event):
        if self.hud:
            self.hud.show_event('HALF TIME', 3.0)
            text = self.commentary.on_event('halftime',
                                             home_score=self.match.home_score,
                                             away_score=self.match.away_score)
            if text:
                self.hud.show_commentary(text)
        if self.sound:
            self.sound.play_whistle('long')
        if self.menu:
            self.menu.build_halftime_screen(self.match)
            self.menu.is_visible = True
            mouse.visible = True

    def _on_fulltime(self, event):
        if self.hud:
            self.hud.show_event('FULL TIME', 4.0)
            text = self.commentary.on_event('fulltime',
                                             home_score=self.match.home_score,
                                             away_score=self.match.away_score)
            if text:
                self.hud.show_commentary(text)
        if self.sound:
            self.sound.play_whistle('long')

    def _on_penalty(self, event):
        if self.hud:
            team_name = event.data.get('team', '')
            text = self.commentary.on_event('penalty', team=team_name)
            if text:
                self.hud.show_commentary(text)
            self.hud.show_event('PENALTY!', 2.5)
        if self.sound:
            self.sound.play_whistle()

    def _check_state_transitions(self):
        if not self.match:
            return
        ms = self.match.state
        if ms == GameState.MATCH_FULLTIME and self.state != GameState.MATCH_FULLTIME:
            self.state = GameState.MATCH_FULLTIME
            if self.menu:
                self.menu.build_fulltime_screen(self.match)
                self.menu.is_visible = True
                mouse.visible = True
        elif ms == GameState.MATCH_HALFTIME and self.state != GameState.MATCH_HALFTIME:
            self.state = GameState.MATCH_HALFTIME
        elif ms == GameState.MATCH_PLAYING:
            if self.state in [GameState.MATCH_HALFTIME, GameState.MATCH_INTRO]:
                if self.menu and self.menu.is_visible:
                    self.menu.hide()
                    mouse.visible = False
            self.state = GameState.MATCH_PLAYING
        elif ms == GameState.MATCH_INTRO:
            self.state = GameState.MATCH_INTRO
        elif ms == GameState.SET_PIECE:
            self.state = GameState.SET_PIECE
        elif ms == GameState.MATCH_GOAL:
            self.state = GameState.MATCH_GOAL

    def _apply_replay_frame(self, frame):
        if self.ball:
            self.ball.position = frame.ball_pos
            self.ball._update_entity()
        for player in self.match.all_players:
            if player.id in frame.player_positions:
                player.position = frame.player_positions[player.id]
                player._update_entity()
            if player.id in frame.player_facings:
                player.facing_angle = frame.player_facings[player.id]


# ── Module-level Ursina hooks (called automatically by the engine) ──

def update():
    """Called every frame by Ursina."""
    if game is None:
        return
    dt = ursina_time.dt
    game.frame_count += 1

    if game.state == GameState.MAIN_MENU:
        return
    if not game.match:
        return

    effective_dt = dt
    if game.slow_motion:
        effective_dt = game.slow_motion.get_dt(dt)
        game.slow_motion.update(dt)

    # Replay
    if game.replay_player and game.replay_player.is_active:
        frame = game.replay_player.update(dt)
        if frame:
            game._apply_replay_frame(frame)
            cam_pos, cam_look = game.replay_player.get_camera_position(frame.ball_pos)
            camera.position = cam_pos
            camera.look_at(cam_look)
        else:
            game.camera_system.set_mode(CameraMode.BROADCAST)
        return

    game.match.update(effective_dt)
    game._process_match_events()

    if game.controller and game.match.state == GameState.MATCH_PLAYING:
        game.controller.update(effective_dt, game.ball, game.away_team)
    elif game.controller and game.match.state == GameState.SET_PIECE:
        if game.home_team.is_human and game.referee and game.referee.set_piece_team == game.home_team:
            taken = game.controller.handle_set_piece_input(game.ball, game.match)
            if taken:
                game.match._resume_play()

    if game.camera_system:
        bv = game.ball.velocity if game.ball else Vec3(0, 0, 0)
        bp = game.ball.position if game.ball else Vec3(0, 0, 0)
        game.camera_system.update(effective_dt, bp, bv)

    if game.effects:
        game.effects.update(effective_dt)
        if game.ball and game.ball.speed > 15:
            game.effects.spawn_ball_trail(game.ball.position, game.ball.speed)

    if game.screen_flash:
        game.screen_flash.update(dt)
    if game.hud:
        game.hud.update(dt, game.match)
    if game.commentary:
        game.commentary.update(dt)
        if game.match.state == GameState.MATCH_PLAYING:
            ambient = game.commentary.get_ambient_commentary(game.match)
            if ambient and game.hud:
                game.hud.show_commentary(ambient)
    if game.sound:
        game.sound.update(dt, game.match)

    if game.replay_buffer and game.match.state == GameState.MATCH_PLAYING:
        game.replay_buffer.record(dt, game.match.match_time, game.ball, game.match.all_players)

    game._check_state_transitions()


def input(key):
    """Called by Ursina on key events."""
    if game is None:
        return
    if game.state == GameState.MAIN_MENU:
        return
    if not game.match:
        return

    if key == 'escape':
        if game.match.state in [GameState.MATCH_PLAYING, GameState.SET_PIECE]:
            paused = game.match.toggle_pause()
            if paused:
                game.match.state = GameState.MATCH_PAUSED
                if game.menu:
                    game.menu.build_pause_menu(game.match)
                    game.menu.is_visible = True
                mouse.visible = True
            else:
                game.match.state = GameState.MATCH_PLAYING
                if game.menu:
                    game.menu.hide()
                mouse.visible = False
        elif game.match.state == GameState.MATCH_PAUSED:
            game.match.is_paused = False
            game.match.state = GameState.MATCH_PLAYING
            if game.menu:
                game.menu.hide()
            mouse.visible = False

    if key in ['1', '2', '3', '4'] and game.camera_system:
        modes = {
            '1': CameraMode.BROADCAST, '2': CameraMode.DYNAMIC,
            '3': CameraMode.END_TO_END, '4': CameraMode.TACTICAL,
        }
        game.camera_system.set_mode(modes[key])
    if key == 'm' and game.hud:
        game.hud.toggle_minimap()
    if key == 'v' and game.replay_buffer:
        frames = game.replay_buffer.get_last_n_seconds(5.0)
        if frames and game.replay_player:
            game.replay_player.start(frames, 0.5)
    if key == 'tab' and game.controller and game.ball:
        game.home_team.cycle_selected_player(game.ball)


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == '__main__':
    app = Ursina(
        title=WINDOW_TITLE,
        borderless=False,
        fullscreen=WINDOW_FULLSCREEN,
        development_mode=True,
    )
    window.color = color.black
    mouse.visible = True

    game = Game()
    app.run()
