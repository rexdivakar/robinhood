# Robinhood

## Comamnds to run

### Build the container
```shell
docker build -t stock_analysis .
```

### Run the container
```shell
docker run -d -p 8501:8501 -v $(pwd):/app --name stock_analysis --restart unless-stopped stock_analysis:latest
```
