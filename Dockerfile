FROM python:alpine
WORKDIR /app
EXPOSE 8080
VOLUME ["/app/db", "/app/downloaded"]
ENV YDL_DOCKER=1

RUN apk add --no-cache \
  ffmpeg \
  tzdata

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup -g 1000 -S ytdl && \
  adduser -u 1000 -S ytdl -G ytdl
USER ytdl

COPY --chown=ytdl . /app
CMD [ "python", "-u", "./youtube-dl-server.py" ]
