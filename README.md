# CodeAtlas

AI-Powered Software Codebase Archaeology & Architecture Intelligence Platform.

## Requirements
- Docker and Docker Compose
- Node.js 20+
- Python 3.11+
- Ollama (for local AI features)

## Setup Instructions

1. Clone the repository and navigate into the folder.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Start the services using Docker Compose:
   ```bash
   docker compose up --build -d
   ```
4. Verify the services are running:
   - Frontend: http://localhost:3000
   - API Health: http://localhost:8000/health

## Database Migrations

Because the initial schema setup requires an active database connection to reflect the models, you'll need to run Alembic autogenerate after Docker Compose is up:

1. Exec into the API container:
   ```bash
   docker compose exec api bash
   ```
2. Generate the initial migration:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```
3. Apply the migration:
   ```bash
   alembic upgrade head
   ```
