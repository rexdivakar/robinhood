# Use the official Python runtime as a parent image
FROM python:3.11-slim AS base

# Update and install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to prevent .pyc files and to disable buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set up a non-root user to avoid root privileges
RUN useradd -ms /bin/bash appuser

# Set the working directory and switch to non-root user
WORKDIR /app
USER appuser

# Copy requirements.txt and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run Streamlit with the virtual environment
CMD ["/app/venv/bin/streamlit", "run", "interactive_stock_analysis.py"]
