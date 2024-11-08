# Robinhood

## Comamnds to run

### Build the container
```shell
docker build -t robinhood .
```

### Run the container
```shell
docker run -d -p 8501:8050 -v $(pwd):/app --name robinhood --restart unless-stopped robinhood:latest
```
