"""
Ultimate Soccer 3D - Utility Functions
Vector math, geometry helpers, and general utilities.
"""
import math
import random
from typing import Tuple, List, Optional
from ursina import Vec3, Vec2

# =============================================================================
# VECTOR MATH
# =============================================================================

def vec3_length(v: Vec3) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)

def vec3_length_xz(v: Vec3) -> float:
    return math.sqrt(v.x * v.x + v.z * v.z)

def vec3_normalize(v: Vec3) -> Vec3:
    length = vec3_length(v)
    if length < 0.0001:
        return Vec3(0, 0, 0)
    return Vec3(v.x / length, v.y / length, v.z / length)

def vec3_normalize_xz(v: Vec3) -> Vec3:
    length = vec3_length_xz(v)
    if length < 0.0001:
        return Vec3(0, 0, 0)
    return Vec3(v.x / length, 0, v.z / length)

def vec3_distance(a: Vec3, b: Vec3) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)

def vec3_distance_xz(a: Vec3, b: Vec3) -> float:
    dx = a.x - b.x
    dz = a.z - b.z
    return math.sqrt(dx * dx + dz * dz)

def vec3_dot(a: Vec3, b: Vec3) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z

def vec3_cross(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    )

def vec3_lerp(a: Vec3, b: Vec3, t: float) -> Vec3:
    t = max(0.0, min(1.0, t))
    return Vec3(
        a.x + (b.x - a.x) * t,
        a.y + (b.y - a.y) * t,
        a.z + (b.z - a.z) * t
    )

def vec3_slerp(a: Vec3, b: Vec3, t: float) -> Vec3:
    dot = vec3_dot(vec3_normalize(a), vec3_normalize(b))
    dot = max(-1.0, min(1.0, dot))
    theta = math.acos(dot) * t
    relative = vec3_normalize(Vec3(b.x - a.x * dot, b.y - a.y * dot, b.z - a.z * dot))
    la = vec3_length(a)
    lb = vec3_length(b)
    length = la + (lb - la) * t
    return Vec3(
        (a.x * math.cos(theta) + relative.x * math.sin(theta)) * length / max(la, 0.001),
        (a.y * math.cos(theta) + relative.y * math.sin(theta)) * length / max(la, 0.001),
        (a.z * math.cos(theta) + relative.z * math.sin(theta)) * length / max(la, 0.001),
    )

def vec3_reflect(v: Vec3, normal: Vec3) -> Vec3:
    d = 2.0 * vec3_dot(v, normal)
    return Vec3(v.x - d * normal.x, v.y - d * normal.y, v.z - d * normal.z)

def vec3_project(v: Vec3, onto: Vec3) -> Vec3:
    d = vec3_dot(onto, onto)
    if d < 0.0001:
        return Vec3(0, 0, 0)
    scalar = vec3_dot(v, onto) / d
    return Vec3(onto.x * scalar, onto.y * scalar, onto.z * scalar)

def vec3_rotate_y(v: Vec3, angle_rad: float) -> Vec3:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return Vec3(
        v.x * cos_a + v.z * sin_a,
        v.y,
        -v.x * sin_a + v.z * cos_a
    )

def vec3_angle_between(a: Vec3, b: Vec3) -> float:
    la = vec3_length(a)
    lb = vec3_length(b)
    if la < 0.0001 or lb < 0.0001:
        return 0.0
    dot = vec3_dot(a, b) / (la * lb)
    dot = max(-1.0, min(1.0, dot))
    return math.acos(dot)

def vec3_angle_xz(v: Vec3) -> float:
    return math.atan2(v.x, v.z)

def vec3_from_angle_xz(angle_rad: float, magnitude: float = 1.0) -> Vec3:
    return Vec3(
        math.sin(angle_rad) * magnitude,
        0,
        math.cos(angle_rad) * magnitude
    )

def vec3_clamp_length(v: Vec3, max_length: float) -> Vec3:
    length = vec3_length(v)
    if length > max_length and length > 0.0001:
        scale = max_length / length
        return Vec3(v.x * scale, v.y * scale, v.z * scale)
    return v

