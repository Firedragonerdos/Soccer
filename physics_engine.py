"""
Ultimate Soccer 3D - Physics Engine
Collision detection, resolution, and physical interactions between entities.
"""
import math
import random
from ursina import Vec3
from config import (
    PLAYER_RADIUS, PLAYER_HEIGHT, BALL_RADIUS, PLAYER_MASS, BALL_MASS,
    DRIBBLE_TOUCH_DISTANCE, DRIBBLE_CLOSE_CONTROL, DRIBBLE_LOSE_BALL_BASE_CHANCE,
    TACKLE_RANGE, TACKLE_SLIDE_RANGE, TACKLE_STANDING_RANGE,
    GK_CATCH_RANGE, GK_PUNCH_RANGE, GK_PARRY_RANGE,
    GOAL_WIDTH, GOAL_HEIGHT, FIELD_HALF_LENGTH, FIELD_HALF_WIDTH
)
from utils import (
    vec3_distance_xz, vec3_normalize, vec3_normalize_xz, vec3_length_xz,
    vec3_dot, vec3_reflect, clamp, probability_check, attr_to_multiplier
)
from player import PlayerState


class PhysicsEngine:
    """Handles all physics interactions in the game."""

    def __init__(self):
        self.collision_pairs = []
        self.ball_player_events = []

    def update(self, players: list, ball, dt: float):
        """Run physics update for all entities."""
        self.collision_pairs.clear()
        self.ball_player_events.clear()

        # Player-player collisions
        self._resolve_player_collisions(players, dt)

        # Ball-player interactions
        self._resolve_ball_player(players, ball, dt)

        # Ball dribbling control
        self._update_dribble_control(players, ball, dt)

    def _resolve_player_collisions(self, players: list, dt: float):
        """Resolve collisions between players."""
        for i in range(len(players)):
            if players[i].is_sent_off:
                continue
            for j in range(i + 1, len(players)):
                if players[j].is_sent_off:
                    continue

                p1 = players[i]
                p2 = players[j]
                dist = vec3_distance_xz(p1.position, p2.position)
                min_dist = PLAYER_RADIUS * 2

                if dist < min_dist and dist > 0.01:
                    # Resolve overlap
                    overlap = min_dist - dist
                    direction = vec3_normalize_xz(Vec3(
                        p2.position.x - p1.position.x, 0,
                        p2.position.z - p1.position.z
                    ))

                    # Weight by strength
                    str1 = p1.get_attr(p1.attributes.get(None, 50)) if False else 70
                    str2 = p2.get_attr(p2.attributes.get(None, 50)) if False else 70

                    from config import PlayerAttribute
                    str1 = p1.get_attr(PlayerAttribute.STRENGTH)
                    str2 = p2.get_attr(PlayerAttribute.STRENGTH)

                    total_str = max(str1 + str2, 1)
                    ratio1 = str2 / total_str
                    ratio2 = str1 / total_str

                    # Sliding/tackling players push harder
                    if p1.state == PlayerState.SLIDE_TACKLING:
                        ratio1 *= 0.3
                        ratio2 *= 1.7
                    if p2.state == PlayerState.SLIDE_TACKLING:
                        ratio1 *= 1.7
                        ratio2 *= 0.3

                    # Apply separation
                    p1.position = Vec3(
                        p1.position.x - direction.x * overlap * ratio1,
                        0,
                        p1.position.z - direction.z * overlap * ratio1
                    )
                    p2.position = Vec3(
                        p2.position.x + direction.x * overlap * ratio2,
                        0,
                        p2.position.z + direction.z * overlap * ratio2
                    )

                    # Velocity transfer (simplified)
                    bounce_factor = 0.3
                    v1_along = vec3_dot(Vec3(p1.velocity.x, 0, p1.velocity.z),
                                         Vec3(direction.x, 0, direction.z))
                    v2_along = vec3_dot(Vec3(p2.velocity.x, 0, p2.velocity.z),
                                         Vec3(direction.x, 0, direction.z))

                    if v1_along > v2_along:
                        impulse = (v1_along - v2_along) * bounce_factor
                        p1.velocity = Vec3(
                            p1.velocity.x - direction.x * impulse * ratio1,
                            0,
                            p1.velocity.z - direction.z * impulse * ratio1
                        )
                        p2.velocity = Vec3(
                            p2.velocity.x + direction.x * impulse * ratio2,
                            0,
                            p2.velocity.z + direction.z * impulse * ratio2
                        )

                    self.collision_pairs.append((p1, p2, dist))

    def _resolve_ball_player(self, players: list, ball, dt: float):
        """Handle ball-player interactions."""
        if ball.is_held:
            return

        for player in players:
            if player.is_sent_off:
                continue

            dist = vec3_distance_xz(player.position, ball.position)
            height_diff = abs(ball.position.y - (player.jump_height + PLAYER_HEIGHT * 0.5))

            # Check if player can interact with ball
            can_touch = dist < PLAYER_RADIUS + BALL_RADIUS + 0.3

            # Goalkeeper catching/punching
            if player.is_goalkeeper and player.state == PlayerState.GK_DIVING:
                dive_reach = GK_CATCH_RANGE + BALL_RADIUS
                if dist < dive_reach and height_diff < 2.5:
                    event = {
                        'type': 'gk_save',
                        'player': player,
                        'distance': dist,
                        'ball_speed': ball.speed,
                    }
                    self.ball_player_events.append(event)
                    continue

            # Standing GK catch
            if (player.is_goalkeeper and can_touch and
                ball.position.y < PLAYER_HEIGHT + player.jump_height + 0.5):
                if ball.shot_active or ball.cross_active:
                    event = {
                        'type': 'gk_save',
                        'player': player,
                        'distance': dist,
                        'ball_speed': ball.speed,
                    }
                    self.ball_player_events.append(event)
                    continue

            # Tackle interaction
            if player.state in [PlayerState.TACKLING, PlayerState.SLIDE_TACKLING]:
                tackle_range = TACKLE_SLIDE_RANGE if player.state == PlayerState.SLIDE_TACKLING else TACKLE_STANDING_RANGE
                if dist < tackle_range + BALL_RADIUS:
                    event = {
                        'type': 'tackle',
                        'player': player,
                        'distance': dist,
                    }
                    self.ball_player_events.append(event)
                    # Also allow tackling player to pick up loose ball directly
                    if not any(p.has_ball for p in [pl for pl in players if not pl.is_sent_off]):
                        event_ctrl = {
                            'type': 'ball_control',
                            'player': player,
                            'distance': dist,
                        }
                        self.ball_player_events.append(event_ctrl)
                    continue

            # Normal ball pickup / control
            if can_touch and not ball.is_held:
                # Header opportunity
                if (ball.position.y > PLAYER_HEIGHT * 0.7 and
                    ball.position.y < PLAYER_HEIGHT * 1.5 + player.jump_height and
                    not ball.is_on_ground):
                    event = {
                        'type': 'header_opportunity',
                        'player': player,
                        'distance': dist,
                        'ball_height': ball.position.y,
                    }
                    self.ball_player_events.append(event)

                # Ball control / pickup
                elif ball.position.y < PLAYER_HEIGHT * 0.8:
                    event = {
                        'type': 'ball_control',
                        'player': player,
                        'distance': dist,
                    }
                    self.ball_player_events.append(event)

            # Ball hitting player body (deflection)
            if (dist < PLAYER_RADIUS + BALL_RADIUS and
                ball.speed > 5.0 and not can_touch and
                not player.has_ball):
                direction = vec3_normalize_xz(Vec3(
                    ball.position.x - player.position.x, 0,
                    ball.position.z - player.position.z
                ))
                ball.deflect(direction, 0.5)

    def _update_dribble_control(self, players: list, ball, dt: float):
        """Update ball position for dribbling players."""
        for player in players:
            if not player.has_ball or player.is_sent_off:
                continue

            if ball.is_held:
                continue

            # Keep ball near player while dribbling
            speed = vec3_length_xz(player.velocity)
            dribble_attr = player.get_attr(
                __import__('config', fromlist=['PlayerAttribute']).PlayerAttribute.BALL_CONTROL
            )
            control = attr_to_multiplier(dribble_attr)

            # Touch distance based on speed and control
            if speed > 5.0:
                touch_dist = DRIBBLE_TOUCH_DISTANCE * (1.0 + (1.0 - control) * 0.5)
            else:
                touch_dist = DRIBBLE_CLOSE_CONTROL

            # Ball follows player
            target_ball_x = player.position.x + player.facing_direction.x * touch_dist
            target_ball_z = player.position.z + player.facing_direction.z * touch_dist

            # Smooth ball follow
            lerp_speed = 8.0 * control
            ball.position = Vec3(
                ball.position.x + (target_ball_x - ball.position.x) * min(1, lerp_speed * dt),
                BALL_RADIUS,
                ball.position.z + (target_ball_z - ball.position.z) * min(1, lerp_speed * dt)
            )
            ball.velocity = Vec3(player.velocity.x, 0, player.velocity.z)
            ball.last_touched_by = player
            ball.last_touched_team = player.team_id
            ball.frames_since_touch = 0

            # Random touch animation
            if speed > 3.0:
                player.dribble_timer += dt
                if player.dribble_timer > 0.3:
                    player.dribble_timer = 0
                    # Small random touch offset
                    offset_x = random.uniform(-0.1, 0.1) * (1.0 - control)
                    offset_z = random.uniform(-0.1, 0.1) * (1.0 - control)
                    ball.position = Vec3(
                        ball.position.x + offset_x,
                        BALL_RADIUS,
                        ball.position.z + offset_z
                    )

            # Check if ball is lost due to poor control at high speed
            if speed > 7.0:
                lose_chance = DRIBBLE_LOSE_BALL_BASE_CHANCE * (1.0 - control * 0.8) * (speed / 10.0)
                if probability_check(lose_chance):
                    player.has_ball = False
                    # Ball goes slightly ahead
                    ball.velocity = Vec3(
                        player.velocity.x * 1.3 + random.uniform(-2, 2),
                        0,
                        player.velocity.z * 1.3 + random.uniform(-2, 2)
                    )

    def process_ball_events(self, ball, match_state) -> list:
        """Process accumulated ball-player events. Returns list of events for referee/match."""
        results = []

        # Sort by distance (closest first)
        self.ball_player_events.sort(key=lambda e: e['distance'])

        ball_claimed = False

        for event in self.ball_player_events:
            if ball_claimed and event['type'] in ['ball_control', 'gk_save']:
                continue

            if event['type'] == 'ball_control':
                player = event['player']
                # Don't pick up if someone already has it
                if any(p.has_ball for p in self._get_all_players(match_state)):
                    # Steal from current holder
                    current_holder = next((p for p in self._get_all_players(match_state)
                                          if p.has_ball), None)
                    if current_holder and current_holder.team_id != player.team_id:
                        # Contested ball
                        from config import PlayerAttribute
                        control1 = player.get_attr(PlayerAttribute.BALL_CONTROL)
                        control2 = current_holder.get_attr(PlayerAttribute.BALL_CONTROL)
                        if random.random() < control1 / (control1 + control2):
                            current_holder.has_ball = False
                            player.has_ball = True
                            ball.last_touched_by = player
                            ball.last_touched_team = player.team_id
                            ball_claimed = True
                            results.append({
                                'type': 'ball_won',
                                'player': player,
                                'from_player': current_holder,
                            })
                    continue

                player.has_ball = True
                ball.last_touched_by = player
                ball.last_touched_team = player.team_id
                ball.owner = player
                ball.shot_active = False
                ball.pass_active = False
                ball.cross_active = False
                ball_claimed = True
                results.append({
                    'type': 'ball_control',
                    'player': player,
                })

            elif event['type'] == 'gk_save':
                player = event['player']
                caught = player.gk_catch(ball)
                if caught:
                    ball_claimed = True
                    results.append({
                        'type': 'gk_catch',
                        'player': player,
                        'ball_speed': event['ball_speed'],
                    })
                else:
                    results.append({
                        'type': 'gk_parry',
                        'player': player,
                        'ball_speed': event['ball_speed'],
                    })

            elif event['type'] == 'tackle':
                player = event['player']
                # Find ball holder
                holder = next((p for p in self._get_all_players(match_state)
                              if p.has_ball and p.team_id != player.team_id), None)
                if holder:
                    success, is_foul, severity = player.check_tackle_success(holder)
                    if success:
                        holder.has_ball = False
                        player.has_ball = True
                        player.tackles_won += 1
                        ball.last_touched_by = player
                        ball.last_touched_team = player.team_id
                        ball_claimed = True
                        results.append({
                            'type': 'tackle_won',
                            'player': player,
                            'victim': holder,
                        })
                    elif is_foul:
                        player.fouls_committed += 1
                        results.append({
                            'type': 'foul',
                            'player': player,
                            'victim': holder,
                            'severity': severity,
                            'position': Vec3(holder.position.x, 0, holder.position.z),
                        })
                    else:
                        results.append({
                            'type': 'tackle_missed',
                            'player': player,
                        })

            elif event['type'] == 'header_opportunity':
                results.append({
                    'type': 'header_opportunity',
                    'player': event['player'],
                    'ball_height': event['ball_height'],
                })

        return results

    def _get_all_players(self, match_state):
        """Get all players from match state."""
        if match_state and hasattr(match_state, 'all_players'):
            return match_state.all_players
        return []

    def check_goal(self, ball) -> int:
        """Check if ball crossed goal line into goal."""
        if ball.position.y <= GOAL_HEIGHT + 0.5:
            if abs(ball.position.z) <= GOAL_WIDTH / 2 + 0.2:
                if ball.position.x >= FIELD_HALF_LENGTH + 0.3:
                    return 1  # Goal on right side
                elif ball.position.x <= -(FIELD_HALF_LENGTH + 0.3):
                    return -1  # Goal on left side
        return 0

    def check_out_of_bounds(self, ball) -> dict:
        """Check if ball went out of play."""
        result = {'out': False, 'type': '', 'side_x': 0, 'side_z': 0}

        if abs(ball.position.z) > FIELD_HALF_WIDTH + 1.0:
            result['out'] = True
            result['type'] = 'throw_in'
            result['side_z'] = 1 if ball.position.z > 0 else -1
            result['position'] = Vec3(
                clamp(ball.position.x, -FIELD_HALF_LENGTH, FIELD_HALF_LENGTH),
                0,
                result['side_z'] * FIELD_HALF_WIDTH
            )
            return result

        if abs(ball.position.x) > FIELD_HALF_LENGTH + 1.5:
            result['out'] = True
            result['side_x'] = 1 if ball.position.x > 0 else -1

            if abs(ball.position.z) <= GOAL_WIDTH / 2 and ball.position.y <= GOAL_HEIGHT:
                result['type'] = 'goal'
            else:
                last_team = ball.last_touched_team
                if last_team:
                    result['type'] = 'corner_or_goal_kick'
                else:
                    result['type'] = 'goal_kick'

                result['position'] = Vec3(
                    result['side_x'] * FIELD_HALF_LENGTH,
                    0,
                    clamp(ball.position.z, -FIELD_HALF_WIDTH, FIELD_HALF_WIDTH)
                )
            return result

        return result

    def resolve_player_ball_proximity(self, players: list, ball) -> 'Player':
        """Find the player closest to the ball who can control it."""
        closest = None
        closest_dist = float('inf')

        for player in players:
            if player.is_sent_off:
                continue
            dist = vec3_distance_xz(player.position, ball.position)
            if dist < closest_dist:
                closest_dist = dist
                closest = player

        return closest

    def get_contested_ball_players(self, players: list, ball, radius: float = 3.0) -> list:
        """Get all players within contesting distance of the ball."""
        result = []
        for player in players:
            if player.is_sent_off:
                continue
            dist = vec3_distance_xz(player.position, ball.position)
            if dist < radius:
                result.append((player, dist))
        result.sort(key=lambda x: x[1])
        return result
