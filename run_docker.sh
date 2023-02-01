# build image
docker build -t ppocr-cpu .

# run container
docker run --name ppocr-cpu \
  -d --ulimit core=0 \
  -v /root/ocr-docker/images:/root/ocr-docker/images \
  -p 9000:8000 \
  ppocr-cpu

# view container
docker ps
