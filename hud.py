"""
Ultimate Soccer 3D - HUD System
Scoreboard, minimap, player indicators, power bars, commentary text.
"""
import math
from ursina import (
    Entity, Text, Vec2, Vec3, color, camera, window,
    time as ursina_time, Quad, Button,
)
from config import (
    HUD_SCOREBOARD_OPACITY, HUD_MINIMAP_SIZE, HUD_MINIMAP_OPACITY,
    HUD_POWER_BAR_WIDTH, HUD_POWER_BAR_HEIGHT, HUD_COMMENTARY_DURATION,
    HUD_STAMINA_BAR_WIDTH, HUD_STAMINA_BAR_HEIGHT,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH,
    GameState, CardType, rgb, rgba,
)
from utils import format_match_time, clamp


class HUD:
    """In-game heads-up display."""

    def __init__(self):
        self.elements = []
        self.visible = True
        self.minimap_visible = True

        # Scoreboard
        self.scoreboard_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 0, int(HUD_SCOREBOARD_OPACITY * 255)),
            scale=(0.5, 0.06),
            position=(0, 0.45),
            z=-1,
        )
        self.elements.append(self.scoreboard_bg)

        self.home_name_text = Text(
            text='HOME',
            parent=camera.ui,
            position=(-0.18, 0.455),
            scale=0.8,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(self.home_name_text)

        self.score_text = Text(
            text='0 - 0',
            parent=camera.ui,
            position=(0, 0.455),
            scale=1.2,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(self.score_text)

        self.away_name_text = Text(
            text='AWAY',
            parent=camera.ui,
            position=(0.18, 0.455),
            scale=0.8,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(self.away_name_text)

        self.time_text = Text(
            text="00'",
            parent=camera.ui,
            position=(0, 0.415),
            scale=0.7,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(self.time_text)

        self.half_text = Text(
            text='1ST HALF',
            parent=camera.ui,
            position=(0, 0.39),
            scale=0.5,
            color=color.light_gray,
            origin=(0, 0),
        )
        self.elements.append(self.half_text)

        # Power bar
        self.power_bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 0, 150),
            scale=(0.15, 0.015),
            position=(0, -0.35),
            z=-1,
            enabled=False,
        )
        self.elements.append(self.power_bar_bg)

        self.power_bar_fill = Entity(
            parent=camera.ui,
            model='quad',
            color=color.green,
            scale=(0.0, 0.012),
            position=(-0.075, -0.35),
            origin=(-0.5, 0),
            z=-2,
            enabled=False,
        )
        self.elements.append(self.power_bar_fill)

        self.power_bar_label = Text(
            text='POWER',
            parent=camera.ui,
            position=(0, -0.33),
            scale=0.5,
            color=color.white,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.power_bar_label)

        # Stamina bar (small, under selected player)
        self.stamina_bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 0, 120),
            scale=(0.08, 0.006),
            position=(0, -0.38),
            z=-1,
            enabled=False,
        )
        self.elements.append(self.stamina_bar_bg)

        self.stamina_bar_fill = Entity(
            parent=camera.ui,
            model='quad',
            color=color.lime,
            scale=(0.08, 0.005),
            position=(-0.04, -0.38),
            origin=(-0.5, 0),
            z=-2,
            enabled=False,
        )
        self.elements.append(self.stamina_bar_fill)

        # Commentary text
        self.commentary_text = Text(
            text='',
            parent=camera.ui,
            position=(0, -0.25),
            scale=0.7,
            color=color.white,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.commentary_text)
        self.commentary_timer = 0.0
        self.commentary_queue = []

        # Event text (GOAL!, FOUL, OFFSIDE, etc.)
        self.event_text = Text(
            text='',
            parent=camera.ui,
            position=(0, 0.1),
            scale=2.0,
            color=color.yellow,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.event_text)
        self.event_timer = 0.0

        # Card display
        self.card_display = Entity(
            parent=camera.ui,
            model='quad',
            color=color.yellow,
            scale=(0.03, 0.045),
            position=(0.3, 0.3),
            z=-2,
            enabled=False,
        )
        self.elements.append(self.card_display)
        self.card_text = Text(
            text='',
            parent=camera.ui,
            position=(0.3, 0.26),
            scale=0.5,
            color=color.white,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.card_text)
        self.card_timer = 0.0

        # Minimap
        self.minimap_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(20, 80, 20, int(HUD_MINIMAP_OPACITY * 255)),
            scale=(0.25, 0.15),
            position=(0.62, -0.32),
            z=-1,
        )
        self.elements.append(self.minimap_bg)

        self.minimap_border = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(255, 255, 255, 100),
            scale=(0.252, 0.152),
            position=(0.62, -0.32),
            z=-0.5,
        )
        self.elements.append(self.minimap_border)

        # Minimap center line
        self.minimap_center = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(255, 255, 255, 60),
            scale=(0.001, 0.15),
            position=(0.62, -0.32),
            z=-2,
        )
        self.elements.append(self.minimap_center)

        # Minimap dots for players
        self.minimap_dots = []
        self.minimap_ball_dot = Entity(
            parent=camera.ui,
            model='circle',
            color=color.white,
            scale=0.008,
            position=(0.62, -0.32),
            z=-3,
        )
        self.elements.append(self.minimap_ball_dot)

        # Player info (selected player name)
        self.player_info_text = Text(
            text='',
            parent=camera.ui,
            position=(-0.6, -0.42),
            scale=0.6,
            color=color.white,
            origin=(-0.5, 0),
        )
        self.elements.append(self.player_info_text)

        # Match state text (HALFTIME, PAUSED, etc.)
        self.state_text = Text(
            text='',
            parent=camera.ui,
            position=(0, 0.2),
            scale=1.5,
            color=color.white,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.state_text)

        # Added time indicator
        self.added_time_text = Text(
            text='',
            parent=camera.ui,
            position=(0.08, 0.415),
            scale=0.6,
            color=color.red,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.added_time_text)

        # Goal scorer display
        self.goal_scorer_text = Text(
            text='',
            parent=camera.ui,
            position=(0, 0.0),
            scale=1.0,
            color=color.white,
            origin=(0, 0),
            enabled=False,
        )
        self.elements.append(self.goal_scorer_text)

        # Controls hint
        self.controls_hint = Text(
            text='[WASD] Move  [Space] Pass/Switch  [Q] Shoot/Tackle  [E] Through/Press  [Shift] Sprint',
            parent=camera.ui,
            position=(0, -0.46),
            scale=0.4,
            color=rgba(255, 255, 255, 100),
            origin=(0, 0),
        )
        self.elements.append(self.controls_hint)

    def update(self, dt: float, match=None):
        """Update HUD elements."""
        if not match:
            return

        # Update scoreboard
        self.score_text.text = f"{match.home_score} - {match.away_score}"
        self.time_text.text = match.match_time_str
        self.half_text.text = '1ST HALF' if match.half == 1 else '2ND HALF'

        # Team names
        self.home_name_text.text = match.home_team.team_data.get('short_name', 'HOME') if match.home_team.team_data else 'HOME'
        self.away_name_text.text = match.away_team.team_data.get('short_name', 'AWAY') if match.away_team.team_data else 'AWAY'

        # Added time
        if match.is_extra_time and match.added_time > 0:
            self.added_time_text.text = f"+{int(match.added_time / 15)}"
            self.added_time_text.enabled = True
        else:
            self.added_time_text.enabled = False

        # Power bar
        controlled = match.home_team.selected_player if match.home_team.is_human else None
        if not controlled:
            controlled = match.away_team.selected_player if match.away_team.is_human else None

        if controlled and controlled.is_charging:
            self.power_bar_bg.enabled = True
            self.power_bar_fill.enabled = True
            self.power_bar_label.enabled = True
            fill = controlled.power_charge
            self.power_bar_fill.scale_x = 0.15 * fill
            # Color: green -> yellow -> red
            if fill < 0.5:
                self.power_bar_fill.color = color.green
            elif fill < 0.8:
                self.power_bar_fill.color = color.yellow
            else:
                self.power_bar_fill.color = color.red
            label = controlled.charge_type.upper() if controlled.charge_type else 'POWER'
            self.power_bar_label.text = label
        else:
            self.power_bar_bg.enabled = False
            self.power_bar_fill.enabled = False
            self.power_bar_label.enabled = False

        # Stamina bar
        if controlled:
            self.stamina_bar_bg.enabled = True
            self.stamina_bar_fill.enabled = True
            stamina_pct = controlled.stamina / 100.0
            self.stamina_bar_fill.scale_x = 0.08 * stamina_pct
            if stamina_pct > 0.5:
                self.stamina_bar_fill.color = color.lime
            elif stamina_pct > 0.2:
                self.stamina_bar_fill.color = color.yellow
            else:
                self.stamina_bar_fill.color = color.red

            self.player_info_text.text = f"#{controlled.number} {controlled.name}"
        else:
            self.stamina_bar_bg.enabled = False
            self.stamina_bar_fill.enabled = False
            self.player_info_text.text = ''

        # Commentary
        if self.commentary_timer > 0:
            self.commentary_timer -= dt
            if self.commentary_timer <= 0:
                self.commentary_text.enabled = False
                if self.commentary_queue:
                    self._show_next_commentary()

        # Event text
        if self.event_timer > 0:
            self.event_timer -= dt
            # Fade effect
            alpha = min(1.0, self.event_timer / 0.5)
            self.event_text.color = rgba(255, 255, 0, int(alpha * 255))
            if self.event_timer <= 0:
                self.event_text.enabled = False

        # Card display
        if self.card_timer > 0:
            self.card_timer -= dt
            if self.card_timer <= 0:
                self.card_display.enabled = False
                self.card_text.enabled = False

        # Goal scorer display
        if match.state == GameState.MATCH_GOAL and match.last_goal_scorer:
            self.goal_scorer_text.enabled = True
            scorer = match.last_goal_scorer
            self.goal_scorer_text.text = f"GOAL! {scorer.name} {match.match_minute}'"
        else:
            self.goal_scorer_text.enabled = False

        # Match state text
        if match.state == GameState.MATCH_PAUSED:
            self.state_text.text = 'PAUSED'
            self.state_text.enabled = True
        elif match.state == GameState.MATCH_HALFTIME:
            self.state_text.text = 'HALF TIME'
            self.state_text.enabled = True
        elif match.state == GameState.MATCH_FULLTIME:
            self.state_text.text = 'FULL TIME'
            self.state_text.enabled = True
        else:
            self.state_text.enabled = False

        # Update minimap
        if self.minimap_visible:
            self._update_minimap(match)

    def _update_minimap(self, match):
        """Update minimap dots."""
        # Clear old dots
        for dot in self.minimap_dots:
            dot.disable()
        self.minimap_dots.clear()

        map_cx = 0.62
        map_cy = -0.32
        map_hw = 0.125
        map_hh = 0.075

        def world_to_minimap(wx, wz):
            mx = map_cx + (wx / FIELD_HALF_LENGTH) * map_hw
            my = map_cy + (wz / FIELD_HALF_WIDTH) * map_hh
            return mx, my

        # Home team dots
        for p in match.home_team.players:
            if p.is_sent_off:
                continue
            mx, my = world_to_minimap(p.position.x, p.position.z)
            home_color = match.home_team.team_color
            dot = Entity(
                parent=camera.ui,
                model='circle',
                color=rgb(int(home_color[0]*255), int(home_color[1]*255), int(home_color[2]*255)),
                scale=0.006,
                position=(mx, my),
                z=-3,
            )
            self.minimap_dots.append(dot)

        # Away team dots
        for p in match.away_team.players:
            if p.is_sent_off:
                continue
            mx, my = world_to_minimap(p.position.x, p.position.z)
            away_color = match.away_team.team_color
            dot = Entity(
                parent=camera.ui,
                model='circle',
                color=rgb(int(away_color[0]*255), int(away_color[1]*255), int(away_color[2]*255)),
                scale=0.006,
                position=(mx, my),
                z=-3,
            )
            self.minimap_dots.append(dot)

        # Ball dot
        bx, by = world_to_minimap(match.ball.position.x, match.ball.position.z)
        self.minimap_ball_dot.position = (bx, by)

    def show_event(self, text: str, duration: float = 2.0):
        """Show a large event text."""
        self.event_text.text = text
        self.event_text.enabled = True
        self.event_text.color = color.yellow
        self.event_timer = duration

    def show_commentary(self, text: str):
        """Show commentary text."""
        if self.commentary_timer > 0:
            self.commentary_queue.append(text)
        else:
            self.commentary_text.text = text
            self.commentary_text.enabled = True
            self.commentary_timer = HUD_COMMENTARY_DURATION

    def _show_next_commentary(self):
        if self.commentary_queue:
            text = self.commentary_queue.pop(0)
            self.commentary_text.text = text
            self.commentary_text.enabled = True
            self.commentary_timer = HUD_COMMENTARY_DURATION

    def show_card(self, card_type: CardType, player_name: str):
        """Show a card being given."""
        if card_type == CardType.YELLOW:
            self.card_display.color = color.yellow
            self.card_text.text = f"YELLOW CARD\n{player_name}"
        elif card_type in [CardType.RED, CardType.SECOND_YELLOW]:
            self.card_display.color = color.red
            self.card_text.text = f"RED CARD\n{player_name}"
        else:
            return

        self.card_display.enabled = True
        self.card_text.enabled = True
        self.card_timer = 3.0

    def show_goal(self, scorer_name: str, minute: int, home_score: int, away_score: int):
        """Show goal display."""
        self.show_event(f"GOOOAL!", 3.0)
        self.goal_scorer_text.text = f"{scorer_name} {minute}'"
        self.goal_scorer_text.enabled = True

    def toggle_minimap(self):
        """Toggle minimap visibility."""
        self.minimap_visible = not self.minimap_visible
        self.minimap_bg.enabled = self.minimap_visible
        self.minimap_border.enabled = self.minimap_visible
        self.minimap_center.enabled = self.minimap_visible
        self.minimap_ball_dot.enabled = self.minimap_visible

    def set_visible(self, visible: bool):
        """Show/hide entire HUD."""
        self.visible = visible
        for element in self.elements:
            element.enabled = visible

    def cleanup(self):
        """Remove all HUD elements."""
        for element in self.elements:
            try:
                element.disable()
            except Exception:
                pass
        for dot in self.minimap_dots:
            try:
                dot.disable()
            except Exception:
                pass
        self.elements.clear()
        self.minimap_dots.clear()
