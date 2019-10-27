FROM python:alpine
WORKDIR /app
EXPOSE 8080
VOLUME ["/youtube-dl"]

RUN apk add --no-cache \
  ffmpeg \
  tzdata

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
CMD [ "python", "-u", "./youtube-dl-server.py" ]
