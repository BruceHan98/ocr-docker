FROM brucehan98/ppocr-cpu:latest

WORKDIR /ppocr

COPY app.py .

COPY server.py .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]