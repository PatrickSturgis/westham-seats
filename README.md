# West Ham Season Tickets 2026/27

Two season tickets shared between three people across the 23 home league
games at London Stadium. Each row is a fixture, Seat 1 and Seat 2 are
dropdowns, notes is free text.

Runs on Streamlit Community Cloud. Seat claims are stored in a private
Hugging Face dataset repo, so they survive the app restarting.

## Running locally

```
pip install -r requirements.txt
streamlit run app.py
```

With no secrets configured it writes to `seats.csv` in the working
directory, so you can experiment without touching the shared data. To
point a local copy at the real data, copy `secrets.toml.example` to
`.streamlit/secrets.toml` and fill in the values.

## Configuration

Two secrets, set in the Streamlit Cloud app settings:

| Key | Value |
|---|---|
| `DATA_REPO` | the private HF dataset repo, e.g. `you/westham-seats-data` |
| `HF_TOKEN` | a Hugging Face token with write access |

## When a fixture moves

Edit `HOME_FIXTURES` in `fixtures.py`, push, then press **Re-sync
fixtures** in the app sidebar. Claims are matched on date plus opponent,
so a kick-off time change keeps them.

## Files

| File | What it is |
|---|---|
| `app.py` | The page: table, filters, save logic |
| `store.py` | Load and save, HF dataset or local file |
| `fixtures.py` | The 23 home fixtures |
| `requirements.txt` | Dependencies |
| `secrets.toml.example` | Template for the two secrets |
