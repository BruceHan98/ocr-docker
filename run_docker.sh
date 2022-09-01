# build image
docker build -t ppocr-cpu .

# run container
docker run --name ppocr-cpu \
  -d --ulimit core=0 \
  -v /home/devadmin/htx/ppocr-cpu-docker/ppocr/imgs:/home/devadmin/htx/ppocr-cpu-docker/ppocr/imgs \
  -p 9000:8000 \
  ppocr-cpu

# view container
docker ps