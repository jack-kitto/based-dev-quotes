FROM python:3.12-slim

WORKDIR /app

# Install only what we need
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts
COPY scripts/ /app/scripts/

# Bot needs the quotes data too
COPY quotes/ /app/quotes/

# Output dir for the static API
RUN mkdir -p /app/api

CMD ["python3", "scripts/telegram_bot.py"]