def vec3_move_towards(current: Vec3, target: Vec3, max_delta: float) -> Vec3:
    diff = Vec3(target.x - current.x, target.y - current.y, target.z - current.z)
    dist = vec3_length(diff)
    if dist <= max_delta or dist < 0.0001:
        return target
    normalized = Vec3(diff.x / dist, diff.y / dist, diff.z / dist)
    return Vec3(
        current.x + normalized.x * max_delta,
        current.y + normalized.y * max_delta,
        current.z + normalized.z * max_delta
    )

def vec3_smooth_damp(current: Vec3, target: Vec3, current_velocity: Vec3,
                     smooth_time: float, dt: float, max_speed: float = float('inf')) -> Tuple[Vec3, Vec3]:
    smooth_time = max(0.0001, smooth_time)
    omega = 2.0 / smooth_time
    x = omega * dt
    exp_factor = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)

    diff = Vec3(current.x - target.x, current.y - target.y, current.z - target.z)
    max_dist = max_speed * smooth_time
    diff = vec3_clamp_length(diff, max_dist)
    adjusted_target = Vec3(current.x - diff.x, current.y - diff.y, current.z - diff.z)

    temp = Vec3(
        (current_velocity.x + omega * diff.x) * dt,
        (current_velocity.y + omega * diff.y) * dt,
        (current_velocity.z + omega * diff.z) * dt
    )

    new_velocity = Vec3(
        (current_velocity.x - omega * temp.x) * exp_factor,
        (current_velocity.y - omega * temp.y) * exp_factor,
        (current_velocity.z - omega * temp.z) * exp_factor
    )

    new_pos = Vec3(
        adjusted_target.x + (diff.x + temp.x) * exp_factor,
        adjusted_target.y + (diff.y + temp.y) * exp_factor,
        adjusted_target.z + (diff.z + temp.z) * exp_factor
    )

    return new_pos, new_velocity

# =============================================================================
# GEOMETRY HELPERS
# =============================================================================

def point_in_rect(point: Vec3, rect_center: Vec3, rect_half_width: float, rect_half_length: float) -> bool:
    return (abs(point.x - rect_center.x) <= rect_half_length and
            abs(point.z - rect_center.z) <= rect_half_width)

def point_in_circle(point: Vec3, center: Vec3, radius: float) -> bool:
    return vec3_distance_xz(point, center) <= radius

def point_in_field(point: Vec3, margin: float = 0.0) -> bool:
    from config import FIELD_HALF_LENGTH, FIELD_HALF_WIDTH
    return (abs(point.x) <= FIELD_HALF_LENGTH + margin and
            abs(point.z) <= FIELD_HALF_WIDTH + margin)

def point_in_penalty_area(point: Vec3, side: int) -> bool:
    from config import FIELD_HALF_LENGTH, PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH
    if side > 0:
        return (point.x >= FIELD_HALF_LENGTH - PENALTY_AREA_LENGTH and
                point.x <= FIELD_HALF_LENGTH and
                abs(point.z) <= PENALTY_AREA_WIDTH / 2.0)
    else:
        return (point.x <= -FIELD_HALF_LENGTH + PENALTY_AREA_LENGTH and
                point.x >= -FIELD_HALF_LENGTH and
                abs(point.z) <= PENALTY_AREA_WIDTH / 2.0)

def point_in_goal_area(point: Vec3, side: int) -> bool:
    from config import FIELD_HALF_LENGTH, GOAL_AREA_LENGTH, GOAL_AREA_WIDTH
    if side > 0:
        return (point.x >= FIELD_HALF_LENGTH - GOAL_AREA_LENGTH and
                point.x <= FIELD_HALF_LENGTH and
                abs(point.z) <= GOAL_AREA_WIDTH / 2.0)
    else:
        return (point.x <= -FIELD_HALF_LENGTH + GOAL_AREA_LENGTH and
                point.x >= -FIELD_HALF_LENGTH and
                abs(point.z) <= GOAL_AREA_WIDTH / 2.0)

