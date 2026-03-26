"""
Ultimate Soccer 3D - Tournament System
League, cup, and knockout tournament modes.
"""
import random
from teams_data import TEAMS, get_team


class TournamentMatch:
    """Represents a scheduled match in a tournament."""
    def __init__(self, home_id: str, away_id: str, round_num: int = 0):
        self.home_id = home_id
        self.away_id = away_id
        self.round_num = round_num
        self.home_score = None
        self.away_score = None
        self.played = False
        self.extra_time = False
        self.penalties = False
        self.penalty_home = 0
        self.penalty_away = 0

    @property
    def winner(self):
        if not self.played:
            return None
        if self.penalties:
            return self.home_id if self.penalty_home > self.penalty_away else self.away_id
        if self.home_score > self.away_score:
            return self.home_id
        elif self.away_score > self.home_score:
            return self.away_id
        return None  # Draw

    @property
    def loser(self):
        w = self.winner
        if w == self.home_id:
            return self.away_id
        elif w == self.away_id:
            return self.home_id
        return None

    def set_result(self, home_score, away_score, penalties=None):
        self.home_score = home_score
        self.away_score = away_score
        self.played = True
        if penalties:
            self.penalties = True
            self.penalty_home, self.penalty_away = penalties

    def __repr__(self):
        if self.played:
            home_name = TEAMS.get(self.home_id, {}).get('short_name', self.home_id)
            away_name = TEAMS.get(self.away_id, {}).get('short_name', self.away_id)
            score = f"{self.home_score}-{self.away_score}"
            if self.penalties:
                score += f" (pen {self.penalty_home}-{self.penalty_away})"
            return f"{home_name} {score} {away_name}"
        else:
            home_name = TEAMS.get(self.home_id, {}).get('short_name', self.home_id)
            away_name = TEAMS.get(self.away_id, {}).get('short_name', self.away_id)
            return f"{home_name} vs {away_name}"


class LeagueStanding:
    """League table entry."""
    def __init__(self, team_id: str):
        self.team_id = team_id
        self.played = 0
        self.won = 0
        self.drawn = 0
        self.lost = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def points(self):
        return self.won * 3 + self.drawn

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

    @property
    def team_name(self):
        return TEAMS.get(self.team_id, {}).get('short_name', self.team_id)

    def update(self, goals_for, goals_against):
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
        elif goals_for < goals_against:
            self.lost += 1
        else:
            self.drawn += 1


class League:
    """Round-robin league tournament."""

    def __init__(self, team_ids: list):
        self.team_ids = list(team_ids)
        self.standings = {tid: LeagueStanding(tid) for tid in self.team_ids}
        self.fixtures = []
        self.current_matchday = 0
        self.matchdays = []
        self._generate_fixtures()

    def _generate_fixtures(self):
        """Generate round-robin fixtures."""
        teams = list(self.team_ids)
        if len(teams) % 2 != 0:
            teams.append(None)  # Bye

        n = len(teams)
        matchdays = []

        for round_num in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                home = teams[i]
                away = teams[n - 1 - i]
                if home and away:
                    match = TournamentMatch(home, away, round_num)
                    round_matches.append(match)
                    self.fixtures.append(match)
            matchdays.append(round_matches)

            # Rotate teams (keep first team fixed)
            teams.insert(1, teams.pop())

        # Second leg (reverse fixtures)
        for round_num, md in enumerate(list(matchdays)):
            reverse_round = []
            for m in md:
                rev = TournamentMatch(m.away_id, m.home_id, round_num + len(matchdays))
                reverse_round.append(rev)
                self.fixtures.append(rev)
            matchdays.append(reverse_round)

        self.matchdays = matchdays

    def get_next_match(self) -> TournamentMatch:
        """Get the next unplayed match."""
        for match in self.fixtures:
            if not match.played:
                return match
        return None

    def record_result(self, match: TournamentMatch, home_score: int, away_score: int):
        """Record a match result."""
        match.set_result(home_score, away_score)
        self.standings[match.home_id].update(home_score, away_score)
        self.standings[match.away_id].update(away_score, home_score)

    def get_table(self) -> list:
        """Get sorted league table."""
        table = list(self.standings.values())
        table.sort(key=lambda s: (s.points, s.goal_difference, s.goals_for), reverse=True)
        return table

    def is_finished(self) -> bool:
        return all(m.played for m in self.fixtures)

    def get_champion(self) -> str:
        if not self.is_finished():
            return None
        table = self.get_table()
        return table[0].team_id if table else None


