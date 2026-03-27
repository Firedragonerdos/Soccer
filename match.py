"""
Ultimate Soccer 3D - Match Manager
Match flow, game states, timer, scoring, halftime, and full match logic.
"""
import math
import random
from ursina import Vec3
from config import (
    GameState, SetPieceType, CardType, Position,
    MATCH_HALF_DURATION, MATCH_EXTRA_TIME_MAX, MATCH_HALFTIME_DURATION,
    MATCH_KICKOFF_DELAY, MATCH_GOAL_CELEBRATION_TIME,
    FIELD_HALF_LENGTH, FIELD_HALF_WIDTH, GOAL_WIDTH,
)
from utils import (
    vec3_distance_xz, format_time, format_match_time, clamp,
)
from player import PlayerState


class MatchEvent:
    """Represents a match event for replay/commentary."""
    def __init__(self, event_type: str, time: float, half: int, **kwargs):
        self.event_type = event_type
        self.time = time
        self.half = half
        self.data = kwargs
        self.match_minute = self._calc_minute(time, half)

    def _calc_minute(self, time, half):
        minute = int((time / MATCH_HALF_DURATION) * 45) + (45 if half > 1 else 0)
        return max(1, minute)


class Match:
    """Manages the full match flow."""

    def __init__(self, home_team, away_team, ball, field, referee,
                 physics_engine, difficulty='professional'):
        self.home_team = home_team
        self.away_team = away_team
        self.ball = ball
        self.field = field
        self.referee = referee
        self.physics = physics_engine
        self.difficulty = difficulty

        # Score
        self.home_score = 0
        self.away_score = 0

        # Match state
        self.state = GameState.MATCH_INTRO
        self.previous_state = GameState.MATCH_INTRO

        # Timer
        self.match_time = 0.0
        self.half = 1
        self.extra_time = 0.0
        self.added_time = 0.0
        self.is_extra_time = False
        self.stoppage_timer = 0.0

        # Flow control
        self.kickoff_team = home_team
        self.kickoff_delay = 0.0
        self.celebration_timer = 0.0
        self.halftime_timer = 0.0
        self.intro_timer = 0.0
        self.set_piece_timer = 0.0
        self.set_piece_delay = 2.0

        # Events
        self.events = []
        self.goal_scorers = []
        self.last_goal_scorer = None

        # Ball tracking
        self.ball_in_play = True
        self.last_ball_in_play_pos = Vec3(0, 0, 0)

        # All players reference
        self.all_players = home_team.players + away_team.players

        # Pause
        self.is_paused = False

        # Match end
        self.is_finished = False
        self.result = None  # 'home_win', 'away_win', 'draw'

    @property
    def match_minute(self) -> int:
        minute = int((self.match_time / MATCH_HALF_DURATION) * 45)
        if self.half > 1:
            minute += 45
        return max(1, minute)

    @property
    def match_time_str(self) -> str:
        return format_match_time(self.match_time, self.half)

    @property
    def score_str(self) -> str:
        return f"{self.home_score} - {self.away_score}"

    def start(self):
        """Start the match."""
        self.state = GameState.MATCH_INTRO
        self.intro_timer = 3.0

        # Randomize who kicks off
        if random.random() > 0.5:
            self.kickoff_team = self.home_team
        else:
            self.kickoff_team = self.away_team

        # Set positions
        has_kickoff_home = self.kickoff_team == self.home_team
        self.home_team.set_kickoff_positions(has_kickoff_home)
        self.away_team.set_kickoff_positions(not has_kickoff_home)

        # Place ball at center
        self.ball.reset(Vec3(0, 0.11, 0))
        self.ball.is_in_play = False

        self._add_event('match_start')

    def update(self, dt: float):
        """Main match update loop."""
        if self.is_paused or self.is_finished:
            return

        # State machine
        if self.state == GameState.MATCH_INTRO:
            self._update_intro(dt)
        elif self.state == GameState.MATCH_PLAYING:
            self._update_playing(dt)
        elif self.state == GameState.MATCH_GOAL:
            self._update_goal_celebration(dt)
        elif self.state == GameState.SET_PIECE:
            self._update_set_piece(dt)
        elif self.state == GameState.MATCH_HALFTIME:
            self._update_halftime(dt)
        elif self.state == GameState.MATCH_FULLTIME:
            self._update_fulltime(dt)

    def _update_intro(self, dt: float):
        """Match intro / pre-kickoff."""
        self.intro_timer -= dt
        if self.intro_timer <= 0:
            self._start_kickoff()

    def _start_kickoff(self):
        """Start a kickoff."""
        self.state = GameState.MATCH_PLAYING
        self.ball.is_in_play = True
        self.ball_in_play = True
        self.referee.clear_set_piece()

        # Give ball to kickoff team's striker
        kickoff_players = self.kickoff_team.players
        for p in kickoff_players:
            if p.role in [Position.ST, Position.CF] and not p.is_sent_off:
                # Move ball to center
                self.ball.reset(Vec3(0, 0.11, 0))
                break

    def _update_playing(self, dt: float):
        """Update during active play."""
        # Update match time
        self.match_time += dt

        # Check half time / full time
        total_time = MATCH_HALF_DURATION + self.added_time
        if self.match_time >= total_time:
            if self.half == 1:
                self._start_halftime()
                return
            else:
                self._start_fulltime()
                return

        # Calculate added time
        self.stoppage_timer += dt
        if self.match_time > MATCH_HALF_DURATION * 0.95:
            if not self.is_extra_time:
                self.added_time = random.uniform(15, 45)
                self.is_extra_time = True

        # Update physics
        self.physics.update(self.all_players, self.ball, dt)
        events = self.physics.process_ball_events(self.ball, self)

        # Process physics events
        for event in events:
            self._process_physics_event(event)

        # Update teams
        self.home_team.update(dt, self.ball, self.away_team, self)
        self.away_team.update(dt, self.ball, self.home_team, self)

        # Update ball
        self.ball.update(dt)

        # Update referee
        ref_events = self.referee.update(dt, self.ball, self.home_team, self.away_team, self)
        if ref_events:
            for event in ref_events:
                self._process_referee_event(event)

        # Check goals
        self._check_goal()

        # Check out of play
        self._check_out_of_play()

        # Track ball in play
        if self.ball.is_in_play:
            self.last_ball_in_play_pos = Vec3(
                self.ball.position.x, self.ball.position.y, self.ball.position.z
            )

    def _check_goal(self):
        """Check if a goal was scored."""
        if not self.ball.is_in_play:
            return

        goal_side = self.field.is_ball_in_goal(self.ball.position)
        if goal_side == 0:
            return

        # Determine which team scored
        if goal_side == 1:
            # Ball in right goal
            if self.home_team.attacking_direction > 0:
                scoring_team = self.home_team
                conceding_team = self.away_team
                self.home_score += 1
            else:
                scoring_team = self.away_team
                conceding_team = self.home_team
                self.away_score += 1
        else:
            # Ball in left goal
            if self.home_team.attacking_direction < 0:
                scoring_team = self.home_team
                conceding_team = self.away_team
                self.home_score += 1
            else:
                scoring_team = self.away_team
                conceding_team = self.home_team
                self.away_score += 1

        scoring_team.goals_scored += 1
        conceding_team.goals_conceded += 1

        # Find scorer
        scorer = self.ball.last_touched_by
        if scorer and scorer.team_id == scoring_team.team_id:
            scorer.goals += 1
            self.last_goal_scorer = scorer
        else:
            # Own goal
            scorer = self.ball.last_touched_by
            if scorer:
                self.last_goal_scorer = scorer

        self.goal_scorers.append({
            'scorer': scorer,
            'team': scoring_team,
            'minute': self.match_minute,
            'home_score': self.home_score,
            'away_score': self.away_score,
        })

        self._add_event('goal', scorer=scorer, team=scoring_team.team_id,
                        score=f"{self.home_score}-{self.away_score}")

        # Start celebration
        self.state = GameState.MATCH_GOAL
        self.celebration_timer = MATCH_GOAL_CELEBRATION_TIME
        self.ball.is_in_play = False
        scoring_team.celebrate_goal(scorer)

        # Other team kicks off after goal
        self.kickoff_team = conceding_team

    def _check_out_of_play(self):
        """Check if ball went out of play."""
        if not self.ball.is_in_play:
            return
        if not self.ball.out_of_bounds and self.ball.in_goal == 0:
            return

        result = self.referee.check_out_of_play(self.ball, self.home_team, self.away_team)
        if result.get('goal'):
            return  # Handled by _check_goal

        if result.get('restart'):
            self.ball.is_in_play = False
            self.ball_in_play = False
            self.state = GameState.SET_PIECE
            self.set_piece_timer = 0.0
            self._add_event('out_of_play', restart_type=str(result.get('type', '')))

    def _update_goal_celebration(self, dt: float):
        """Update goal celebration state."""
        self.celebration_timer -= dt

        # Update player celebrations
        for p in self.all_players:
            if p.state == PlayerState.CELEBRATING:
                p.update(dt)

        if self.celebration_timer <= 0:
            # Reset for kickoff
            has_kickoff_home = self.kickoff_team == self.home_team
            self.home_team.set_kickoff_positions(has_kickoff_home)
            self.away_team.set_kickoff_positions(not has_kickoff_home)
            self.ball.reset(Vec3(0, 0.11, 0))
            self.ball.is_in_play = False

            self.state = GameState.MATCH_INTRO
            self.intro_timer = MATCH_KICKOFF_DELAY

    def _update_set_piece(self, dt: float):
        """Update set piece state."""
        self.set_piece_timer += dt

        # Wait for players to get in position
        if self.set_piece_timer < self.set_piece_delay:
            # Move players to set piece positions
            sp_type = self.referee.current_set_piece
            sp_team = self.referee.set_piece_team
            sp_pos = self.referee.set_piece_position

            if sp_team:
                other_team = self.away_team if sp_team == self.home_team else self.home_team

                if sp_type == SetPieceType.CORNER_KICK:
                    sp_team.set_piece_positions('corner_kick_attack', True, sp_pos)
                    other_team.set_piece_positions('corner_kick_defend', False, sp_pos)
                elif sp_type == SetPieceType.FREE_KICK:
                    sp_team.set_piece_positions('free_kick_attack', True, sp_pos)
                elif sp_type == SetPieceType.GOAL_KICK:
                    sp_team.set_piece_positions('goal_kick', True, sp_pos)
                elif sp_type == SetPieceType.THROW_IN:
                    sp_team.set_piece_positions('throw_in', True, sp_pos)

            # Place ball
            self.ball.reset(self.referee.set_piece_position)

            # Keep human control on the closest eligible taker at restarts.
            if sp_team and sp_team.is_human:
                sp_team.select_nearest_to_ball(self.ball)

            # Update players moving to position
            self.home_team.update(dt, self.ball, self.away_team, self)
            self.away_team.update(dt, self.ball, self.home_team, self)
            return

        # Execute set piece
        if not self.referee.set_piece_ready:
            self.referee.execute_set_piece(self.ball)

        # AI takes the set piece
        if self.referee.set_piece_team and not self.referee.set_piece_team.is_human:
            self._ai_take_set_piece()
        elif self.referee.set_piece_team and self.referee.set_piece_team.is_human:
            # Wait for human to take it
            if self.ball.speed > 1.0 or self.ball.frames_since_touch < 5:
                self._resume_play()

        # Check if ball has been played
        if self.ball.speed > 1.0 and self.set_piece_timer > self.set_piece_delay + 0.5:
            self._resume_play()

        # Timeout - auto take
        if self.set_piece_timer > self.set_piece_delay + 8.0:
            self._ai_take_set_piece()

    def _ai_take_set_piece(self):
        """AI takes a set piece."""
        sp_type = self.referee.current_set_piece
        sp_team = self.referee.set_piece_team
        sp_pos = self.referee.set_piece_position

        if not sp_team:
            self._resume_play()
            return

        # Find nearest player to ball
        nearest = None
        nearest_dist = float('inf')
        for p in sp_team.players:
            if p.is_goalkeeper and sp_type != SetPieceType.GOAL_KICK:
                continue
            if p.is_sent_off:
                continue
            d = vec3_distance_xz(p.position, sp_pos)
            if d < nearest_dist:
                nearest = p
                nearest_dist = d

        if not nearest:
            self._resume_play()
            return

        atk_dir = sp_team.attacking_direction

        if sp_type == SetPieceType.GOAL_KICK:
            if sp_team.goalkeeper:
                sp_team.goalkeeper.has_ball = True
                from goalkeeper import GoalkeeperAI
                if sp_team.gk_ai:
                    sp_team.gk_ai.on_goal_kick(self.ball, sp_team.players)
                else:
                    target = Vec3(atk_dir * 30, 0, random.uniform(-15, 15))
                    nearest.initiate_pass(target, self.ball, 0.8, is_lob=True)

        elif sp_type == SetPieceType.CORNER_KICK:
            # Cross into box
            target = Vec3(
                atk_dir * (FIELD_HALF_LENGTH - 10),
                0,
                random.uniform(-5, 5)
            )
            nearest.initiate_cross(target, self.ball, random.uniform(0.5, 0.8))

        elif sp_type == SetPieceType.FREE_KICK:
            dist_to_goal = abs(sp_pos.x - atk_dir * FIELD_HALF_LENGTH)
            if dist_to_goal < 25 and abs(sp_pos.z) < 20:
                # Shoot at goal
                goal_target = Vec3(
                    atk_dir * FIELD_HALF_LENGTH,
                    random.uniform(0.5, 2.0),
                    random.uniform(-3, 3)
                )
                nearest.initiate_shot(goal_target, self.ball, random.uniform(0.6, 0.9))
            else:
                # Pass to teammate
                from utils import get_best_pass_target
                other_team = self.away_team if sp_team == self.home_team else self.home_team
                target = get_best_pass_target(nearest, sp_team.players, other_team.players, sp_pos)
                if target:
                    nearest.initiate_pass(target.position, self.ball, 0.6)
                else:
                    target_pos = Vec3(atk_dir * 20 + sp_pos.x, 0, random.uniform(-10, 10))
                    nearest.initiate_pass(target_pos, self.ball, 0.7, is_lob=True)

        elif sp_type == SetPieceType.THROW_IN:
            from utils import get_best_pass_target
            other_team = self.away_team if sp_team == self.home_team else self.home_team
            target = get_best_pass_target(nearest, sp_team.players, other_team.players, sp_pos)
            if target:
                nearest.initiate_pass(target.position, self.ball, 0.4)
            else:
                nearest.initiate_pass(
                    Vec3(sp_pos.x + atk_dir * 5, 0, 0), self.ball, 0.3
                )

        elif sp_type == SetPieceType.PENALTY:
            goal_target = Vec3(
                atk_dir * FIELD_HALF_LENGTH,
                random.uniform(0.3, 1.8),
                random.uniform(-2.5, 2.5)
            )
            nearest.initiate_shot(goal_target, self.ball, random.uniform(0.7, 0.95))
            # GK reacts
            other_team = self.away_team if sp_team == self.home_team else self.home_team
            if other_team.gk_ai:
                other_team.gk_ai.on_penalty_save(self.ball)

        self._resume_play()

    def _resume_play(self):
        """Resume normal play after set piece."""
        self.state = GameState.MATCH_PLAYING
        self.referee.clear_set_piece()
        self.ball.is_in_play = True
        self.ball_in_play = True
        self.ball.out_of_bounds = False
        self.ball.in_goal = 0

    def _start_halftime(self):
        """Start halftime."""
        self.state = GameState.MATCH_HALFTIME
        self.halftime_timer = MATCH_HALFTIME_DURATION
        self.ball.is_in_play = False
        self._add_event('halftime')

    def _update_halftime(self, dt: float):
        """Update halftime state."""
        self.halftime_timer -= dt
        if self.halftime_timer <= 0:
            self._start_second_half()

    def _start_second_half(self):
        """Start the second half."""
        self.half = 2
        self.match_time = 0.0
        self.is_extra_time = False
        self.added_time = 0.0

        # Switch sides
        self.home_team.attacking_direction *= -1
        self.away_team.attacking_direction *= -1

        for p in self.home_team.players:
            p.attacking_direction = self.home_team.attacking_direction
        for p in self.away_team.players:
            p.attacking_direction = self.away_team.attacking_direction

        if self.home_team.gk_ai:
            self.home_team.gk_ai.setup(self.home_team.attacking_direction)
        if self.away_team.gk_ai:
            self.away_team.gk_ai.setup(self.away_team.attacking_direction)

        # Other team kicks off
        self.kickoff_team = self.away_team if self.kickoff_team == self.home_team else self.home_team

        has_kickoff_home = self.kickoff_team == self.home_team
        self.home_team.set_kickoff_positions(has_kickoff_home)
        self.away_team.set_kickoff_positions(not has_kickoff_home)
        self.ball.reset(Vec3(0, 0.11, 0))

        self.state = GameState.MATCH_INTRO
        self.intro_timer = MATCH_KICKOFF_DELAY
        self._add_event('second_half_start')

    def _start_fulltime(self):
        """End the match."""
        self.state = GameState.MATCH_FULLTIME
        self.is_finished = True
        self.ball.is_in_play = False

        if self.home_score > self.away_score:
            self.result = 'home_win'
        elif self.away_score > self.home_score:
            self.result = 'away_win'
        else:
            self.result = 'draw'

        self._add_event('fulltime', result=self.result,
                        score=f"{self.home_score}-{self.away_score}")

    def _update_fulltime(self, dt: float):
        """Update fulltime state."""
        pass  # Wait for user input

    def _process_physics_event(self, event: dict):
        """Process a physics event."""
        if event['type'] == 'foul':
            offender = event['player']
            victim = event['victim']
            severity = event['severity']
            position = event['position']

            offender_team = self.home_team if offender.team_id == self.home_team.team_id else self.away_team
            victim_team = self.away_team if offender_team == self.home_team else self.home_team

            result = self.referee.process_foul(
                offender, victim, severity, position,
                self.ball, victim_team, offender_team
            )

            if result['type'] == 'foul':
                self._add_event('foul', offender=offender.name, victim=victim.name,
                               card=str(result.get('card', '')))
                if result.get('is_penalty'):
                    self._add_event('penalty', team=victim_team.team_id)

                # Stop play
                self.ball.is_in_play = False
                self.state = GameState.SET_PIECE
                self.set_piece_timer = 0.0

            elif result['type'] == 'advantage':
                self._add_event('advantage', team=victim_team.team_id)

        elif event['type'] == 'tackle_won':
            self._add_event('tackle', player=event['player'].name)

        elif event['type'] == 'gk_catch':
            self._add_event('save', player=event['player'].name)

        elif event['type'] == 'gk_parry':
            self._add_event('parry', player=event['player'].name)

    def _process_referee_event(self, event: dict):
        """Process a referee event."""
        if event.get('type') == 'offside':
            offside = event['event']
            self._add_event('offside', player=offside.player.name)
            self.ball.is_in_play = False
            self.state = GameState.SET_PIECE
            self.set_piece_timer = 0.0

    def _add_event(self, event_type: str, **kwargs):
        """Add a match event."""
        event = MatchEvent(event_type, self.match_time, self.half, **kwargs)
        self.events.append(event)

    def toggle_pause(self):
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def get_possession_stats(self) -> tuple:
        """Get possession percentages."""
        total = self.home_team.possession_time + self.away_team.possession_time
        if total < 0.1:
            return 50.0, 50.0
        home_pct = (self.home_team.possession_time / total) * 100
        away_pct = 100 - home_pct
        return round(home_pct, 1), round(away_pct, 1)

    def get_match_stats(self) -> dict:
        """Get full match statistics."""
        home_stats = self.home_team.get_stats()
        away_stats = self.away_team.get_stats()
        home_poss, away_poss = self.get_possession_stats()

        return {
            'home': {**home_stats, 'possession': home_poss},
            'away': {**away_stats, 'possession': away_poss},
        }

    def cleanup(self):
        """Clean up match resources."""
        self.home_team.cleanup()
        self.away_team.cleanup()
        self.ball.cleanup()
        self.field.cleanup()
