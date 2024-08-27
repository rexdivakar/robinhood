#!/bin/sh

# Build the Docker image
docker build -t streamlit-stock-analysis .


# Run the Docker container
docker run -d --name robinhood -p 8501:8501 streamlit-stock-analysis