class KnockoutCup:
    """Single-elimination knockout tournament."""

    def __init__(self, team_ids: list):
        self.team_ids = list(team_ids)
        random.shuffle(self.team_ids)

        # Pad to power of 2
        while len(self.team_ids) & (len(self.team_ids) - 1) != 0:
            self.team_ids.append(None)

        self.rounds = []
        self.current_round = 0
        self._generate_first_round()

    def _generate_first_round(self):
        """Generate first round matches."""
        matches = []
        for i in range(0, len(self.team_ids), 2):
            home = self.team_ids[i]
            away = self.team_ids[i + 1]
            if home and away:
                matches.append(TournamentMatch(home, away, 0))
            elif home:
                # Bye - auto advance
                m = TournamentMatch(home, home, 0)
                m.set_result(1, 0)
                matches.append(m)
            elif away:
                m = TournamentMatch(away, away, 0)
                m.set_result(1, 0)
                matches.append(m)
        self.rounds.append(matches)

    def get_next_match(self) -> TournamentMatch:
        """Get next unplayed match in current round."""
        if self.current_round >= len(self.rounds):
            return None
        for m in self.rounds[self.current_round]:
            if not m.played:
                return m

        # All played in current round - generate next round
        self._advance_round()
        if self.current_round < len(self.rounds):
            for m in self.rounds[self.current_round]:
                if not m.played:
                    return m
        return None

    def record_result(self, match: TournamentMatch, home_score: int, away_score: int,
                       penalties: tuple = None):
        """Record a cup match result. Must have a winner (penalties if draw)."""
        if home_score == away_score and not penalties:
            # Simulate penalties
            penalties = self._simulate_penalties()
        match.set_result(home_score, away_score, penalties)

    def _simulate_penalties(self) -> tuple:
        """Simulate a penalty shootout."""
        home = 0
        away = 0
        for i in range(5):
            if random.random() > 0.25:
                home += 1
            if random.random() > 0.25:
                away += 1
        while home == away:
            if random.random() > 0.25:
                home += 1
            if random.random() > 0.25:
                away += 1
            if home != away:
                break
            # Sudden death continues
        return home, away

    def _advance_round(self):
        """Generate next round from winners."""
        if self.current_round >= len(self.rounds):
            return

        current_matches = self.rounds[self.current_round]
        if not all(m.played for m in current_matches):
            return

        winners = [m.winner for m in current_matches if m.winner]
        if len(winners) <= 1:
            self.current_round += 1
            return

        next_matches = []
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                next_matches.append(TournamentMatch(
                    winners[i], winners[i + 1], self.current_round + 1
                ))
            else:
                # Odd number - bye
                m = TournamentMatch(winners[i], winners[i], self.current_round + 1)
                m.set_result(1, 0)
                next_matches.append(m)

        self.rounds.append(next_matches)
        self.current_round += 1

    def is_finished(self) -> bool:
        if not self.rounds:
            return False
        last_round = self.rounds[-1]
        return len(last_round) == 1 and last_round[0].played

    def get_champion(self) -> str:
        if not self.is_finished():
            return None
        return self.rounds[-1][0].winner

    def get_round_name(self) -> str:
        total_teams = len(self.team_ids)
        remaining = max(1, total_teams >> self.current_round)
        if remaining <= 2:
            return "FINAL"
        elif remaining <= 4:
            return "SEMI-FINAL"
        elif remaining <= 8:
            return "QUARTER-FINAL"
        elif remaining <= 16:
            return "ROUND OF 16"
        else:
            return f"ROUND {self.current_round + 1}"
