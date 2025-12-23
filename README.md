# SmartNotesNotify

Minimal FastAPI + PostgreSQL (JSONB) board. The entrypoint exposes the `/new_note`, `/api/board/{user}`, and `/board/{user}` routes described in the MVP. The HTML board runs on port 9432 when started with the provided command.

## Quick start
1. Copy `.env.example` to `.env` and adjust `DATABASE_URL` to point at your Postgres instance.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server on port 9432:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 9432 --reload
   ```
   or set `DATABASE_URL` in the environment and run the same command without the `--reload` flag in production.

The project uses SQLAlchemy 2.0 declarative models; onboarding the database happens automatically on startup (including Postgres enums and `set_updated_at` triggers defined in `app/db.py`).

## Database schema highlights
- `users` with a unique `user_key`.
- `todo_lists` (frames) with position/size and automatic `updated_at`.
- `notes` with board coordinates, geo JSONB, LLM flags, notification hints, and board/list indexes.
- The `set_updated_at` trigger keeps `updated_at` current when raw updates occur.

## Running the board
With the server running, open `http://localhost:9432/board/<user_key>` to pan/zoom notes, drag them between frames, and trigger the placeholder LLM analysis via the HUD button. The board fetches `/api/board/{user}` for the latest state and saves position/TODO-list assignments through `/api/notes/{note_id}`.
