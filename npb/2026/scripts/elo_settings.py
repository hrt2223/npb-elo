"""Editable parameters shared by Elo rating and win-probability calculations."""

# Rating assigned to every team before its first game.
INITIAL_RATING = 1500.0

# Maximum rating adjustment per game.
K_FACTOR = 24.0

# Expected score = 1 / (1 + LOGISTIC_BASE ** (rating_difference / LOGISTIC_SCALE))
LOGISTIC_BASE = 10.0
LOGISTIC_SCALE = 1850.0

# Rating points added to the home team when calculating expected score.
HOME_ADVANTAGE = 28.0
