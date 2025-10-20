# Build image
docker build -f Dockerfile -t fastaptamer3 .

# Run container
docker run -d -p 5000:5000 fastaptamer3