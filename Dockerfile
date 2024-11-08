# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to avoid .pyc files and enable unbuffered output
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r ./app/requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run Streamlit when the container launches
CMD ["streamlit", "run", "interactive_stock_analysis.py"]
