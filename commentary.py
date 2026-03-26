"""
Ultimate Soccer 3D - Commentary System
Dynamic text-based commentary that reacts to match events.
"""
import random
from config import GameState, SetPieceType, CardType


class Commentary:
    """Generates contextual commentary text for match events."""

    def __init__(self):
        self.last_event = None
        self.event_cooldown = 0.0
        self.min_interval = 3.0

        self.templates = {
            'goal': [
                "GOOOAL! {scorer} scores for {team}!",
                "What a strike! {scorer} finds the net!",
                "He's done it! {scorer} makes it {score}!",
                "BRILLIANT! {scorer} with a fantastic goal!",
                "The crowd goes wild! {scorer} scores!",
                "INCREDIBLE! {scorer} won't believe it! {score}!",
                "What a moment! {scorer} delivers for {team}!",
                "NET! {scorer} with the clinical finish!",
            ],
            'save': [
                "Great save by {player}!",
                "Superb stop from {player}!",
                "{player} denies the shot!",
                "Excellent reflexes from {player}!",
                "What a save! {player} keeps it out!",
                "{player} with a stunning save!",
            ],
            'parry': [
                "{player} parries it away!",
                "Can only palm it away, {player}!",
                "{player} pushes it to safety!",
                "Not held by {player}, parried wide!",
            ],
            'foul': [
                "Foul by {offender} on {victim}!",
                "{offender} brings down {victim}!",
                "The referee blows for a foul on {victim}!",
                "That's a foul! {offender} caught {victim}!",
                "Free kick! {offender} took out {victim}!",
            ],
            'yellow_card': [
                "Yellow card for {player}!",
                "{player} is booked! Yellow card!",
                "The referee shows yellow to {player}!",
                "That'll be a booking for {player}!",
                "Into the book goes {player}!",
            ],
            'red_card': [
                "RED CARD! {player} is sent off!",
                "{player} sees red! He's off!",
                "That's a straight red for {player}!",
                "The referee has no choice! Red card for {player}!",
            ],
            'second_yellow': [
                "Second yellow! {player} is off!",
                "Two yellows make a red! {player} is sent off!",
                "{player} picks up a second booking and is dismissed!",
            ],
            'penalty': [
                "PENALTY! The referee points to the spot!",
                "It's a penalty kick!",
                "The referee awards a penalty!",
                "Penalty to {team}! Huge moment!",
            ],
            'corner': [
                "Corner kick for {team}.",
                "It's a corner. {team} will deliver it.",
                "Corner coming in for {team}.",
            ],
            'goal_kick': [
                "Goal kick.",
                "That's a goal kick.",
                "The goalkeeper will restart with a goal kick.",
            ],
            'throw_in': [
                "Throw-in for {team}.",
                "{team} with the throw-in.",
            ],
            'offside': [
                "Offside! {player} was caught out!",
                "The flag goes up! {player} is offside!",
                "Offside against {player}!",
                "No goal! {player} was in an offside position!",
            ],
            'tackle': [
                "Great tackle by {player}!",
                "{player} wins the ball cleanly!",
                "Superb challenge from {player}!",
                "What a tackle! {player} dispossesses the attacker!",
            ],
            'shot_wide': [
                "Shot goes wide!",
                "Off target! Just wide of the post!",
                "He fires it wide! Close though!",
                "Misses the target! That was a good chance.",
            ],
            'shot_over': [
                "Over the bar!",
                "He blazes it over!",
                "Too high! Over the crossbar!",
            ],
            'crossbar': [
                "Off the crossbar!",
                "It hits the woodwork! So close!",
                "CROSSBAR! Can you believe it!",
                "Off the bar! Agonizing for the striker!",
            ],
            'post': [
                "Off the post!",
                "It rattles the post! So unlucky!",
                "POST! What a near miss!",
            ],
            'skill_move': [
                "Lovely skill!",
                "Beautiful footwork!",
                "What a move! Silky skills!",
                "He dances past the defender!",
            ],
            'through_ball': [
                "Brilliant through ball!",
                "What a pass! Threaded through!",
                "Inch-perfect through ball!",
            ],
            'cross': [
                "Cross coming in!",
                "He whips it in!",
                "Ball into the box!",
            ],
            'advantage': [
                "Advantage played by the referee!",
                "Play on! The referee plays advantage!",
                "Advantage! Let's see if it pays off!",
            ],
            'kickoff': [
                "And we're underway!",
                "The match begins!",
                "Kick off! Here we go!",
            ],
            'halftime': [
                "The referee blows for half time!",
                "That's the half! {home_score} - {away_score} at the break.",
                "Half time! The teams head to the dressing rooms.",
            ],
            'fulltime': [
                "It's all over! Full time!",
                "The final whistle blows! {home_score} - {away_score}!",
                "That's it! The match is over!",
            ],
            'possession': [
                "{team} controlling possession now.",
                "Good passing from {team}.",
                "{team} keeping the ball well.",
            ],
            'pressure': [
                "{team} applying pressure here!",
                "The defense is under siege!",
                "{team} looking dangerous in attack!",
            ],
            'counter_attack': [
                "Counter attack! {team} breaking fast!",
                "Quick break from {team}!",
                "On the counter! This could be dangerous!",
            ],
            'chance': [
                "Good chance here!",
                "This is a great opportunity!",
                "Dangerous moment!",
            ],
            'clearance': [
                "Cleared away!",
                "Good defensive clearance!",
                "Danger averted!",
            ],
            'interception': [
                "Well read! Good interception!",
                "Intercepted! Great anticipation!",
            ],
            'header': [
                "Header!",
                "He rises to meet it!",
                "Good header!",
                "Powerful header!",
            ],
            'long_range': [
                "He tries from distance!",
                "Long range effort!",
                "Ambitious shot from outside the box!",
            ],
            'injury_time': [
                "We're into added time!",
                "Injury time being played.",
                "{minutes} minutes of added time!",
            ],
        }

    def get_commentary(self, event_type: str, **kwargs) -> str:
        """Get a random commentary line for an event."""
        templates = self.templates.get(event_type, [])
        if not templates:
            return ""

        template = random.choice(templates)

        # Fill in placeholders
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template

    def update(self, dt: float):
        """Update commentary cooldown."""
        if self.event_cooldown > 0:
            self.event_cooldown -= dt

    def can_commentate(self) -> bool:
        return self.event_cooldown <= 0

    def on_event(self, event_type: str, **kwargs) -> str:
        """Process an event and return commentary if appropriate."""
        if not self.can_commentate() and event_type not in ['goal', 'red_card', 'penalty']:
            return ""

        text = self.get_commentary(event_type, **kwargs)
        if text:
            self.event_cooldown = self.min_interval
            self.last_event = event_type

        return text

    def get_ambient_commentary(self, match) -> str:
        """Generate ambient commentary based on match state."""
        if not self.can_commentate():
            return ""

        # Random ambient commentary
        if random.random() > 0.01:  # Very rare
            return ""

        options = []

        # Possession-based
        home_poss, away_poss = match.get_possession_stats()
        if home_poss > 60:
            options.append(self.get_commentary('possession', team=match.home_team.team_name))
        elif away_poss > 60:
            options.append(self.get_commentary('possession', team=match.away_team.team_name))

        # Score-based
        diff = abs(match.home_score - match.away_score)
        if diff >= 3:
            leading = match.home_team.team_name if match.home_score > match.away_score else match.away_team.team_name
            options.append(f"{leading} in commanding control!")

        # Time-based
        if match.match_minute > 80 and match.home_score == match.away_score:
            options.append("Can either side find a winner?")
        elif match.match_minute > 85 and match.home_score != match.away_score:
            trailing = match.home_team.team_name if match.home_score < match.away_score else match.away_team.team_name
            options.append(f"Time running out for {trailing}!")

        if options:
            text = random.choice(options)
            self.event_cooldown = self.min_interval * 2
            return text

        return ""
