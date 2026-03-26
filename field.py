"""
Ultimate Soccer 3D - Field & Stadium
3D pitch with markings, goals, nets, stadium stands, and lighting.
"""
import math
from ursina import (Entity, Vec3, Vec2, color, Mesh, camera, 
                     DirectionalLight, AmbientLight, PointLight, scene)
from config import (
    FIELD_LENGTH, FIELD_WIDTH, FIELD_HALF_LENGTH, FIELD_HALF_WIDTH,
    PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH, GOAL_AREA_LENGTH, GOAL_AREA_WIDTH,
    GOAL_WIDTH, GOAL_HEIGHT, GOAL_DEPTH, GOAL_POST_RADIUS, CENTER_CIRCLE_RADIUS,
    CORNER_ARC_RADIUS, LINE_WIDTH, GRASS_COLOR_1, GRASS_COLOR_2,
    GRASS_STRIPE_WIDTH, LINE_COLOR, STADIUM_STAND_HEIGHT, STADIUM_STAND_DEPTH,
    STADIUM_LIGHT_HEIGHT, STADIUM_AMBIENT_LIGHT, STADIUM_DIRECTIONAL_LIGHT,
    PENALTY_SPOT_DISTANCE, COLOR_NET_WHITE, COLOR_WHITE, COLOR_PITCH_GREEN,
    COLOR_PITCH_DARK, WeatherType, rgb, rgba,
)


