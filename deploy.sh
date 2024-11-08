#!/bin/sh

# Build the Docker image
docker build -t robinhood .


# Run the Docker container
docker run -d -p 8501:8050 -v $(pwd):/app --name robinhood --restart unless-stopped robinhood:latest

