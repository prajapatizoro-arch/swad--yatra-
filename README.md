# Swad Yatra

Swad Yatra is a deployable Python/Flask web app that preserves and discovers regional Indian heritage recipes. The user interface is plain HTML, CSS, and JavaScript in `public/`; `app.py` is the Python backend.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`.

## Deploy

Deploy on Render, Railway, Fly.io, or any Python 3.10+ host with:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Community submissions are stored in `data/submissions.json`, while uploaded videos are stored in `uploads/`. For a production host with ephemeral disk, attach persistent storage and mount both folders—or replace the small file store in `server.js` with Postgres/MongoDB and object storage.

On Render with a persistent disk mounted at `/var/data`, set `DATA_DIR=/var/data/data` and `UPLOAD_DIR=/var/data/uploads` in the service environment variables.
