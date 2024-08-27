#!/bin/sh

# Build the Docker image
docker build -t robinhood .


# Run the Docker container
docker run -d --name robinhood -p 8501:8501 --restart unless-stopped robinhood

