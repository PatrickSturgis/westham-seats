"""West Ham season ticket tracker for Patrick, John and Dave.

Two seats, 23 home games, one shared page. Pick your games, leave a note,
hit save. Everything is stored in a private Hugging Face dataset repo so
it survives the Space going to sleep.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from fixtures import SEAT_OPTIONS, SHARERS
from store import get_backend, resync

st.set_page_config(
    page_title="West Ham Season Tickets 2026/27",
    page_icon="⚽",
    layout="wide",
)

SEAT_COLS = ["seat_1", "seat_2"]
CLAIMED = set(SHARERS) | {"Guest"}

# Access is controlled by the Streamlit Community Cloud viewer list, so
# there is no passcode here. Only invited email addresses can load the app
# at all.


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

@st.cache_resource
def backend():
    return get_backend()


def load(force: bool = False):
    """Put the saved sheet into session state."""
    if force or "df" not in st.session_state:
        df, revision = backend().load()
        st.session_state.df = df
        st.session_state.revision = revision


def pretty_date(iso: str) -> str:
    return pd.to_datetime(iso).strftime("%a %-d %b %Y")


def today_iso() -> str:
    return pd.Timestamp.today().normalize().strftime("%Y-%m-%d")


# ----------------------------------------------------------------------
# Layout
# ----------------------------------------------------------------------

load()
df = st.session_state.df

st.title("⚽ West Ham Season Tickets 2026/27")
st.caption(
    "Two seats shared between Patrick, John and Dave. "
    "23 home league games at London Stadium. "
    "Change a dropdown, then press Save."
)

# --- Sidebar -----------------------------------------------------------

with st.sidebar:
    st.subheader("Season so far")

    tally = {name: 0 for name in [*SHARERS, "Guest", "Spare"]}
    for col in SEAT_COLS:
        for value in df[col]:
            if value in tally:
                tally[value] += 1

    total_seats = len(df) * 2
    taken = sum(tally[name] for name in CLAIMED)

    for name in SHARERS:
        st.metric(name, f"{tally[name]} seats")
    if tally["Guest"] or tally["Spare"]:
        st.caption(f"Guest: {tally['Guest']}  |  Spare: {tally['Spare']}")
    st.caption(f"{taken} of {total_seats} seats claimed")

    fair_share = total_seats / len(SHARERS)
    st.progress(min(taken / total_seats, 1.0))
    st.caption(f"An even split is about {fair_share:.0f} seats each.")

    st.divider()
    if st.button("Reload from server", use_container_width=True):
        load(force=True)
        st.rerun()

    with st.expander("Fixture changes"):
        st.write(
            "If a game gets moved for TV, edit fixtures.py in the Space "
            "and press this. Seat claims and notes are kept."
        )
        if st.button("Re-sync fixtures", use_container_width=True):
            merged = resync(st.session_state.df)
            st.session_state.revision = backend().save(merged, "re-sync fixtures")
            st.session_state.df = merged
            st.success("Fixture list re-synced.")
            st.rerun()

    st.divider()
    st.caption(f"Storage: {backend().label}")

# --- Filters -----------------------------------------------------------

left, right = st.columns([1, 1])
with left:
    view_mode = st.radio(
        "Show",
        ["Upcoming games", "Whole season", "Unclaimed seats only"],
        horizontal=True,
        label_visibility="collapsed",
    )

visible = df
if view_mode == "Upcoming games":
    visible = df[df["date"] >= today_iso()]
elif view_mode == "Unclaimed seats only":
    visible = df[(df["seat_1"] == "") | (df["seat_2"] == "")]

if visible.empty:
    st.info("Nothing to show with that filter.")
    st.stop()

# --- Table -------------------------------------------------------------

view = visible.copy()
view["when"] = [pretty_date(d) for d in view["date"]]
view["fixture"] = view["opponent"] + "  (" + view["kickoff"] + ")"

edited = st.data_editor(
    view,
    column_order=["when", "fixture", "seat_1", "seat_2", "notes"],
    column_config={
        "when": st.column_config.TextColumn("Date", disabled=True, width="small"),
        "fixture": st.column_config.TextColumn(
            "Opponent", disabled=True, width="medium"
        ),
        "seat_1": st.column_config.SelectboxColumn(
            "Seat 1", options=SEAT_OPTIONS, width="small"
        ),
        "seat_2": st.column_config.SelectboxColumn(
            "Seat 2", options=SEAT_OPTIONS, width="small"
        ),
        "notes": st.column_config.TextColumn(
            "Notes", width="large", help="Swaps, who owes who, parking, anything"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor",
)

# --- Save --------------------------------------------------------------

pending = edited.set_index("match_id")[["seat_1", "seat_2", "notes"]]
merged = df.set_index("match_id").copy()
merged.update(pending)
merged = merged.reset_index()[df.columns]
dirty = not merged.equals(df)

save_col, status_col = st.columns([1, 4])

with save_col:
    save_clicked = st.button(
        "Save changes",
        type="primary",
        disabled=not dirty,
        use_container_width=True,
    )

with status_col:
    if dirty:
        st.warning("You have unsaved changes.")
    else:
        st.success("Everything is saved.")

if save_clicked:
    latest, latest_revision = backend().load()
    if latest_revision != st.session_state.revision:
        st.session_state.pending = merged
        st.session_state.latest = latest
        st.error(
            "Someone else saved while this page was open. "
            "Choose which version to keep."
        )
    else:
        st.session_state.revision = backend().save(merged, "update seats")
        st.session_state.df = merged
        st.toast("Saved.")
        st.rerun()

if "pending" in st.session_state:
    keep_col, drop_col = st.columns(2)
    with keep_col:
        if st.button("Keep my changes and overwrite", use_container_width=True):
            merged = st.session_state.pop("pending")
            st.session_state.pop("latest", None)
            st.session_state.revision = backend().save(merged, "overwrite")
            st.session_state.df = merged
            st.rerun()
    with drop_col:
        if st.button("Discard mine and reload theirs", use_container_width=True):
            st.session_state.pop("pending", None)
            st.session_state.pop("latest", None)
            load(force=True)
            st.rerun()

# --- Next game ---------------------------------------------------------

upcoming = df[df["date"] >= today_iso()]
if not upcoming.empty:
    nxt = upcoming.iloc[0]
    holders = [s for s in (nxt["seat_1"], nxt["seat_2"]) if s]
    who = " and ".join(holders) if holders else "nobody yet"
    st.divider()
    st.caption(
        f"Next up: {nxt['opponent']} on {pretty_date(nxt['date'])} "
        f"at {nxt['kickoff']}. Going: {who}."
    )
