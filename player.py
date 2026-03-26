"""
Ultimate Soccer 3D - Player Entity
Player model, attributes, state machine, animations, and movement.
"""
import math
import random
from ursina import Entity, Vec3, Vec2, color, time as ursina_time
from config import (
    PLAYER_HEIGHT, PLAYER_RADIUS, PLAYER_MASS,
    PLAYER_WALK_SPEED, PLAYER_JOG_SPEED, PLAYER_RUN_SPEED, PLAYER_SPRINT_SPEED,
    PLAYER_MAX_SPRINT_SPEED, PLAYER_ACCELERATION, PLAYER_DECELERATION,
    PLAYER_TURN_SPEED, PLAYER_TURN_SPEED_WITH_BALL,
    STAMINA_MAX, STAMINA_SPRINT_DRAIN, STAMINA_RUN_DRAIN,
    STAMINA_RECOVERY_RATE, STAMINA_RECOVERY_WALKING, STAMINA_LOW_THRESHOLD,
    STAMINA_SPEED_PENALTY,
    DRIBBLE_TOUCH_DISTANCE, DRIBBLE_CLOSE_CONTROL, DRIBBLE_SPEED_PENALTY,
    DRIBBLE_LOSE_BALL_BASE_CHANCE, DRIBBLE_SKILL_MOVE_DURATION,
    PASS_SHORT_POWER, PASS_MEDIUM_POWER, PASS_LONG_POWER, PASS_THROUGH_BALL_POWER,
    PASS_LOB_POWER, PASS_LOB_ANGLE, PASS_ACCURACY_BASE, PASS_POWER_CHARGE_RATE,
    PASS_MAX_POWER, PASS_CROSS_POWER, PASS_CROSS_HEIGHT,
    SHOOT_POWER_BASE, SHOOT_POWER_MAX, SHOOT_POWER_CHARGE_RATE,
    SHOOT_ACCURACY_BASE, SHOOT_FINESSE_POWER, SHOOT_FINESSE_CURVE,
    SHOOT_ANGLE_VARIANCE, SHOOT_HEIGHT_BASE, SHOOT_HEIGHT_VARIANCE,
    TACKLE_RANGE, TACKLE_SLIDE_RANGE, TACKLE_SLIDE_SPEED,
    TACKLE_SLIDE_DURATION, TACKLE_SLIDE_COOLDOWN,
    TACKLE_STANDING_RANGE, TACKLE_STANDING_DURATION,
    TACKLE_SUCCESS_BASE, TACKLE_FOUL_CHANCE_BASE,
    TACKLE_RECOVERY_TIME,
    HEADER_JUMP_HEIGHT, HEADER_JUMP_DURATION, HEADER_RANGE,
    GK_DIVE_SPEED, GK_DIVE_RANGE, GK_DIVE_DURATION, GK_DIVE_RECOVERY,
    GK_REACTION_TIME, GK_POSITIONING_SPEED, GK_RUSH_SPEED,
    GK_CATCH_RANGE, GK_PUNCH_RANGE, GK_PARRY_RANGE,
    Position, PlayerAttribute, FIELD_HALF_LENGTH, FIELD_HALF_WIDTH,
    ANIM_KICK_DURATION, ANIM_SLIDE_DURATION, ANIM_CELEBRATION_DURATION,
    rgb, rgba,
)
from utils import (
    vec3_length, vec3_length_xz, vec3_normalize, vec3_normalize_xz,
    vec3_distance_xz, vec3_lerp, vec3_rotate_y, vec3_angle_xz,
    vec3_from_angle_xz, clamp, lerp, attr_to_multiplier, speed_from_attribute,
    probability_check, gaussian_random
)


class PlayerState:
    IDLE = 'idle'
    RUNNING = 'running'
    SPRINTING = 'sprinting'
    DRIBBLING = 'dribbling'
    PASSING = 'passing'
    SHOOTING = 'shooting'
    CROSSING = 'crossing'
    TACKLING = 'tackling'
    SLIDE_TACKLING = 'slide_tackling'
    HEADING = 'heading'
    JUMPING = 'jumping'
    CELEBRATING = 'celebrating'
    INJURED = 'injured'
    SKILL_MOVE = 'skill_move'
    THROW_IN = 'throw_in'
    GK_DIVING = 'gk_diving'
    GK_HOLDING = 'gk_holding'
    GK_PUNCHING = 'gk_punching'
    GK_KICKING = 'gk_kicking'
    RECOVERING = 'recovering'
    GETTING_UP = 'getting_up'


