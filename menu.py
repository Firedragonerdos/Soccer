"""
Ultimate Soccer 3D - Menu System
Main menu, team selection, formation selection, pause menu, settings.
"""
from ursina import (
    Entity, Text, Button, Vec2, camera, color, window,
    application, mouse, held_keys, time as ursina_time,
)
from config import (
    GameState, TeamTactic, MentalityLevel, CameraMode,
    WINDOW_TITLE, DIFFICULTY_MODIFIERS, rgb, rgba,
)
from teams_data import get_team_list, get_all_leagues, get_teams_by_league, TEAMS
from formations import get_formation_names


class MenuSystem:
    """Complete menu system for the game."""

    def __init__(self, on_start_match=None, on_quit=None):
        self.on_start_match = on_start_match
        self.on_quit = on_quit

        self.current_menu = 'main'
        self.elements = []
        self.is_visible = True

        # Selection state
        self.selected_home_team = 'real_madrid'
        self.selected_away_team = 'manchester_city'
        self.selected_difficulty = 'professional'
        self.selected_home_formation = '4-3-3'
        self.selected_away_formation = '4-3-3'

        # Team list navigation
        self.team_list = list(TEAMS.keys())
        self.home_team_index = 0
        self.away_team_index = 2

        self._build_main_menu()

    def _clear_elements(self):
        """Remove all current menu elements."""
        for e in self.elements:
            try:
                e.disable()
            except Exception:
                pass
        self.elements.clear()

    def _build_main_menu(self):
        """Build the main menu."""
        self._clear_elements()
        self.current_menu = 'main'

        # Background
        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(5, 15, 5, 240),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        # Title
        title = Text(
            text='ULTIMATE SOCCER 3D',
            parent=camera.ui,
            position=(0, 0.35),
            scale=3,
            color=rgb(50, 255, 50),
            origin=(0, 0),
        )
        self.elements.append(title)

        subtitle = Text(
            text='The Beautiful Game',
            parent=camera.ui,
            position=(0, 0.27),
            scale=1.2,
            color=rgb(200, 200, 200),
            origin=(0, 0),
        )
        self.elements.append(subtitle)

        # Menu buttons
        btn_y = 0.12
        btn_spacing = 0.08

        quick_match_btn = Button(
            text='QUICK MATCH',
            parent=camera.ui,
            scale=(0.35, 0.06),
            position=(0, btn_y),
            color=rgb(30, 120, 30),
            highlight_color=rgb(50, 180, 50),
            text_color=color.white,
            on_click=self._on_quick_match,
        )
        self.elements.append(quick_match_btn)

        team_select_btn = Button(
            text='TEAM SELECT',
            parent=camera.ui,
            scale=(0.35, 0.06),
            position=(0, btn_y - btn_spacing),
            color=rgb(30, 120, 30),
            highlight_color=rgb(50, 180, 50),
            text_color=color.white,
            on_click=self._on_team_select,
        )
        self.elements.append(team_select_btn)

        settings_btn = Button(
            text='SETTINGS',
            parent=camera.ui,
            scale=(0.35, 0.06),
            position=(0, btn_y - btn_spacing * 2),
            color=rgb(30, 120, 30),
            highlight_color=rgb(50, 180, 50),
            text_color=color.white,
            on_click=self._on_settings,
        )
        self.elements.append(settings_btn)

        quit_btn = Button(
            text='QUIT',
            parent=camera.ui,
            scale=(0.35, 0.06),
            position=(0, btn_y - btn_spacing * 3),
            color=rgb(120, 30, 30),
            highlight_color=rgb(180, 50, 50),
            text_color=color.white,
            on_click=self._on_quit,
        )
        self.elements.append(quit_btn)

        # Footer
        footer = Text(
            text='v1.0 | Python + Ursina Engine',
            parent=camera.ui,
            position=(0, -0.45),
            scale=0.6,
            color=rgb(100, 100, 100),
            origin=(0, 0),
        )
        self.elements.append(footer)

        # Controls info
        controls = Text(
            text='WASD: Move | Space: Pass | Q: Shoot | E: Through Ball | Shift: Sprint | F: Skill',
            parent=camera.ui,
            position=(0, -0.38),
            scale=0.5,
            color=rgb(150, 150, 150),
            origin=(0, 0),
        )
        self.elements.append(controls)

    def _build_team_select(self):
        """Build team selection screen."""
        self._clear_elements()
        self.current_menu = 'team_select'

        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(5, 10, 20, 240),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        title = Text(
            text='SELECT TEAMS',
            parent=camera.ui,
            position=(0, 0.42),
            scale=2,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(title)

        # Home team selection
        home_label = Text(
            text='HOME TEAM (YOU)',
            parent=camera.ui,
            position=(-0.3, 0.32),
            scale=1.0,
            color=rgb(100, 200, 255),
            origin=(0, 0),
        )
        self.elements.append(home_label)

        # Home team name
        home_team_data = TEAMS.get(self.team_list[self.home_team_index], {})
        self.home_team_text = Text(
            text=home_team_data.get('name', 'Unknown'),
            parent=camera.ui,
            position=(-0.3, 0.24),
            scale=1.2,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(self.home_team_text)

        home_rating = Text(
            text=f"Rating: {home_team_data.get('rating', '?')} | {home_team_data.get('formation', '4-4-2')}",
            parent=camera.ui,
            position=(-0.3, 0.18),
            scale=0.7,
            color=color.light_gray,
            origin=(0, 0),
        )
        self.elements.append(home_rating)
        self.home_rating_text = home_rating

        # Home team color swatch
        hc = home_team_data.get('home_color', (1, 1, 1))
        home_swatch = Entity(
            parent=camera.ui,
            model='quad',
            color=rgb(int(hc[0]*255), int(hc[1]*255), int(hc[2]*255)),
            scale=(0.06, 0.06),
            position=(-0.3, 0.1),
        )
        self.elements.append(home_swatch)
        self.home_swatch = home_swatch

        # Navigation arrows for home
        home_left = Button(
            text='Prev',
            parent=camera.ui,
            scale=(0.1, 0.04),
            position=(-0.48, 0.24),
            color=rgb(60, 60, 60),
            text_color=color.white,
            on_click=lambda: self._change_team('home', -1),
        )
        self.elements.append(home_left)

        home_right = Button(
            text='Next',
            parent=camera.ui,
            scale=(0.1, 0.04),
            position=(-0.12, 0.24),
            color=rgb(60, 60, 60),
            text_color=color.white,
            on_click=lambda: self._change_team('home', 1),
        )
        self.elements.append(home_right)

        # VS text
        vs_text = Text(
            text='VS',
            parent=camera.ui,
            position=(0, 0.24),
            scale=2,
            color=color.red,
            origin=(0, 0),
        )
        self.elements.append(vs_text)

        # Away team selection
        away_label = Text(
            text='AWAY TEAM (CPU)',
            parent=camera.ui,
            position=(0.3, 0.32),
            scale=1.0,
            color=rgb(255, 100, 100),
            origin=(0, 0),
        )
        self.elements.append(away_label)

        away_team_data = TEAMS.get(self.team_list[self.away_team_index], {})
        self.away_team_text = Text(
            text=away_team_data.get('name', 'Unknown'),
            parent=camera.ui,
            position=(0.3, 0.24),
            scale=1.2,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(self.away_team_text)

        away_rating = Text(
            text=f"Rating: {away_team_data.get('rating', '?')} | {away_team_data.get('formation', '4-4-2')}",
            parent=camera.ui,
            position=(0.3, 0.18),
            scale=0.7,
            color=color.light_gray,
            origin=(0, 0),
        )
        self.elements.append(away_rating)
        self.away_rating_text = away_rating

        ac = away_team_data.get('home_color', (1, 1, 1))
        away_swatch = Entity(
            parent=camera.ui,
            model='quad',
            color=rgb(int(ac[0]*255), int(ac[1]*255), int(ac[2]*255)),
            scale=(0.06, 0.06),
            position=(0.3, 0.1),
        )
        self.elements.append(away_swatch)
        self.away_swatch = away_swatch

        away_left = Button(
            text='Prev',
            parent=camera.ui,
            scale=(0.1, 0.04),
            position=(0.12, 0.24),
            color=rgb(60, 60, 60),
            text_color=color.white,
            on_click=lambda: self._change_team('away', -1),
        )
        self.elements.append(away_left)

        away_right = Button(
            text='Next',
            parent=camera.ui,
            scale=(0.1, 0.04),
            position=(0.48, 0.24),
            color=rgb(60, 60, 60),
            text_color=color.white,
            on_click=lambda: self._change_team('away', 1),
        )
        self.elements.append(away_right)

        # Difficulty selector
        diff_label = Text(
            text='DIFFICULTY',
            parent=camera.ui,
            position=(0, -0.05),
            scale=0.9,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(diff_label)

        difficulties = ['amateur', 'semi_pro', 'professional', 'world_class', 'legendary']
        diff_names = ['Amateur', 'Semi-Pro', 'Professional', 'World Class', 'Legendary']
        self.diff_buttons = []

        for i, (diff, name) in enumerate(zip(difficulties, diff_names)):
            x_pos = -0.28 + i * 0.14
            is_selected = diff == self.selected_difficulty
            btn_color = rgb(50, 180, 50) if is_selected else rgb(60, 60, 60)

            btn = Button(
                text=name,
                parent=camera.ui,
                scale=(0.13, 0.04),
                position=(x_pos, -0.12),
                color=btn_color,
                text_color=color.white,
                on_click=lambda d=diff: self._select_difficulty(d),
            )
            btn.difficulty = diff
            self.elements.append(btn)
            self.diff_buttons.append(btn)

        # Player list preview
        self._build_player_list(-0.3, -0.2, self.team_list[self.home_team_index])
        self._build_player_list(0.3, -0.2, self.team_list[self.away_team_index])

        # Start & Back buttons
        start_btn = Button(
            text='START MATCH',
            parent=camera.ui,
            scale=(0.3, 0.06),
            position=(0, -0.4),
            color=rgb(30, 150, 30),
            highlight_color=rgb(50, 200, 50),
            text_color=color.white,
            on_click=self._on_start_match,
        )
        self.elements.append(start_btn)

        back_btn = Button(
            text='BACK',
            parent=camera.ui,
            scale=(0.15, 0.04),
            position=(-0.35, -0.43),
            color=rgb(100, 30, 30),
            text_color=color.white,
            on_click=self._build_main_menu,
        )
        self.elements.append(back_btn)

    def _build_player_list(self, x_center, y_start, team_id):
        """Build a player list preview for a team."""
        team_data = TEAMS.get(team_id, {})
        players = team_data.get('players', [])[:11]

        for i, p in enumerate(players):
            y = y_start - i * 0.028
            text_str = f"{p.get('number', '?'):>2}. {p.get('name', '?'):<14} {p.get('position', '?').value:>3} {p.get('rating', '?')}"
            pt = Text(
                text=text_str,
                parent=camera.ui,
                position=(x_center, y),
                scale=0.45,
                color=color.light_gray,
                origin=(0, 0),
                font='VeraMono.ttf',
            )
            self.elements.append(pt)

    def _change_team(self, side: str, direction: int):
        """Change selected team."""
        if side == 'home':
            self.home_team_index = (self.home_team_index + direction) % len(self.team_list)
            self.selected_home_team = self.team_list[self.home_team_index]
        else:
            self.away_team_index = (self.away_team_index + direction) % len(self.team_list)
            self.selected_away_team = self.team_list[self.away_team_index]

        # Rebuild team select to update display
        self._build_team_select()

    def _select_difficulty(self, difficulty: str):
        """Select difficulty level."""
        self.selected_difficulty = difficulty
        for btn in self.diff_buttons:
            if hasattr(btn, 'difficulty'):
                if btn.difficulty == difficulty:
                    btn.color = rgb(50, 180, 50)
                else:
                    btn.color = rgb(60, 60, 60)

    def _build_settings(self):
        """Build settings menu."""
        self._clear_elements()
        self.current_menu = 'settings'

        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(10, 10, 20, 240),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        title = Text(
            text='SETTINGS',
            parent=camera.ui,
            position=(0, 0.35),
            scale=2,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(title)

        # Settings options
        settings_text = [
            'Controls: WASD / Arrow Keys for movement',
            'Space: Pass (offense) / Switch Player (defense)',
            'Q: Shoot (offense) / Slide Tackle (defense)',
            'E: Through Ball (offense) / Press (defense)',
            'C: Cross | R: Lob Pass | F: Skill Move / Contain',
            'Shift: Sprint | Tab: Team Press',
            '1-4: Camera Modes | M: Minimap | V: Replay',
            'ESC: Pause',
            '',
            'Camera: Broadcast | Dynamic | End-to-End | Tactical',
        ]

        for i, line in enumerate(settings_text):
            t = Text(
                text=line,
                parent=camera.ui,
                position=(0, 0.2 - i * 0.05),
                scale=0.7,
                color=color.light_gray,
                origin=(0, 0),
            )
            self.elements.append(t)

        back_btn = Button(
            text='BACK',
            parent=camera.ui,
            scale=(0.2, 0.05),
            position=(0, -0.35),
            color=rgb(100, 30, 30),
            text_color=color.white,
            on_click=self._build_main_menu,
        )
        self.elements.append(back_btn)

    def build_pause_menu(self, match):
        """Build in-game pause menu."""
        self._clear_elements()
        self.current_menu = 'pause'

        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 0, 180),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        title = Text(
            text='PAUSED',
            parent=camera.ui,
            position=(0, 0.3),
            scale=2.5,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(title)

        # Score
        score = Text(
            text=f"{match.home_team.team_name}  {match.home_score} - {match.away_score}  {match.away_team.team_name}",
            parent=camera.ui,
            position=(0, 0.2),
            scale=1.2,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(score)

        # Stats
        home_poss, away_poss = match.get_possession_stats()
        stats_lines = [
            f"Possession: {home_poss:.0f}% - {away_poss:.0f}%",
            f"Shots: {sum(p.shots for p in match.home_team.players)} - {sum(p.shots for p in match.away_team.players)}",
            f"Fouls: {sum(p.fouls_committed for p in match.home_team.players)} - {sum(p.fouls_committed for p in match.away_team.players)}",
        ]
        for i, line in enumerate(stats_lines):
            t = Text(
                text=line,
                parent=camera.ui,
                position=(0, 0.1 - i * 0.05),
                scale=0.7,
                color=color.light_gray,
                origin=(0, 0),
            )
            self.elements.append(t)

        resume_btn = Button(
            text='RESUME',
            parent=camera.ui,
            scale=(0.3, 0.06),
            position=(0, -0.1),
            color=rgb(30, 120, 30),
            text_color=color.white,
            on_click=lambda: self._on_resume(match),
        )
        self.elements.append(resume_btn)

        quit_btn = Button(
            text='QUIT TO MENU',
            parent=camera.ui,
            scale=(0.3, 0.06),
            position=(0, -0.2),
            color=rgb(120, 30, 30),
            text_color=color.white,
            on_click=self._on_quit_to_menu,
        )
        self.elements.append(quit_btn)

    def build_fulltime_screen(self, match):
        """Build full-time results screen."""
        self._clear_elements()
        self.current_menu = 'fulltime'

        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 10, 220),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        title = Text(
            text='FULL TIME',
            parent=camera.ui,
            position=(0, 0.38),
            scale=2.5,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(title)

        # Final score
        score = Text(
            text=f"{match.home_team.team_name}",
            parent=camera.ui,
            position=(-0.2, 0.26),
            scale=1.2,
            color=color.white,
            origin=(0.5, 0),
        )
        self.elements.append(score)

        score_nums = Text(
            text=f"{match.home_score}  -  {match.away_score}",
            parent=camera.ui,
            position=(0, 0.26),
            scale=2.0,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(score_nums)

        away_name = Text(
            text=f"{match.away_team.team_name}",
            parent=camera.ui,
            position=(0.2, 0.26),
            scale=1.2,
            color=color.white,
            origin=(-0.5, 0),
        )
        self.elements.append(away_name)

        # Goal scorers
        y = 0.16
        for gs in match.goal_scorers:
            scorer = gs.get('scorer')
            name = scorer.name if scorer else 'OG'
            minute = gs.get('minute', 0)
            team = gs.get('team')
            x_pos = -0.15 if team == match.home_team else 0.15
            t = Text(
                text=f"{name} {minute}'",
                parent=camera.ui,
                position=(x_pos, y),
                scale=0.7,
                color=color.light_gray,
                origin=(0, 0),
            )
            self.elements.append(t)
            y -= 0.04

        # Stats
        stats = match.get_match_stats()
        stat_y = -0.05
        stat_labels = [
            ('Possession', 'possession', '%'),
            ('Shots', 'shots', ''),
            ('Passes', 'passes', ''),
            ('Tackles Won', 'tackles_won', ''),
            ('Fouls', 'fouls', ''),
            ('Yellow Cards', 'yellow_cards', ''),
            ('Corners', 'corners', ''),
        ]

        for label, key, suffix in stat_labels:
            home_val = stats['home'].get(key, 0)
            away_val = stats['away'].get(key, 0)
            if suffix == '%':
                stat_str = f"{home_val:.0f}%   {label}   {away_val:.0f}%"
            else:
                stat_str = f"{home_val}   {label}   {away_val}"
            t = Text(
                text=stat_str,
                parent=camera.ui,
                position=(0, stat_y),
                scale=0.6,
                color=color.light_gray,
                origin=(0, 0),
            )
            self.elements.append(t)
            stat_y -= 0.035

        # Buttons
        replay_btn = Button(
            text='PLAY AGAIN',
            parent=camera.ui,
            scale=(0.25, 0.05),
            position=(-0.15, -0.4),
            color=rgb(30, 120, 30),
            text_color=color.white,
            on_click=self._on_play_again,
        )
        self.elements.append(replay_btn)

        menu_btn = Button(
            text='MAIN MENU',
            parent=camera.ui,
            scale=(0.25, 0.05),
            position=(0.15, -0.4),
            color=rgb(100, 30, 30),
            text_color=color.white,
            on_click=self._on_quit_to_menu,
        )
        self.elements.append(menu_btn)

    def build_halftime_screen(self, match):
        """Build halftime screen."""
        self._clear_elements()
        self.current_menu = 'halftime'

        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=rgba(0, 0, 0, 200),
            scale=(2, 2),
            z=1,
        )
        self.elements.append(bg)

        title = Text(
            text='HALF TIME',
            parent=camera.ui,
            position=(0, 0.3),
            scale=2.5,
            color=color.white,
            origin=(0, 0),
        )
        self.elements.append(title)

        score = Text(
            text=f"{match.home_team.team_name}  {match.home_score} - {match.away_score}  {match.away_team.team_name}",
            parent=camera.ui,
            position=(0, 0.2),
            scale=1.2,
            color=color.yellow,
            origin=(0, 0),
        )
        self.elements.append(score)

        home_poss, away_poss = match.get_possession_stats()
        stats = Text(
            text=f"Possession: {home_poss:.0f}% - {away_poss:.0f}%",
            parent=camera.ui,
            position=(0, 0.1),
            scale=0.8,
            color=color.light_gray,
            origin=(0, 0),
        )
        self.elements.append(stats)

        info = Text(
            text='Second half starting soon...',
            parent=camera.ui,
            position=(0, -0.1),
            scale=0.7,
            color=color.light_gray,
            origin=(0, 0),
        )
        self.elements.append(info)

    # Callbacks
    def _on_quick_match(self):
        self.selected_home_team = 'real_madrid'
        self.selected_away_team = 'manchester_city'
        self._on_start_match()

    def _on_team_select(self):
        self._build_team_select()

    def _on_settings(self):
        self._build_settings()

    def _on_quit(self):
        if self.on_quit:
            self.on_quit()
        else:
            application.quit()

    def _on_start_match(self):
        self.selected_home_team = self.team_list[self.home_team_index]
        self.selected_away_team = self.team_list[self.away_team_index]
        if self.on_start_match:
            self.on_start_match(
                self.selected_home_team,
                self.selected_away_team,
                self.selected_difficulty,
            )
        self._clear_elements()
        self.is_visible = False

    def _on_resume(self, match):
        match.toggle_pause()
        self._clear_elements()
        self.is_visible = False

    def _on_quit_to_menu(self):
        if self.on_quit:
            self.on_quit()
        self._build_main_menu()
        self.is_visible = True

    def _on_play_again(self):
        self._build_team_select()

    def show(self):
        self.is_visible = True

    def hide(self):
        self._clear_elements()
        self.is_visible = False

    def cleanup(self):
        self._clear_elements()
