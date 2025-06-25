# Arivu Foods SCMS Architecture

This project adopts a minimal architecture to start development.

- **Frontend**: Static HTML/Bootstrap in `frontend/`. Uses fetch to call API.
- **Backend**: Flask app in `backend/` providing REST endpoints. Entry via `python -m backend.run`.
- **Database**: PostgreSQL (or SQLite for dev) using migrations in `db/migrations`.

```
[Browser] -> [Flask API] -> [Database]
```

Future revisions may introduce React or Vue and background workers.

