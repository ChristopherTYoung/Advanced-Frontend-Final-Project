FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . /app

CMD ["fastapi", "run", "main.py"]
