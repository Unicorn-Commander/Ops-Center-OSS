# Build stage for React app
FROM node:20-alpine as frontend-build

WORKDIR /app

# Install bash (required for prebuild scripts)
RUN apk add --no-cache bash

# Copy package files
COPY package*.json ./
COPY scripts ./scripts
RUN npm install

# Copy source code
COPY src ./src
COPY public ./public
COPY index.html ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Build the React app (skip prebuild verification in Docker)
RUN npm run build:skip-verify

# Python backend stage
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    pciutils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/*.py ./
COPY backend/models ./models
COPY backend/database ./database
COPY backend/services ./services
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini

# Copy backend submodules — these are imported by server.py and must
# ship inside the image so the container runs without a host bind-mount.
# (Bind-mounts are still used in dev for hot-reload; this list mirrors
# the imports in server.py so a fresh build is self-contained.)
COPY backend/colonel ./colonel
COPY backend/routers ./routers
COPY backend/middleware ./middleware
COPY backend/observability ./observability
COPY backend/cache ./cache
COPY backend/billing ./billing
COPY backend/federation ./federation
COPY backend/local_inference ./local_inference
COPY backend/migrations ./migrations
COPY backend/model_adapters ./model_adapters
COPY backend/templates ./templates
COPY backend/email_templates ./email_templates
COPY backend/utils ./utils
COPY backend/config ./config
COPY backend/static ./static
COPY backend/sql ./sql
COPY backend/scripts ./scripts

# Copy built React app from frontend stage
COPY --from=frontend-build /app/dist ./dist

# Copy public files (including login.html)
COPY public ./public

# Expose port
EXPOSE 8084

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8084"]