def line_circle_intersection(line_start: Vec3, line_end: Vec3,
                              circle_center: Vec3, radius: float) -> bool:
    dx = line_end.x - line_start.x
    dz = line_end.z - line_start.z
    fx = line_start.x - circle_center.x
    fz = line_start.z - circle_center.z

    a = dx * dx + dz * dz
    b = 2.0 * (fx * dx + fz * dz)
    c = fx * fx + fz * fz - radius * radius

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return False

    discriminant = math.sqrt(discriminant)
    t1 = (-b - discriminant) / (2.0 * a)
    t2 = (-b + discriminant) / (2.0 * a)

    return (0 <= t1 <= 1) or (0 <= t2 <= 1) or (t1 < 0 and t2 > 1)

def closest_point_on_line(point: Vec3, line_start: Vec3, line_end: Vec3) -> Vec3:
    line = Vec3(line_end.x - line_start.x, 0, line_end.z - line_start.z)
    length_sq = line.x * line.x + line.z * line.z
    if length_sq < 0.0001:
        return line_start

    to_point = Vec3(point.x - line_start.x, 0, point.z - line_start.z)
    t = max(0, min(1, (to_point.x * line.x + to_point.z * line.z) / length_sq))
    return Vec3(line_start.x + line.x * t, 0, line_start.z + line.z * t)

def ray_plane_intersection(ray_origin: Vec3, ray_dir: Vec3,
                           plane_point: Vec3, plane_normal: Vec3) -> Optional[Vec3]:
    denom = vec3_dot(plane_normal, ray_dir)
    if abs(denom) < 0.0001:
        return None
    diff = Vec3(plane_point.x - ray_origin.x, plane_point.y - ray_origin.y, plane_point.z - ray_origin.z)
    t = vec3_dot(diff, plane_normal) / denom
    if t < 0:
        return None
    return Vec3(ray_origin.x + ray_dir.x * t, ray_origin.y + ray_dir.y * t, ray_origin.z + ray_dir.z * t)

# =============================================================================
# SOCCER-SPECIFIC HELPERS
# =============================================================================

def calculate_pass_target(passer_pos: Vec3, receiver_pos: Vec3,
                          receiver_velocity: Vec3, ball_speed: float) -> Vec3:
    distance = vec3_distance_xz(passer_pos, receiver_pos)
    travel_time = distance / max(ball_speed, 1.0)
    lead = Vec3(
        receiver_velocity.x * travel_time * 0.6,
        0,
        receiver_velocity.z * travel_time * 0.6
    )
    return Vec3(receiver_pos.x + lead.x, 0, receiver_pos.z + lead.z)

def calculate_shot_direction(shooter_pos: Vec3, goal_pos: Vec3,
                              accuracy: float, power: float) -> Vec3:
    direction = vec3_normalize(Vec3(goal_pos.x - shooter_pos.x, 0, goal_pos.z - shooter_pos.z))
    inaccuracy = (1.0 - accuracy) * 0.3
    angle_offset = random.gauss(0, inaccuracy)
    direction = vec3_rotate_y(direction, angle_offset)
    height = random.uniform(0.2, 2.0) * (1.0 - accuracy * 0.5)
    return Vec3(direction.x * power, height + power * 0.15, direction.z * power)

def calculate_trajectory(start_pos: Vec3, velocity: Vec3, gravity: float,
                          time_step: float, max_time: float) -> List[Vec3]:
    points = []
    pos = Vec3(start_pos.x, start_pos.y, start_pos.z)
    vel = Vec3(velocity.x, velocity.y, velocity.z)
    t = 0.0
    while t < max_time:
        points.append(Vec3(pos.x, pos.y, pos.z))
        vel = Vec3(vel.x, vel.y + gravity * time_step, vel.z)
        pos = Vec3(pos.x + vel.x * time_step, pos.y + vel.y * time_step, pos.z + vel.z * time_step)
        if pos.y < 0:
            pos = Vec3(pos.x, 0, pos.z)
            break
        t += time_step
    points.append(pos)
    return points

