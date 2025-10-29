# Dockerfile for discord_bot
# Uses a slim Python image, installs requirements if `requirements.txt` exists,
# copies the app and runs the bot entrypoint `main.py`.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps (some packages may need a compiler)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache if present
COPY requirements.txt ./

# Upgrade pip and install requirements if file exists
RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy the rest of the application
COPY . /app

# Default command - run the main bot file. Adjust if your entrypoint differs.
CMD ["fastapi", "main.py"]
