FROM python:alpine
WORKDIR /app
EXPOSE 8080
ENV YDL_SERVER_DOCKER=1

RUN apk add --no-cache \
  ffmpeg \
  tzdata

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup -g 1000 -S ytdl && \
  adduser -u 1000 -S ytdl -G ytdl && \
  chown -R ytdl:ytdl /app
USER ytdl

# Make the directories so that ownership is correct
RUN mkdir -p /app/db /app/downloaded /app/static/video
VOLUME ["/app/db", "/app/downloaded", "/app/static/video"]

COPY --chown=ytdl . /app
CMD [ "python", "-u", "-m", "youtube_dl_subscribed" ]
