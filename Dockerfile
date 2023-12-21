FROM python:3.6
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt Makefile /app/
RUN make install
COPY . /app

CMD make run
 