class Field:
    """Creates and manages the 3D football field with all markings and stadium."""

    def __init__(self, weather: WeatherType = WeatherType.CLEAR):
        self.weather = weather
        self.entities = []
        self.lights = []
        self.goal_entities = {'left': [], 'right': []}
        self._build_pitch()
        self._build_lines()
        self._build_goals()
        self._build_stadium()
        self._setup_lighting()
        self._build_sky()

    def _build_pitch(self):
        """Create the grass pitch with stripe pattern."""
        stripe_count = int(FIELD_LENGTH / GRASS_STRIPE_WIDTH)
        for i in range(stripe_count):
            x_pos = -FIELD_HALF_LENGTH + GRASS_STRIPE_WIDTH * (i + 0.5)
            c = GRASS_COLOR_1 if i % 2 == 0 else GRASS_COLOR_2
            stripe = Entity(
                model='quad',
                color=rgb(*[int(v * 255) for v in c]),
                scale=(GRASS_STRIPE_WIDTH, FIELD_WIDTH),
                position=(x_pos, 0.0, 0),
                rotation=(90, 0, 0),
                double_sided=True
            )
            self.entities.append(stripe)

        surround_size = 8.0
        surround_color = rgb(30, 100, 28)

        for side_x in [-1, 1]:
            surround = Entity(
                model='quad',
                color=surround_color,
                scale=(surround_size, FIELD_WIDTH + surround_size * 2),
                position=(side_x * (FIELD_HALF_LENGTH + surround_size / 2), -0.01, 0),
                rotation=(90, 0, 0),
                double_sided=True
            )
            self.entities.append(surround)

        for side_z in [-1, 1]:
            surround = Entity(
                model='quad',
                color=surround_color,
                scale=(FIELD_LENGTH + surround_size * 2, surround_size),
                position=(0, -0.01, side_z * (FIELD_HALF_WIDTH + surround_size / 2)),
                rotation=(90, 0, 0),
                double_sided=True
            )
            self.entities.append(surround)

    def _create_line(self, start_x, start_z, end_x, end_z, width=LINE_WIDTH):
        """Create a line on the pitch."""
        dx = end_x - start_x
        dz = end_z - start_z
        length = math.sqrt(dx * dx + dz * dz)
        center_x = (start_x + end_x) / 2.0
        center_z = (start_z + end_z) / 2.0
        angle = math.degrees(math.atan2(dx, dz))

        line = Entity(
            model='quad',
            color=rgb(255, 255, 255),
            scale=(width, length),
            position=(center_x, 0.01, center_z),
            rotation=(90, angle, 0),
            double_sided=True
        )
        self.entities.append(line)
        return line

    def _create_circle(self, center_x, center_z, radius, segments=64, width=LINE_WIDTH):
        """Create a circle line on the pitch."""
        for i in range(segments):
            angle1 = (2 * math.pi * i) / segments
            angle2 = (2 * math.pi * (i + 1)) / segments
            x1 = center_x + radius * math.cos(angle1)
            z1 = center_z + radius * math.sin(angle1)
            x2 = center_x + radius * math.cos(angle2)
            z2 = center_z + radius * math.sin(angle2)
            self._create_line(x1, z1, x2, z2, width)

    def _create_arc(self, center_x, center_z, radius, start_angle, end_angle,
                     segments=16, width=LINE_WIDTH):
        """Create an arc line on the pitch."""
        for i in range(segments):
            t1 = start_angle + (end_angle - start_angle) * i / segments
            t2 = start_angle + (end_angle - start_angle) * (i + 1) / segments
            x1 = center_x + radius * math.cos(t1)
            z1 = center_z + radius * math.sin(t1)
            x2 = center_x + radius * math.cos(t2)
            z2 = center_z + radius * math.sin(t2)
            self._create_line(x1, z1, x2, z2, width)

    def _create_spot(self, x, z, radius=0.15):
        """Create a spot (penalty spot, center spot)."""
        spot = Entity(
            model='sphere',
            color=color.white,
            scale=radius * 2,
            position=(x, 0.02, z),
        )
        self.entities.append(spot)

    def _build_lines(self):
        """Build all pitch markings."""
        hl = FIELD_HALF_LENGTH
        hw = FIELD_HALF_WIDTH

        # Touchlines (long sides)
        self._create_line(-hl, -hw, hl, -hw)
        self._create_line(-hl, hw, hl, hw)

        # Goal lines (short sides)
        self._create_line(-hl, -hw, -hl, hw)
        self._create_line(hl, -hw, hl, hw)

        # Halfway line
        self._create_line(0, -hw, 0, hw)

        # Center circle
        self._create_circle(0, 0, CENTER_CIRCLE_RADIUS)

        # Center spot
        self._create_spot(0, 0)

        # Penalty areas
        for side in [-1, 1]:
            pa_x = side * hl
            pa_inner_x = side * (hl - PENALTY_AREA_LENGTH)
            pa_hw = PENALTY_AREA_WIDTH / 2.0

            # Penalty area box
            self._create_line(pa_x, -pa_hw, pa_inner_x, -pa_hw)
            self._create_line(pa_x, pa_hw, pa_inner_x, pa_hw)
            self._create_line(pa_inner_x, -pa_hw, pa_inner_x, pa_hw)

            # Goal area box
            ga_inner_x = side * (hl - GOAL_AREA_LENGTH)
            ga_hw = GOAL_AREA_WIDTH / 2.0
            self._create_line(pa_x, -ga_hw, ga_inner_x, -ga_hw)
            self._create_line(pa_x, ga_hw, ga_inner_x, ga_hw)
            self._create_line(ga_inner_x, -ga_hw, ga_inner_x, ga_hw)

            # Penalty spot
            penalty_x = side * (hl - PENALTY_SPOT_DISTANCE)
            self._create_spot(penalty_x, 0)

            # Penalty arc (D)
            if side > 0:
                self._create_arc(penalty_x, 0, CENTER_CIRCLE_RADIUS,
                                  math.radians(125), math.radians(235), 20)
            else:
                self._create_arc(penalty_x, 0, CENTER_CIRCLE_RADIUS,
                                  math.radians(-55), math.radians(55), 20)

            # Corner arcs
            for corner_z in [-1, 1]:
                cx = side * hl
                cz = corner_z * hw
                if side > 0 and corner_z > 0:
                    self._create_arc(cx, cz, CORNER_ARC_RADIUS,
                                      math.radians(180), math.radians(270), 8)
                elif side > 0 and corner_z < 0:
                    self._create_arc(cx, cz, CORNER_ARC_RADIUS,
                                      math.radians(90), math.radians(180), 8)
                elif side < 0 and corner_z > 0:
                    self._create_arc(cx, cz, CORNER_ARC_RADIUS,
                                      math.radians(270), math.radians(360), 8)
                else:
                    self._create_arc(cx, cz, CORNER_ARC_RADIUS,
                                      math.radians(0), math.radians(90), 8)

    def _build_goals(self):
        """Build goal posts, crossbar, and nets for both ends."""
        for side in [-1, 1]:
            goal_x = side * FIELD_HALF_LENGTH
            post_color = color.white
            goal_parts = []

            # Left post
            left_post = Entity(
                model='cube',
                color=post_color,
                scale=(GOAL_POST_RADIUS * 2, GOAL_HEIGHT, GOAL_POST_RADIUS * 2),
                position=(goal_x, GOAL_HEIGHT / 2, -GOAL_WIDTH / 2),
            )
            goal_parts.append(left_post)

            # Right post
            right_post = Entity(
                model='cube',
                color=post_color,
                scale=(GOAL_POST_RADIUS * 2, GOAL_HEIGHT, GOAL_POST_RADIUS * 2),
                position=(goal_x, GOAL_HEIGHT / 2, GOAL_WIDTH / 2),
            )
            goal_parts.append(right_post)

            # Crossbar
            crossbar = Entity(
                model='cube',
                color=post_color,
                scale=(GOAL_POST_RADIUS * 2, GOAL_POST_RADIUS * 2, GOAL_WIDTH),
                position=(goal_x, GOAL_HEIGHT, 0),
            )
            goal_parts.append(crossbar)

            # Back frame top
            back_top = Entity(
                model='cube',
                color=post_color,
                scale=(GOAL_POST_RADIUS * 2, GOAL_POST_RADIUS * 2, GOAL_WIDTH),
                position=(goal_x + side * GOAL_DEPTH, GOAL_HEIGHT * 0.6, 0),
            )
            goal_parts.append(back_top)

            # Back frame posts
            for z_pos in [-GOAL_WIDTH / 2, GOAL_WIDTH / 2]:
                back_post = Entity(
                    model='cube',
                    color=post_color,
                    scale=(GOAL_POST_RADIUS * 2, GOAL_HEIGHT * 0.6, GOAL_POST_RADIUS * 2),
                    position=(goal_x + side * GOAL_DEPTH, GOAL_HEIGHT * 0.3, z_pos),
                )
                goal_parts.append(back_post)

            # Side frame bars
            for z_pos in [-GOAL_WIDTH / 2, GOAL_WIDTH / 2]:
                side_bar = Entity(
                    model='cube',
                    color=post_color,
                    scale=(GOAL_DEPTH, GOAL_POST_RADIUS * 2, GOAL_POST_RADIUS * 2),
                    position=(goal_x + side * GOAL_DEPTH / 2, GOAL_HEIGHT, z_pos),
                )
                goal_parts.append(side_bar)

            # Net - back
            net_back = Entity(
                model='quad',
                color=rgba(255, 255, 255, 80),
                scale=(GOAL_WIDTH, GOAL_HEIGHT * 0.6),
                position=(goal_x + side * GOAL_DEPTH, GOAL_HEIGHT * 0.3, 0),
                rotation=(0, 0, 0),
                double_sided=True
            )
            goal_parts.append(net_back)

            # Net - top (angled)
            net_top = Entity(
                model='quad',
                color=rgba(255, 255, 255, 60),
                scale=(GOAL_DEPTH, GOAL_WIDTH),
                position=(goal_x + side * GOAL_DEPTH / 2, GOAL_HEIGHT * 0.8, 0),
                rotation=(70 * side, 0, 0) if side > 0 else (110, 0, 0),
                double_sided=True
            )
            goal_parts.append(net_top)

            # Net - sides
            for z_pos in [-GOAL_WIDTH / 2, GOAL_WIDTH / 2]:
                net_side = Entity(
                    model='quad',
                    color=rgba(255, 255, 255, 60),
                    scale=(GOAL_DEPTH, GOAL_HEIGHT * 0.8),
                    position=(goal_x + side * GOAL_DEPTH / 2, GOAL_HEIGHT * 0.4, z_pos),
                    rotation=(0, 90, 0),
                    double_sided=True
                )
                goal_parts.append(net_side)

            side_key = 'right' if side > 0 else 'left'
            self.goal_entities[side_key] = goal_parts
            self.entities.extend(goal_parts)

    def _build_stadium(self):
        """Build stadium stands around the pitch."""
        stand_color_dark = rgb(60, 60, 70)
        stand_color_seats = rgb(80, 30, 30)
        stand_height = STADIUM_STAND_HEIGHT
        stand_depth = STADIUM_STAND_DEPTH

        # Four stands
        positions = [
            # Side stands (long)
            (0, stand_height / 2, -(FIELD_HALF_WIDTH + stand_depth / 2 + 6),
             FIELD_LENGTH + 20, stand_height, stand_depth, 0),
            (0, stand_height / 2, (FIELD_HALF_WIDTH + stand_depth / 2 + 6),
             FIELD_LENGTH + 20, stand_height, stand_depth, 0),
            # End stands (short)
            (-(FIELD_HALF_LENGTH + stand_depth / 2 + 6), stand_height / 2, 0,
             stand_depth, stand_height, FIELD_WIDTH + 20, 0),
            ((FIELD_HALF_LENGTH + stand_depth / 2 + 6), stand_height / 2, 0,
             stand_depth, stand_height, FIELD_WIDTH + 20, 0),
        ]

        seat_colors = [
            rgb(150, 30, 30),
            rgb(30, 30, 150),
            rgb(150, 30, 30),
            rgb(30, 30, 150),
        ]

        for i, (px, py, pz, sx, sy, sz, ry) in enumerate(positions):
            # Main structure
            stand = Entity(
                model='cube',
                color=stand_color_dark,
                scale=(sx, sy, sz),
                position=(px, py, pz),
            )
            self.entities.append(stand)

            # Seat face (colored)
            seat_offset_z = 0
            seat_offset_x = 0
            seat_rot = (0, 0, 0)
            if i == 0:
                seat_offset_z = stand_depth / 2 + 0.1
                seat_rot = (0, 0, 0)
                seat_scale = (sx, sy * 0.9, 0.1)
            elif i == 1:
                seat_offset_z = -stand_depth / 2 - 0.1
                seat_rot = (0, 180, 0)
                seat_scale = (sx, sy * 0.9, 0.1)
            elif i == 2:
                seat_offset_x = stand_depth / 2 + 0.1
                seat_rot = (0, -90, 0)
                seat_scale = (sz, sy * 0.9, 0.1)
            else:
                seat_offset_x = -stand_depth / 2 - 0.1
                seat_rot = (0, 90, 0)
                seat_scale = (sz, sy * 0.9, 0.1)

            seats = Entity(
                model='cube',
                color=seat_colors[i],
                scale=seat_scale,
                position=(px + seat_offset_x, py, pz + seat_offset_z),
                rotation=seat_rot,
            )
            self.entities.append(seats)

        # Corner fills
        corner_size = 10
        corner_positions = [
            (-(FIELD_HALF_LENGTH + 6), 5, -(FIELD_HALF_WIDTH + 6)),
            ((FIELD_HALF_LENGTH + 6), 5, -(FIELD_HALF_WIDTH + 6)),
            (-(FIELD_HALF_LENGTH + 6), 5, (FIELD_HALF_WIDTH + 6)),
            ((FIELD_HALF_LENGTH + 6), 5, (FIELD_HALF_WIDTH + 6)),
        ]
        for cx, cy, cz in corner_positions:
            corner = Entity(
                model='cube',
                color=stand_color_dark,
                scale=(corner_size, 10, corner_size),
                position=(cx, cy, cz),
            )
            self.entities.append(corner)

        # Floodlights
        light_positions = [
            (-FIELD_HALF_LENGTH - 3, STADIUM_LIGHT_HEIGHT, -FIELD_HALF_WIDTH - 3),
            (FIELD_HALF_LENGTH + 3, STADIUM_LIGHT_HEIGHT, -FIELD_HALF_WIDTH - 3),
            (-FIELD_HALF_LENGTH - 3, STADIUM_LIGHT_HEIGHT, FIELD_HALF_WIDTH + 3),
            (FIELD_HALF_LENGTH + 3, STADIUM_LIGHT_HEIGHT, FIELD_HALF_WIDTH + 3),
        ]
        for lx, ly, lz in light_positions:
            # Pole
            pole = Entity(
                model='cube',
                color=rgb(100, 100, 100),
                scale=(0.5, STADIUM_LIGHT_HEIGHT, 0.5),
                position=(lx, ly / 2, lz),
            )
            self.entities.append(pole)
            # Light head
            light_head = Entity(
                model='cube',
                color=rgb(240, 240, 200),
                scale=(3, 1, 3),
                position=(lx, ly, lz),
            )
            self.entities.append(light_head)

    def _setup_lighting(self):
        """Set up scene lighting based on weather."""
        if self.weather == WeatherType.NIGHT:
            ambient_strength = 0.2
            dir_strength = 0.4
            sky_color = rgb(10, 10, 30)
        elif self.weather == WeatherType.CLOUDY:
            ambient_strength = 0.5
            dir_strength = 0.5
            sky_color = rgb(140, 140, 150)
        elif self.weather == WeatherType.RAIN or self.weather == WeatherType.HEAVY_RAIN:
            ambient_strength = 0.35
            dir_strength = 0.45
            sky_color = rgb(100, 100, 120)
        else:
            ambient_strength = STADIUM_AMBIENT_LIGHT
            dir_strength = STADIUM_DIRECTIONAL_LIGHT
            sky_color = rgb(135, 206, 235)

        try:
            sun = DirectionalLight(
                shadow_map_resolution=Vec2(2048, 2048),
            )
            sun.look_at(Vec3(1, -3, -1))
            self.lights.append(sun)
        except Exception:
            pass  # Lighting may fail outside full app context

        scene.fog_density = 0
        if self.weather == WeatherType.FOG:
            scene.fog_density = 0.01
            scene.fog_color = rgb(180, 180, 190)

    def _build_sky(self):
        """Create sky dome."""
        if self.weather == WeatherType.NIGHT:
            sky_col = rgb(10, 10, 35)
        elif self.weather in [WeatherType.RAIN, WeatherType.HEAVY_RAIN]:
            sky_col = rgb(90, 95, 110)
        elif self.weather == WeatherType.CLOUDY:
            sky_col = rgb(150, 155, 165)
        elif self.weather == WeatherType.SNOW:
            sky_col = rgb(200, 205, 215)
        else:
            sky_col = rgb(135, 206, 235)

        sky = Entity(
            model='sphere',
            scale=500,
            color=sky_col,
            double_sided=True,
        )
        self.entities.append(sky)

    def is_ball_in_goal(self, ball_pos: Vec3) -> int:
        """Check if ball is in a goal. Returns 1 for right goal, -1 for left, 0 for none."""
        if ball_pos.y <= GOAL_HEIGHT and abs(ball_pos.z) <= GOAL_WIDTH / 2:
            if ball_pos.x >= FIELD_HALF_LENGTH:
                return 1
            elif ball_pos.x <= -FIELD_HALF_LENGTH:
                return -1
        return 0

    def is_ball_out_of_bounds(self, ball_pos: Vec3) -> str:
        """Check if ball is out of bounds. Returns 'goal_kick', 'corner', 'throw_in', or ''."""
        if abs(ball_pos.x) > FIELD_HALF_LENGTH + 1:
            return 'goal_line'
        if abs(ball_pos.z) > FIELD_HALF_WIDTH + 0.5:
            return 'throw_in'
        return ''

    def get_goal_position(self, side: int) -> Vec3:
        """Get center of goal for given side (1=right, -1=left)."""
        return Vec3(side * FIELD_HALF_LENGTH, GOAL_HEIGHT / 2, 0)

    def get_penalty_spot(self, side: int) -> Vec3:
        """Get penalty spot position."""
        return Vec3(side * (FIELD_HALF_LENGTH - PENALTY_SPOT_DISTANCE), 0, 0)

    def get_corner_position(self, side_x: int, side_z: int) -> Vec3:
        """Get corner position."""
        return Vec3(side_x * FIELD_HALF_LENGTH, 0, side_z * FIELD_HALF_WIDTH)

    def get_center_spot(self) -> Vec3:
        return Vec3(0, 0, 0)

    def cleanup(self):
        """Remove all field entities."""
        for entity in self.entities:
            try:
                entity.disable()
            except Exception:
                pass
        self.entities.clear()
        for light in self.lights:
            try:
                light.disable()
            except Exception:
                pass
        self.lights.clear()
