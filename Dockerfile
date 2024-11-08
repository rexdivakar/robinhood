# Use an official Python runtime based on Alpine
FROM python:3.11-alpine

# Set environment variables to avoid .pyc files and enable unbuffered output
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install dependencies for packages that may need compilation
RUN apk add --no-cache gcc musl-dev libffi-dev

# Copy the rest of the application code
COPY . .

# Install Python dependencies in a single layer
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Streamlit port
EXPOSE 8501

# Run Streamlit with the interactive analysis script
CMD ["streamlit", "run", "interactive_stock_analysis.py"]
