"""Storage layer for the West Ham season ticket tracker.

Two backends:

  HFBackend    reads and writes a CSV in a Hugging Face dataset repo.
               Used when HF_TOKEN and DATA_REPO are set, which is how
               the deployed Space runs.

  LocalBackend reads and writes a CSV on disk. Used for local testing
               and as a fallback so the app never hard-crashes.

Both return (DataFrame, revision). The revision is a content hash, used
to detect that someone else saved while you had the page open.
"""

from __future__ import annotations

import hashlib
import io
import os

import pandas as pd

from fixtures import COLUMNS, match_id, seed_rows

DATA_FILE = "seats.csv"


def _revision(df: pd.DataFrame) -> str:
    return hashlib.sha256(to_csv_bytes(df)).hexdigest()[:12]


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee the expected columns, types and ordering."""
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS].copy()
    for col in COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()
    # Backfill match_id for any row written by an older version.
    blank = df["match_id"] == ""
    if blank.any():
        df.loc[blank, "match_id"] = [
            match_id(d, o)
            for d, o in zip(df.loc[blank, "date"], df.loc[blank, "opponent"])
        ]
    return df.sort_values("date", kind="stable").reset_index(drop=True)


def seed_frame() -> pd.DataFrame:
    return _normalise(pd.DataFrame(seed_rows()))


def resync(current: pd.DataFrame) -> pd.DataFrame:
    """Fold the fixture list in fixtures.py into saved data.

    Dates and kick-off times are refreshed from the fixture list, claims
    and notes are kept, fixtures no longer in the list are dropped, and
    new fixtures arrive blank. Rows are matched on match_id, so changing
    a kick-off time keeps its claims but moving a game to a new date
    creates a new row.
    """
    current = _normalise(current)
    kept = current.set_index("match_id")[["seat_1", "seat_2", "notes"]].to_dict("index")
    fresh = seed_frame()
    for col in ("seat_1", "seat_2", "notes"):
        fresh[col] = [kept.get(mid, {}).get(col, "") for mid in fresh["match_id"]]
    return _normalise(fresh)


class LocalBackend:
    label = "local file"

    def __init__(self, path: str = DATA_FILE):
        self.path = path

    def load(self):
        if os.path.exists(self.path):
            df = _normalise(pd.read_csv(self.path, dtype=str, keep_default_na=False))
        else:
            df = seed_frame()
            self.save(df, "seed")
        return df, _revision(df)

    def save(self, df: pd.DataFrame, message: str = "update"):
        df = _normalise(df)
        with open(self.path, "wb") as handle:
            handle.write(to_csv_bytes(df))
        return _revision(df)


class HFBackend:
    label = "Hugging Face dataset"

    def __init__(self, repo_id: str, token: str):
        from huggingface_hub import HfApi

        self.repo_id = repo_id
        self.token = token
        self.api = HfApi(token=token)
        self.api.create_repo(
            repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True
        )

    def load(self):
        from huggingface_hub.errors import EntryNotFoundError

        try:
            path = self.api.hf_hub_download(
                repo_id=self.repo_id,
                filename=DATA_FILE,
                repo_type="dataset",
                force_download=True,
            )
            df = _normalise(pd.read_csv(path, dtype=str, keep_default_na=False))
        except EntryNotFoundError:
            df = seed_frame()
            self.save(df, "seed blank season")
        return df, _revision(df)

    def save(self, df: pd.DataFrame, message: str = "update"):
        df = _normalise(df)
        self.api.upload_file(
            path_or_fileobj=io.BytesIO(to_csv_bytes(df)),
            path_in_repo=DATA_FILE,
            repo_id=self.repo_id,
            repo_type="dataset",
            commit_message=message,
        )
        return _revision(df)


def setting(name: str) -> str:
    """Read config from Streamlit secrets, falling back to the environment.

    On Streamlit Community Cloud the values come from the app's Secrets
    box. Running locally they come from the environment, or from
    .streamlit/secrets.toml if you have made one.
    """
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:  # noqa: BLE001
        pass
    return os.environ.get(name, "").strip()


def get_backend():
    """Pick a backend from the config, falling back to a local file."""
    repo = setting("DATA_REPO")
    token = setting("HF_TOKEN")
    if repo and token:
        return HFBackend(repo, token)
    return LocalBackend()