class Player:
    """A football player with full attributes, state machine, and physics."""

    _id_counter = 0

    def __init__(self, name: str, number: int, position: Position,
                 team_id: str, team_color: tuple, rating: int = 70,
                 attrs: dict = None, is_gk: bool = False):
        Player._id_counter += 1
        self.id = Player._id_counter
        self.name = name
        self.number = number
        self.role = position
        self.team_id = team_id
        self.team_color = team_color
        self.overall_rating = rating
        self.is_goalkeeper = is_gk or position == Position.GK

        # Attributes
        self.attributes = {}
        self._init_attributes(attrs or {})

        # 3D Entity - body (capsule approximated with cylinder + sphere)
        body_color = rgb(
            int(team_color[0] * 255),
            int(team_color[1] * 255),
            int(team_color[2] * 255)
        )

        self.entity = Entity(
            model='cube',
            color=body_color,
            scale=(PLAYER_RADIUS * 2, PLAYER_HEIGHT * 0.6, PLAYER_RADIUS * 1.5),
            position=(0, PLAYER_HEIGHT * 0.3, 0),
        )

        # Head
        self.head = Entity(
            model='sphere',
            color=rgb(220, 180, 140),
            scale=PLAYER_RADIUS * 1.2,
            parent=self.entity,
            position=(0, 0.7, 0),
        )

        # Legs
        self.left_leg = Entity(
            model='cube',
            color=body_color,
            scale=(0.15, 0.5, 0.15),
            parent=self.entity,
            position=(-0.12, -0.55, 0),
        )
        self.right_leg = Entity(
            model='cube',
            color=body_color,
            scale=(0.15, 0.5, 0.15),
            parent=self.entity,
            position=(0.12, -0.55, 0),
        )

        # Number indicator above head
        self.indicator = Entity(
            model='quad',
            color=rgba(0, 0, 0, 0),
            scale=(0.8, 0.3),
            position=(0, 2.2, 0),
            billboard=True,
        )

        # Player selection arrow (diamond shape using cube rotated 45°)
        self.selection_arrow = Entity(
            model='cube',
            color=color.yellow,
            scale=(0.25, 0.25, 0.25),
            position=(0, 2.8, 0),
            rotation=(45, 0, 45),
            enabled=False,
        )

        # Selection ring on the ground (clearly marks controlled player)
        self.selection_ring = Entity(
            model='circle',
            color=color.yellow,
            scale=(PLAYER_RADIUS * 5, PLAYER_RADIUS * 5),
            position=(0, 0.02, 0),
            rotation=(90, 0, 0),
            double_sided=True,
            enabled=False,
        )

        # Shadow
        self.shadow = Entity(
            model='quad',
            color=rgba(0, 0, 0, 60),
            scale=(PLAYER_RADIUS * 3, PLAYER_RADIUS * 3),
            position=(0, 0.005, 0),
            rotation=(90, 0, 0),
            double_sided=True,
        )

        # Physics
        self.position = Vec3(0, 0, 0)
        self.velocity = Vec3(0, 0, 0)
        self.facing_angle = 0.0  # radians
        self.facing_direction = Vec3(0, 0, 1)
        self.move_direction = Vec3(0, 0, 0)
        self.target_position = None
        self.desired_velocity = Vec3(0, 0, 0)

        # State
        self.state = PlayerState.IDLE
        self.state_timer = 0.0
        self.previous_state = PlayerState.IDLE
        self.state_locked = False
        self.lock_timer = 0.0

        # Ball control
        self.has_ball = False
        self.dribble_timer = 0.0
        self.ball_touch_offset = Vec3(0, 0, 0)

        # Stamina
        self.stamina = STAMINA_MAX
        self.is_sprinting = False
        self.stamina_depleted = False

        # Combat
        self.tackle_cooldown = 0.0
        self.tackle_target = None
        self.slide_direction = Vec3(0, 0, 0)

        # Shooting/Passing
        self.power_charge = 0.0
        self.is_charging = False
        self.charge_type = None  # 'shoot', 'pass', 'cross', 'lob'

        # Heading
        self.is_jumping = False
        self.jump_height = 0.0
        self.jump_timer = 0.0
        self.jump_target = None

        # GK specific
        self.dive_direction = Vec3(0, 0, 0)
        self.dive_timer = 0.0
        self.gk_recovery_timer = 0.0
        self.is_rushing = False

        # AI
        self.is_human_controlled = False
        self.ai_state = None
        self.ai_target = None
        self.ai_timer = 0.0
        self.formation_position = Vec3(0, 0, 0)  # Target pos from formation
        self.attacking_direction = 1  # 1 = attacking right, -1 = attacking left

        # Match stats
        self.goals = 0
        self.assists = 0
        self.shots = 0
        self.passes_completed = 0
        self.passes_attempted = 0
        self.tackles_won = 0
        self.tackles_attempted = 0
        self.fouls_committed = 0
        self.yellow_cards = 0
        self.red_cards = 0
        self.is_sent_off = False
        self.distance_covered = 0.0
        self.last_position = Vec3(0, 0, 0)

        # Skill move
        self.skill_move_timer = 0.0
        self.skill_move_type = 0
        self.skill_move_direction = Vec3(0, 0, 0)

        # Animation state
        self.anim_timer = 0.0
        self.leg_anim_phase = 0.0
        self.celebration_type = 0

    def _init_attributes(self, attrs: dict):
        """Initialize player attributes from data."""
        default = self.overall_rating
        for attr in PlayerAttribute:
            self.attributes[attr] = attrs.get(attr, default)

    def get_attr(self, attr: PlayerAttribute) -> int:
        return self.attributes.get(attr, 50)

    def get_speed_multiplier(self) -> float:
        pace = self.get_attr(PlayerAttribute.PACE)
        mult = attr_to_multiplier(pace)
        if self.stamina < STAMINA_LOW_THRESHOLD:
            mult *= STAMINA_SPEED_PENALTY
        if self.has_ball:
            mult *= DRIBBLE_SPEED_PENALTY
        return mult

    def get_max_speed(self) -> float:
        base = PLAYER_SPRINT_SPEED if self.is_sprinting else PLAYER_RUN_SPEED
        return base * self.get_speed_multiplier()

    def set_position(self, pos: Vec3):
        self.position = Vec3(pos.x, 0, pos.z)
        self.last_position = Vec3(pos.x, 0, pos.z)
        self._update_entity()

    def set_facing(self, angle: float):
        self.facing_angle = angle
        self.facing_direction = vec3_from_angle_xz(angle)

    def select(self, selected: bool):
        self.is_human_controlled = selected
        self.selection_arrow.enabled = selected
        self.selection_ring.enabled = selected
        if selected:
            self.selection_arrow.color = color.yellow
            self.selection_ring.color = color.yellow
        else:
            self.selection_arrow.color = rgba(0, 0, 0, 0)
            self.selection_ring.color = rgba(0, 0, 0, 0)

    def move(self, direction: Vec3, sprint: bool = False):
        """Set movement direction and sprint flag."""
        self.move_direction = direction
        self.is_sprinting = sprint and self.stamina > 5

    def stop(self):
        self.move_direction = Vec3(0, 0, 0)
        self.is_sprinting = False

    def start_charge(self, charge_type: str):
        """Start charging a shot/pass."""
        if self.state_locked:
            return
        self.is_charging = True
        self.charge_type = charge_type
        self.power_charge = 0.0

    def release_charge(self) -> float:
        """Release charge and return power level (0-1)."""
        power = min(1.0, self.power_charge)
        self.is_charging = False
        self.charge_type = None
        self.power_charge = 0.0
        return power

    def can_act(self) -> bool:
        return not self.state_locked and not self.is_sent_off

    def initiate_pass(self, target_pos: Vec3, ball, power_ratio: float = 0.5,
                       is_through: bool = False, is_lob: bool = False):
        """Execute a pass."""
        if not self.can_act():
            return

        self._set_state(PlayerState.PASSING, ANIM_KICK_DURATION)
        direction = vec3_normalize(Vec3(target_pos.x - self.position.x, 0,
                                         target_pos.z - self.position.z))

        accuracy_attr = self.get_attr(PlayerAttribute.SHORT_PASSING)
        if is_through:
            accuracy_attr = self.get_attr(PlayerAttribute.VISION)
        elif is_lob:
            accuracy_attr = self.get_attr(PlayerAttribute.LONG_PASSING)

        accuracy = PASS_ACCURACY_BASE * attr_to_multiplier(accuracy_attr)
        error_angle = gaussian_random(0, (1.0 - accuracy) * 0.15)
        direction = vec3_rotate_y(direction, error_angle)

        dist = vec3_distance_xz(self.position, target_pos)
        if is_lob:
            power = PASS_LOB_POWER * power_ratio * attr_to_multiplier(self.get_attr(PlayerAttribute.LONG_PASSING))
            kick_dir = Vec3(direction.x, math.sin(PASS_LOB_ANGLE), direction.z)
        elif is_through:
            power = PASS_THROUGH_BALL_POWER * power_ratio * attr_to_multiplier(self.get_attr(PlayerAttribute.VISION))
            kick_dir = Vec3(direction.x, 0.05, direction.z)
        elif dist > 25:
            power = PASS_LONG_POWER * power_ratio * attr_to_multiplier(self.get_attr(PlayerAttribute.LONG_PASSING))
            kick_dir = Vec3(direction.x, 0.1, direction.z)
        elif dist > 12:
            power = PASS_MEDIUM_POWER * power_ratio * attr_to_multiplier(self.get_attr(PlayerAttribute.SHORT_PASSING))
            kick_dir = Vec3(direction.x, 0.03, direction.z)
        else:
            power = PASS_SHORT_POWER * power_ratio * attr_to_multiplier(self.get_attr(PlayerAttribute.SHORT_PASSING))
            kick_dir = Vec3(direction.x, 0.01, direction.z)

        kick_dir = vec3_normalize(kick_dir)
        spin_attr = self.get_attr(PlayerAttribute.CURVE)
        spin = Vec3(gaussian_random(0, 0.5) * attr_to_multiplier(spin_attr), 0, 0)

        ball.kick(kick_dir, power, spin, kicker=self, is_pass=True)
        self.has_ball = False
        self.passes_attempted += 1
        self.facing_angle = vec3_angle_xz(direction)

    def initiate_shot(self, target_pos: Vec3, ball, power_ratio: float = 0.7,
                       is_finesse: bool = False, is_chip: bool = False):
        """Execute a shot."""
        if not self.can_act():
            return

        self._set_state(PlayerState.SHOOTING, ANIM_KICK_DURATION)
        direction = vec3_normalize(Vec3(target_pos.x - self.position.x, 0,
                                         target_pos.z - self.position.z))

        accuracy = SHOOT_ACCURACY_BASE * attr_to_multiplier(self.get_attr(PlayerAttribute.FINISHING))
        error_angle = gaussian_random(0, SHOOT_ANGLE_VARIANCE * (1.0 - accuracy))
        direction = vec3_rotate_y(direction, error_angle)

        if is_finesse:
            power = SHOOT_POWER_MAX * power_ratio * SHOOT_FINESSE_POWER * attr_to_multiplier(
                self.get_attr(PlayerAttribute.FINISHING))
            height = SHOOT_HEIGHT_BASE * 0.8
            spin = Vec3(SHOOT_FINESSE_CURVE * (1 if random.random() > 0.5 else -1), 0, 0)
        elif is_chip:
            power = SHOOT_POWER_BASE * power_ratio * 0.8
            height = 1.5
            spin = Vec3(0, 0, -2)
        else:
            power = SHOOT_POWER_MAX * power_ratio * attr_to_multiplier(
                self.get_attr(PlayerAttribute.SHOT_POWER))
            height = SHOOT_HEIGHT_BASE + gaussian_random(0, SHOOT_HEIGHT_VARIANCE * (1.0 - accuracy))
            spin_attr = self.get_attr(PlayerAttribute.CURVE)
            spin = Vec3(gaussian_random(0, 1.5) * attr_to_multiplier(spin_attr), 0,
                        gaussian_random(0, 0.5))

        kick_dir = vec3_normalize(Vec3(direction.x, max(0, height * 0.15), direction.z))
        ball.kick(kick_dir, power, spin, kicker=self, is_shot=True)
        self.has_ball = False
        self.shots += 1
        self.facing_angle = vec3_angle_xz(direction)

    def initiate_cross(self, target_pos: Vec3, ball, power_ratio: float = 0.6):
        """Execute a cross."""
        if not self.can_act():
            return

        self._set_state(PlayerState.CROSSING, ANIM_KICK_DURATION)
        direction = vec3_normalize(Vec3(target_pos.x - self.position.x, 0,
                                         target_pos.z - self.position.z))

        cross_attr = self.get_attr(PlayerAttribute.CROSSING)
        accuracy = PASS_ACCURACY_BASE * attr_to_multiplier(cross_attr)
        error_angle = gaussian_random(0, (1.0 - accuracy) * 0.2)
        direction = vec3_rotate_y(direction, error_angle)

        power = PASS_CROSS_POWER * power_ratio * attr_to_multiplier(cross_attr)
        height = PASS_CROSS_HEIGHT * (0.7 + power_ratio * 0.5)
        kick_dir = vec3_normalize(Vec3(direction.x, height * 0.08, direction.z))

        spin = Vec3(gaussian_random(0, 1.0), 0, -1.0)
        ball.kick(kick_dir, power, spin, kicker=self, is_cross=True)
        self.has_ball = False
        self.facing_angle = vec3_angle_xz(direction)

    def initiate_tackle(self, target_pos: Vec3, is_slide: bool = False):
        """Execute a tackle."""
        if not self.can_act() or self.tackle_cooldown > 0:
            return

        if is_slide:
            self._set_state(PlayerState.SLIDE_TACKLING, TACKLE_SLIDE_DURATION)
            self.slide_direction = vec3_normalize_xz(Vec3(
                target_pos.x - self.position.x, 0, target_pos.z - self.position.z
            ))
            self.tackle_cooldown = TACKLE_SLIDE_COOLDOWN
        else:
            self._set_state(PlayerState.TACKLING, TACKLE_STANDING_DURATION)
            self.tackle_cooldown = TACKLE_RECOVERY_TIME

        self.tackles_attempted += 1
        self.facing_angle = vec3_angle_xz(Vec3(
            target_pos.x - self.position.x, 0, target_pos.z - self.position.z
        ))

    def check_tackle_success(self, target_player) -> tuple:
        """Check if tackle wins the ball. Returns (success, is_foul, severity)."""
        tackle_attr = self.get_attr(PlayerAttribute.STANDING_TACKLE)
        if self.state == PlayerState.SLIDE_TACKLING:
            tackle_attr = self.get_attr(PlayerAttribute.SLIDING_TACKLE)

        success_chance = TACKLE_SUCCESS_BASE * attr_to_multiplier(tackle_attr)
        dribble_attr = target_player.get_attr(PlayerAttribute.DRIBBLING)
        success_chance *= (1.0 - attr_to_multiplier(dribble_attr) * 0.3)

        foul_chance = TACKLE_FOUL_CHANCE_BASE
        if self.state == PlayerState.SLIDE_TACKLING:
            foul_chance += 0.10
        angle_diff = abs(self.facing_angle - target_player.facing_angle)
        if angle_diff > math.pi * 0.7:
            foul_chance += 0.35
            success_chance *= 0.6

        aggression = self.get_attr(PlayerAttribute.AGGRESSION)
        foul_chance += (aggression / 99.0) * 0.1

        is_foul = probability_check(foul_chance)
        success = probability_check(success_chance) and not is_foul

        severity = 0.0
        if is_foul:
            severity = random.uniform(0.2, 0.6)
            if self.state == PlayerState.SLIDE_TACKLING:
                severity += 0.15
            if angle_diff > math.pi * 0.7:
                severity += 0.25
            severity = clamp(severity, 0.0, 1.0)

        return success, is_foul, severity

    def initiate_skill_move(self, direction: Vec3):
        """Execute a skill move / dribble trick."""
        if not self.can_act() or not self.has_ball:
            return

        dribble_attr = self.get_attr(PlayerAttribute.DRIBBLING)
        if dribble_attr < 60:
            self.skill_move_type = random.choice([0, 1])
        elif dribble_attr < 80:
            self.skill_move_type = random.choice([0, 1, 2, 3])
        else:
            self.skill_move_type = random.choice([0, 1, 2, 3, 4, 5])

        self._set_state(PlayerState.SKILL_MOVE, DRIBBLE_SKILL_MOVE_DURATION)
        self.skill_move_direction = direction if vec3_length(direction) > 0.1 else self.facing_direction
        self.skill_move_timer = DRIBBLE_SKILL_MOVE_DURATION

    def initiate_header(self, target_pos: Vec3, ball):
        """Execute a header."""
        if not self.can_act():
            return

        self._set_state(PlayerState.HEADING, HEADER_JUMP_DURATION)
        self.is_jumping = True
        self.jump_timer = HEADER_JUMP_DURATION
        self.jump_target = target_pos

        direction = vec3_normalize(Vec3(target_pos.x - self.position.x, 0,
                                         target_pos.z - self.position.z))
        heading_attr = self.get_attr(PlayerAttribute.HEADING)
        power = 8.0 * attr_to_multiplier(heading_attr)
        height_dir = random.uniform(-0.3, 0.1)
        kick_dir = Vec3(direction.x, height_dir, direction.z)

        ball.header(kick_dir, power, self)
        self.facing_angle = vec3_angle_xz(direction)

    # GK Actions
    def gk_dive(self, direction: Vec3):
        """Goalkeeper dive."""
        if not self.can_act() or self.gk_recovery_timer > 0:
            return

        self._set_state(PlayerState.GK_DIVING, GK_DIVE_DURATION)
        self.dive_direction = vec3_normalize(direction)
        self.dive_timer = GK_DIVE_DURATION
        self.gk_recovery_timer = GK_DIVE_RECOVERY

    def gk_catch(self, ball) -> bool:
        """Try to catch the ball. Returns success."""
        handling = self.get_attr(PlayerAttribute.GK_HANDLING)
        ball_speed = ball.speed
        catch_difficulty = clamp(ball_speed / 35.0, 0.0, 1.0)
        catch_chance = attr_to_multiplier(handling) * (1.0 - catch_difficulty * 0.5)

        if probability_check(catch_chance):
            ball.hold(self)
            self._set_state(PlayerState.GK_HOLDING, 1.0)
            return True
        else:
            # Parry instead
            parry_dir = Vec3(
                -ball.velocity.x * 0.3 + random.uniform(-3, 3),
                abs(ball.velocity.y) * 0.3 + random.uniform(1, 4),
                random.uniform(-5, 5)
            )
            ball.deflect(vec3_normalize(parry_dir), 0.4)
            return False

    def gk_punch(self, ball):
        """Goalkeeper punches the ball away."""
        punch_dir = Vec3(
            self.facing_direction.x * 15 + random.uniform(-3, 3),
            random.uniform(5, 10),
            random.uniform(-8, 8)
        )
        ball.kick(vec3_normalize(punch_dir), 18.0, kicker=self)

    def gk_distribute(self, target_pos: Vec3, ball, is_throw: bool = False):
        """GK distributes the ball."""
        direction = vec3_normalize(Vec3(target_pos.x - self.position.x, 0,
                                         target_pos.z - self.position.z))
        if is_throw:
            power = 18.0 * attr_to_multiplier(self.get_attr(PlayerAttribute.GK_KICKING)) * 0.6
            kick_dir = Vec3(direction.x, 0.15, direction.z)
        else:
            power = 30.0 * attr_to_multiplier(self.get_attr(PlayerAttribute.GK_KICKING))
            kick_dir = Vec3(direction.x, 0.4, direction.z)

        ball.kick(vec3_normalize(kick_dir), power, kicker=self, is_pass=True)
        ball.is_held = False
        ball.owner = None
        self.has_ball = False
        self._set_state(PlayerState.GK_KICKING, 0.5)

    def celebrate(self):
        self.celebration_type = random.randint(0, 5)
        self._set_state(PlayerState.CELEBRATING, ANIM_CELEBRATION_DURATION)
        self.velocity = Vec3(0, 0, 0)

    def _set_state(self, new_state: str, lock_duration: float = 0.0):
        self.previous_state = self.state
        self.state = new_state
        self.state_timer = 0.0
        if lock_duration > 0:
            self.state_locked = True
            self.lock_timer = lock_duration
        self.anim_timer = 0.0

    def update(self, dt: float):
        """Update player physics and state."""
        if self.is_sent_off:
            return

        # Update timers
        self.state_timer += dt
        self.anim_timer += dt

        if self.state_locked:
            self.lock_timer -= dt
            if self.lock_timer <= 0:
                self.state_locked = False
                self.lock_timer = 0
                if self.state in [PlayerState.SLIDE_TACKLING, PlayerState.GK_DIVING]:
                    self._set_state(PlayerState.GETTING_UP, 0.3)
                elif self.state == PlayerState.GETTING_UP:
                    self._set_state(PlayerState.IDLE)
                elif self.state != PlayerState.GK_HOLDING:
                    self._set_state(PlayerState.IDLE)

        # Tackle cooldown
        if self.tackle_cooldown > 0:
            self.tackle_cooldown -= dt

        # GK recovery
        if self.gk_recovery_timer > 0:
            self.gk_recovery_timer -= dt

        # Stamina
        self._update_stamina(dt)

        # Skill move
        if self.state == PlayerState.SKILL_MOVE:
            self.skill_move_timer -= dt
            self._execute_skill_move(dt)

        # Slide tackle movement
        if self.state == PlayerState.SLIDE_TACKLING:
            speed = TACKLE_SLIDE_SPEED * (1.0 - self.state_timer / TACKLE_SLIDE_DURATION)
            self.velocity = Vec3(
                self.slide_direction.x * speed,
                0,
                self.slide_direction.z * speed
            )

        # GK Dive movement
        elif self.state == PlayerState.GK_DIVING:
            dive_progress = self.state_timer / GK_DIVE_DURATION
            speed = GK_DIVE_SPEED * (1.0 - dive_progress)
            self.velocity = Vec3(
                self.dive_direction.x * speed,
                0,
                self.dive_direction.z * speed
            )
            self.jump_height = math.sin(dive_progress * math.pi) * 0.8

        # Normal movement
        elif not self.state_locked:
            self._update_movement(dt)

        # Power charging
        if self.is_charging:
            self.power_charge += SHOOT_POWER_CHARGE_RATE * dt / SHOOT_POWER_MAX
            self.power_charge = min(1.0, self.power_charge)

        # Jumping
        if self.is_jumping:
            self.jump_timer -= dt
            jump_progress = 1.0 - max(0, self.jump_timer) / HEADER_JUMP_DURATION
            self.jump_height = math.sin(jump_progress * math.pi) * HEADER_JUMP_HEIGHT
            jumping_attr = self.get_attr(PlayerAttribute.JUMPING)
            self.jump_height *= attr_to_multiplier(jumping_attr)
            if self.jump_timer <= 0:
                self.is_jumping = False
                self.jump_height = 0

        # Apply velocity
        self.position = Vec3(
            self.position.x + self.velocity.x * dt,
            0,
            self.position.z + self.velocity.z * dt
        )

        # Keep on field (with some margin for GK)
        margin = 5.0 if self.is_goalkeeper else 2.0
        self.position = Vec3(
            clamp(self.position.x, -FIELD_HALF_LENGTH - margin, FIELD_HALF_LENGTH + margin),
            0,
            clamp(self.position.z, -FIELD_HALF_WIDTH - margin, FIELD_HALF_WIDTH + margin)
        )

        # Distance tracking
        dist = vec3_distance_xz(self.position, self.last_position)
        self.distance_covered += dist
        self.last_position = Vec3(self.position.x, 0, self.position.z)

        # Update animations
        self._update_animation(dt)

        # Update entity
        self._update_entity()

    def _update_stamina(self, dt: float):
        """Update stamina based on activity."""
        speed = vec3_length_xz(self.velocity)
        if self.is_sprinting and speed > PLAYER_JOG_SPEED:
            self.stamina -= STAMINA_SPRINT_DRAIN * dt
        elif speed > PLAYER_WALK_SPEED:
            self.stamina -= STAMINA_RUN_DRAIN * dt
        elif speed < PLAYER_WALK_SPEED * 0.5:
            self.stamina += STAMINA_RECOVERY_WALKING * dt
        else:
            self.stamina += STAMINA_RECOVERY_RATE * dt

        self.stamina = clamp(self.stamina, 0, STAMINA_MAX)
        self.stamina_depleted = self.stamina < STAMINA_LOW_THRESHOLD

    def _update_movement(self, dt: float):
        """Update player movement based on input direction."""
        move_len = vec3_length_xz(self.move_direction)
        if move_len > 0.1:
            max_speed = self.get_max_speed()
            target_vel = Vec3(
                self.move_direction.x / move_len * max_speed,
                0,
                self.move_direction.z / move_len * max_speed
            )

            accel = PLAYER_ACCELERATION
            acceleration_attr = self.get_attr(PlayerAttribute.ACCELERATION)
            accel *= attr_to_multiplier(acceleration_attr)

            self.velocity = Vec3(
                self.velocity.x + (target_vel.x - self.velocity.x) * min(1, accel * dt),
                0,
                self.velocity.z + (target_vel.z - self.velocity.z) * min(1, accel * dt),
            )

            # Update facing
            target_angle = vec3_angle_xz(self.move_direction)
            turn_speed = PLAYER_TURN_SPEED_WITH_BALL if self.has_ball else PLAYER_TURN_SPEED
            agility = self.get_attr(PlayerAttribute.AGILITY)
            turn_speed *= attr_to_multiplier(agility)

            angle_diff = target_angle - self.facing_angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            self.facing_angle += angle_diff * min(1, turn_speed * dt)
            self.facing_direction = vec3_from_angle_xz(self.facing_angle)

            # State
            speed = vec3_length_xz(self.velocity)
            if self.has_ball:
                self.state = PlayerState.DRIBBLING
            elif self.is_sprinting and speed > PLAYER_RUN_SPEED:
                self.state = PlayerState.SPRINTING
            elif speed > PLAYER_WALK_SPEED:
                self.state = PlayerState.RUNNING
        else:
            # Decelerate
            decel = PLAYER_DECELERATION * dt
            speed = vec3_length_xz(self.velocity)
            if speed > decel:
                factor = (speed - decel) / speed
                self.velocity = Vec3(self.velocity.x * factor, 0, self.velocity.z * factor)
            else:
                self.velocity = Vec3(0, 0, 0)
                if not self.state_locked:
                    self.state = PlayerState.IDLE

    def _execute_skill_move(self, dt: float):
        """Execute the current skill move animation."""
        progress = 1.0 - self.skill_move_timer / DRIBBLE_SKILL_MOVE_DURATION

        if self.skill_move_type == 0:  # Step-over
            angle_offset = math.sin(progress * math.pi * 2) * 0.5
            self.facing_angle += angle_offset * dt * 5
        elif self.skill_move_type == 1:  # Body feint
            lateral = math.sin(progress * math.pi) * 2.0
            perp = vec3_rotate_y(self.facing_direction, math.pi / 2)
            self.velocity = Vec3(
                self.facing_direction.x * 3 + perp.x * lateral,
                0,
                self.facing_direction.z * 3 + perp.z * lateral
            )
        elif self.skill_move_type == 2:  # Roulette
            self.facing_angle += dt * 12
        elif self.skill_move_type == 3:  # Elastico
            wave = math.sin(progress * math.pi * 3) * 1.5
            perp = vec3_rotate_y(self.facing_direction, math.pi / 2)
            self.velocity = Vec3(
                self.facing_direction.x * 4 + perp.x * wave,
                0,
                self.facing_direction.z * 4 + perp.z * wave
            )
        elif self.skill_move_type == 4:  # Rainbow flick
            self.velocity = Vec3(
                self.facing_direction.x * 5,
                0,
                self.facing_direction.z * 5
            )
        elif self.skill_move_type == 5:  # Heel-to-heel
            speed_burst = 6.0 if progress > 0.5 else 2.0
            self.velocity = Vec3(
                self.facing_direction.x * speed_burst,
                0,
                self.facing_direction.z * speed_burst
            )

    def _update_animation(self, dt: float):
        """Update visual animation state."""
        speed = vec3_length_xz(self.velocity)

        if self.state in [PlayerState.RUNNING, PlayerState.SPRINTING, PlayerState.DRIBBLING]:
            anim_speed = speed * 3.0
            self.leg_anim_phase += anim_speed * dt
            leg_swing = math.sin(self.leg_anim_phase) * 25
            self.left_leg.rotation_x = leg_swing
            self.right_leg.rotation_x = -leg_swing

            # Arm swing (using body tilt)
            body_lean = math.sin(self.leg_anim_phase * 0.5) * 3
            self.entity.rotation_z = body_lean

        elif self.state == PlayerState.SLIDE_TACKLING:
            progress = self.state_timer / TACKLE_SLIDE_DURATION
            self.entity.rotation_x = lerp(0, 75, min(1, progress * 2))
            if progress > 0.5:
                self.entity.rotation_x = lerp(75, 0, (progress - 0.5) * 2)

        elif self.state == PlayerState.SHOOTING or self.state == PlayerState.PASSING:
            progress = self.state_timer / ANIM_KICK_DURATION
            if progress < 0.4:
                self.right_leg.rotation_x = lerp(0, -45, progress / 0.4)
            else:
                self.right_leg.rotation_x = lerp(-45, 30, (progress - 0.4) / 0.6)

        elif self.state == PlayerState.GK_DIVING:
            progress = self.state_timer / GK_DIVE_DURATION
            self.entity.rotation_z = lerp(0, 80, min(1, progress * 2))
            if self.dive_direction.z > 0.3:
                self.entity.rotation_z = -self.entity.rotation_z

        elif self.state == PlayerState.CELEBRATING:
            self._animate_celebration(dt)

        elif self.state == PlayerState.IDLE:
            self.left_leg.rotation_x = 0
            self.right_leg.rotation_x = 0
            self.entity.rotation_x = 0
            self.entity.rotation_z = 0
            # Subtle idle animation
            idle_bob = math.sin(self.anim_timer * 2) * 0.5
            self.entity.y = PLAYER_HEIGHT * 0.3 + idle_bob * 0.01

    def _animate_celebration(self, dt: float):
        """Animate goal celebration."""
        t = self.state_timer
        if self.celebration_type == 0:  # Knee slide
            if t < 1.0:
                self.entity.rotation_x = lerp(0, 30, t)
                slide_speed = 5.0 * (1.0 - t)
                self.velocity = Vec3(self.facing_direction.x * slide_speed, 0,
                                     self.facing_direction.z * slide_speed)
            else:
                self.velocity = Vec3(0, 0, 0)
        elif self.celebration_type == 1:  # Arms spread run
            self.velocity = Vec3(self.facing_direction.x * 4, 0, self.facing_direction.z * 4)
            self.entity.rotation_z = math.sin(t * 8) * 10
        elif self.celebration_type == 2:  # Backflip (jump)
            if t < 0.5:
                self.jump_height = math.sin(t / 0.5 * math.pi) * 2.0
                self.entity.rotation_x = t / 0.5 * 360
            else:
                self.jump_height = 0
                self.entity.rotation_x = 0
                self.velocity = Vec3(0, 0, 0)
        elif self.celebration_type == 3:  # Dance
            self.entity.rotation_y = math.sin(t * 6) * 30
            self.velocity = Vec3(0, 0, 0)
        else:  # Fist pump
            if t < 0.3:
                self.jump_height = math.sin(t / 0.3 * math.pi) * 0.5
            else:
                self.jump_height = 0
            self.velocity = Vec3(0, 0, 0)

    def _update_entity(self):
        """Sync 3D entities with physics state."""
        y_offset = PLAYER_HEIGHT * 0.3 + self.jump_height
        self.entity.position = Vec3(self.position.x, y_offset, self.position.z)
        self.entity.rotation_y = math.degrees(self.facing_angle)

        # Shadow
        self.shadow.position = Vec3(self.position.x, 0.005, self.position.z)

        # Selection arrow
        self.selection_arrow.position = Vec3(self.position.x, 2.8 + self.jump_height, self.position.z)
        if self.selection_arrow.enabled:
            self.selection_arrow.rotation_y += 180 * ursina_time.dt

        # Selection ring on ground (pulsing scale)
        self.selection_ring.position = Vec3(self.position.x, 0.02, self.position.z)
        if self.selection_ring.enabled:
            pulse = 1.0 + math.sin(self.anim_timer * 4) * 0.15
            ring_size = PLAYER_RADIUS * 5 * pulse
            self.selection_ring.scale = (ring_size, ring_size)

        # Indicator
        self.indicator.position = Vec3(self.position.x, 2.3 + self.jump_height, self.position.z)

    def get_ball_receive_position(self) -> Vec3:
        """Position where this player would receive a pass."""
        return Vec3(
            self.position.x + self.velocity.x * 0.3,
            PLAYER_HEIGHT * 0.3,
            self.position.z + self.velocity.z * 0.3
        )

    def can_reach_ball(self, ball_pos: Vec3, threshold: float = None) -> bool:
        if threshold is None:
            threshold = DRIBBLE_TOUCH_DISTANCE
        return vec3_distance_xz(self.position, ball_pos) < threshold

    def cleanup(self):
        for e in [self.entity, self.head, self.left_leg, self.right_leg,
                  self.indicator, self.selection_arrow, self.selection_ring, self.shadow]:
            try:
                e.disable()
            except Exception:
                pass