def predict_ball_position(ball_pos: Vec3, ball_vel: Vec3, time: float,
                           friction: float = 0.985, gravity: float = -9.81) -> Vec3:
    x = ball_pos.x
    y = ball_pos.y
    z = ball_pos.z
    vx = ball_vel.x
    vy = ball_vel.y
    vz = ball_vel.z

    steps = int(time / 0.02)
    for _ in range(steps):
        x += vx * 0.02
        y += vy * 0.02
        z += vz * 0.02
        vy += gravity * 0.02
        if y <= 0:
            y = 0
            vy = abs(vy) * 0.5
            if abs(vy) < 0.5:
                vy = 0
        vx *= friction
        vz *= friction

    return Vec3(x, max(0, y), z)

def is_offside_position(player_pos: Vec3, ball_pos: Vec3,
                         defenders: List[Vec3], attacking_direction: int) -> bool:
    from config import OFFSIDE_TOLERANCE
    if attacking_direction > 0:
        if player_pos.x <= ball_pos.x:
            return False
        second_last_defender_x = -999
        if len(defenders) >= 2:
            sorted_defenders = sorted(defenders, key=lambda d: d.x, reverse=True)
            second_last_defender_x = sorted_defenders[1].x
        elif len(defenders) == 1:
            second_last_defender_x = defenders[0].x
        return player_pos.x > second_last_defender_x + OFFSIDE_TOLERANCE
    else:
        if player_pos.x >= ball_pos.x:
            return False
        second_last_defender_x = 999
        if len(defenders) >= 2:
            sorted_defenders = sorted(defenders, key=lambda d: d.x)
            second_last_defender_x = sorted_defenders[1].x
        elif len(defenders) == 1:
            second_last_defender_x = defenders[0].x
        return player_pos.x < second_last_defender_x - OFFSIDE_TOLERANCE

def get_best_pass_target(passer: 'Player', teammates: List['Player'],
                          opponents: List['Player'], ball_pos: Vec3) -> Optional['Player']:
    best_target = None
    best_score = -999.0

    for teammate in teammates:
        if teammate == passer:
            continue
        if teammate.is_goalkeeper and vec3_distance_xz(teammate.position, ball_pos) > 30:
            continue

        dist = vec3_distance_xz(passer.position, teammate.position)
        if dist < 3.0 or dist > 50.0:
            continue

        direction = vec3_normalize_xz(Vec3(
            teammate.position.x - passer.position.x, 0,
            teammate.position.z - passer.position.z
        ))

        is_clear = True
        min_opponent_dist = 999.0
        for opponent in opponents:
            opp_to_line = closest_point_on_line(opponent.position, passer.position, teammate.position)
            opp_dist = vec3_distance_xz(opponent.position, opp_to_line)
            if opp_dist < 2.0:
                pass_line_dist = vec3_distance_xz(passer.position, opp_to_line)
                if pass_line_dist < dist * 0.9:
                    is_clear = False
                    break
            min_opponent_dist = min(min_opponent_dist, opp_dist)

        if not is_clear:
            continue

        score = 0.0
        score += (1.0 - dist / 50.0) * 20.0
        score += min_opponent_dist * 3.0
        forward_component = direction.x * passer.attacking_direction
        score += forward_component * 15.0
        if abs(teammate.position.z) < 15 and abs(teammate.position.x) > 30:
            score += 10.0

        if score > best_score:
            best_score = score
            best_target = teammate

    return best_target

def calculate_intercept_point(player_pos: Vec3, player_speed: float,
                               ball_pos: Vec3, ball_vel: Vec3) -> Optional[Vec3]:
    for t in [x * 0.1 for x in range(1, 30)]:
        future_ball = predict_ball_position(ball_pos, ball_vel, t)
        dist = vec3_distance_xz(player_pos, future_ball)
        time_needed = dist / max(player_speed, 1.0)
        if time_needed <= t + 0.2:
            return future_ball
    return None

# =============================================================================
# RANDOM & PROBABILITY
# =============================================================================

def weighted_random_choice(choices: list, weights: list):
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if r <= cumulative:
            return choice
    return choices[-1]

def probability_check(chance: float) -> bool:
    return random.random() < chance

def random_offset(magnitude: float) -> Vec3:
    angle = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0, magnitude)
    return Vec3(math.cos(angle) * dist, 0, math.sin(angle) * dist)

