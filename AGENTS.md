# Project instructions

- The application must work well on both mobile and desktop screens.
- After each completed large change, create a local git commit (no push) with a detailed commit message.
- Document the high-level structure: `app/main.py` for FastAPI setup, `app/routers/` + `services/`/`schemas/` for API logic, `app/models/` for SQLAlchemy schema, and `templates/` for the interactive board plus onboarding UI.
- Follow best practices consistently:
  - Keep routers thin by delegating DB work to services and reuse schemas.
  - Preserve the responsive board layout (HUD, pan/zoom, modals) in `templates/board.html`.
  - When touching data models or migrations, rely on FastAPI startup to recreate tables and triggers automatically.
