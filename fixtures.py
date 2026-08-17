"""West Ham United 2026/27 EFL Championship home fixtures.

Season ticket games only: the 23 league matches at London Stadium.
Kick-off times are as published at fixture release and will move for TV.
Edit this list if a game is rescheduled, then use "Re-sync fixtures"
in the app sidebar to fold the change into the live sheet without
losing any seat claims.
"""

# (ISO date, kick-off time, opponent)
HOME_FIXTURES = [
    ("2026-08-22", "15:00", "Charlton Athletic"),
    ("2026-09-01", "19:45", "Wolverhampton Wanderers"),
    ("2026-09-05", "15:00", "Derby County"),
    ("2026-09-11", "20:00", "Wrexham"),
    ("2026-10-10", "15:00", "Queens Park Rangers"),
    ("2026-10-24", "15:00", "Southampton"),
    ("2026-10-31", "15:00", "West Bromwich Albion"),
    ("2026-11-21", "15:00", "Preston North End"),
    ("2026-11-28", "15:00", "Stoke City"),
    ("2026-12-08", "19:45", "Middlesbrough"),
    ("2026-12-12", "15:00", "Bristol City"),
    ("2026-12-26", "15:00", "Norwich City"),
    ("2027-01-16", "15:00", "Swansea City"),
    ("2027-01-27", "19:45", "Cardiff City"),
    ("2027-01-30", "15:00", "Blackburn Rovers"),
    ("2027-02-16", "19:45", "Lincoln City"),
    ("2027-02-20", "15:00", "Millwall"),
    ("2027-03-06", "15:00", "Burnley"),
    ("2027-03-17", "19:45", "Sheffield United"),
    ("2027-04-03", "15:00", "Birmingham City"),
    ("2027-04-06", "19:45", "Bolton Wanderers"),
    ("2027-04-17", "15:00", "Watford"),
    ("2027-05-01", "12:30", "Portsmouth"),
]

# Who can hold a seat. "" means nobody has claimed it yet.
SHARERS = ["Patrick", "John", "Dave"]
SEAT_OPTIONS = ["", *SHARERS, "Guest", "Spare"]

COLUMNS = ["match_id", "date", "kickoff", "opponent", "seat_1", "seat_2", "notes"]


def match_id(date: str, opponent: str) -> str:
    """Stable key for a fixture, so re-syncing never orphans a claim."""
    return f"{date}|{opponent}"


def seed_rows():
    """The blank season, as a list of dicts."""
    return [
        {
            "match_id": match_id(date, opponent),
            "date": date,
            "kickoff": kickoff,
            "opponent": opponent,
            "seat_1": "",
            "seat_2": "",
            "notes": "",
        }
        for date, kickoff, opponent in HOME_FIXTURES
    ]