def gaussian_random(mean: float = 0.0, std: float = 1.0) -> float:
    return random.gauss(mean, std)

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))

def inverse_lerp(a: float, b: float, value: float) -> float:
    if abs(b - a) < 0.0001:
        return 0.0
    return (value - a) / (b - a)

def remap(value: float, from_min: float, from_max: float, to_min: float, to_max: float) -> float:
    t = inverse_lerp(from_min, from_max, value)
    return lerp(to_min, to_max, t)

def smooth_step(edge0: float, edge1: float, x: float) -> float:
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def ease_in_out(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t

# =============================================================================
# FORMATTING
# =============================================================================

def format_time(seconds: float) -> str:
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"

def format_match_time(seconds: float, half: int) -> str:
    from config import MATCH_HALF_DURATION
    match_minutes = int((seconds / MATCH_HALF_DURATION) * 45) + (45 if half > 1 else 0)
    match_minutes = max(1, match_minutes)
    return f"{match_minutes}'"

def attr_to_multiplier(attribute_value: int) -> float:
    return 0.5 + (attribute_value / 99.0) * 0.7

def speed_from_attribute(pace: int, base_speed: float) -> float:
    return base_speed * (0.7 + (pace / 99.0) * 0.4)

# =============================================================================
# SPATIAL QUERIES
# =============================================================================

def find_nearest_player(position: Vec3, players: list, exclude=None, max_distance: float = float('inf')):
    nearest = None
    nearest_dist = max_distance
    for player in players:
        if player == exclude:
            continue
        dist = vec3_distance_xz(position, player.position)
        if dist < nearest_dist:
            nearest_dist = dist
            nearest = player
    return nearest, nearest_dist

def find_players_in_radius(position: Vec3, players: list, radius: float, exclude=None) -> list:
    result = []
    for player in players:
        if player == exclude:
            continue
        if vec3_distance_xz(position, player.position) <= radius:
            result.append(player)
    return result

def find_open_space(position: Vec3, players: list, search_radius: float = 15.0,
                    samples: int = 8) -> Vec3:
    best_pos = position
    best_score = -999

    for i in range(samples):
        angle = (2 * math.pi * i) / samples
        for dist in [5, 10, 15]:
            test_pos = Vec3(
                position.x + math.cos(angle) * dist,
                0,
                position.z + math.sin(angle) * dist
            )
            if not point_in_field(test_pos, -2):
                continue

            min_player_dist = 999
            for player in players:
                d = vec3_distance_xz(test_pos, player.position)
                min_player_dist = min(min_player_dist, d)

            score = min_player_dist
            if score > best_score:
                best_score = score
                best_pos = test_pos

    return best_pos

def passing_lane_clear(start: Vec3, end: Vec3, opponents: list,
                        lane_width: float = 2.0) -> bool:
    for opp in opponents:
        closest = closest_point_on_line(opp.position, start, end)
        dist_to_line = vec3_distance_xz(opp.position, closest)
        dist_from_start = vec3_distance_xz(start, closest)
        total_dist = vec3_distance_xz(start, end)
        if dist_to_line < lane_width and dist_from_start < total_dist * 0.95:
            return False
    return True

def goal_angle(position: Vec3, goal_x: float, goal_width: float = 7.32) -> float:
    left_post = Vec3(goal_x, 0, -goal_width / 2)
    right_post = Vec3(goal_x, 0, goal_width / 2)
    to_left = vec3_normalize_xz(Vec3(left_post.x - position.x, 0, left_post.z - position.z))
    to_right = vec3_normalize_xz(Vec3(right_post.x - position.x, 0, right_post.z - position.z))
    angle = vec3_angle_between(to_left, to_right)
    return angle

def expected_goals(position: Vec3, goal_x: float, defenders_between: int = 0) -> float:
    distance = abs(position.x - goal_x) + abs(position.z) * 0.3
    angle = goal_angle(position, goal_x)
    xg = (angle / math.pi) * math.exp(-distance / 20.0)
    xg *= max(0.1, 1.0 - defenders_between * 0.15)
    return clamp(xg, 0.01, 0.95)
