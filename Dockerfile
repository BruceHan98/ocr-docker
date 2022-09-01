FROM paddlepaddle/paddle:latest-dev

WORKDIR /ppocr

RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple

RUN pip config set install.trusted-host mirrors.aliyun.com

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY build .

COPY ppocr .

ENV GIT_SSL_NO_VERIFY=1

RUN /bin/sh ./tools/build.sh

RUN ln -s /ppocr/build/ppocr /usr/bin/ppocr

COPY note_utils.py .

COPY app.py .

COPY server.py .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
