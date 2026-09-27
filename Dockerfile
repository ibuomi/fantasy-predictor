# Stage 1: build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: the actual runtime image - just Python + the built frontend
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 5000

# gunicorn instead of Flask's dev server for anything other than local
# development - the same `create_app()` factory serves both the API and
# the built frontend, exactly as `python run.py` does locally.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", "run:app"]
