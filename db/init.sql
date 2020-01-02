PRAGMA foreign_keys = ON;

  -- rate_limit_B INTEGER DEFAULT -1,
  -- retries INTEGER DEFAULT 10,
  -- hls_prefer_native INTEGER DEFAULT 0,
  -- hls_prefer_ffmpeg INTEGER DEFAULT 0,
  -- hls_use_mpegts INTEGER DEFAULT 0

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    version TEXT NOT NULL,
    YDL_OUTPUT_TEMPLATE TEXT NOT NULL,
    YDL_ARCHIVE_FILE TEXT NOT NULL,
    YDL_SERVER_HOST TEXT NOT NULL,
    YDL_SERVER_PORT INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS format_category (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL UNIQUE
);
INSERT INTO format_category (id, category)
    VALUES
        (0, 'Best'),
        (1, 'Video'),
        (2, 'Audio'),
        (3, 'Worst')
;

CREATE TABLE IF NOT EXISTS format (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES format_category(id),
    label TEXT NOT NULL,
    value TEXT NOT NULL UNIQUE
);
INSERT INTO format (category_id, label, value)
    VALUES
        (0, 'Default', '(bestvideo[vcodec^=av01][height>=1080][fps>30]/bestvideo[vcodec=vp9.2][height>=1080][fps>30]/bestvideo[vcodec=vp9][height>=1080][fps>30]/bestvideo[vcodec^=av01][height>=1080]/bestvideo[vcodec=vp9.2][height>=1080]/bestvideo[vcodec=vp9][height>=1080]/bestvideo[height>=1080]/bestvideo[vcodec^=av01][height>=720][fps>30]/bestvideo[vcodec=vp9.2][height>=720][fps>30]/bestvideo[vcodec=vp9][height>=720][fps>30]/bestvideo[vcodec^=av01][height>=720]/bestvideo[vcodec=vp9.2][height>=720]/bestvideo[vcodec=vp9][height>=720]/bestvideo[height>=720]/bestvideo)+(bestaudio[acodec=opus]/bestaudio)/best'),
        (0, 'Best', 'best'),
        (0, 'Best Audio', 'bestaudio'),
        (0, 'Best Video', 'bestvideo'),
        (1, 'MP4', 'mp4'),
        (1, 'Flash Video (FLV)', 'flv'),
        (1, 'WebM', 'webm'),
        (1, 'Ogg', 'ogg'),
        (1, 'Matroska (MKV)', 'mkv'),
        (1, 'AVI', 'avi'),
        (2, 'AAC', 'aac'),
        (2, 'FLAC', 'flac'),
        (2, 'MP3', 'mp3'),
        (2, 'M4A', 'm4a'),
        (2, 'Opus', 'opus'),
        (2, 'Vorbis', 'vorbis'),
        (2, 'WAV', 'wav'),
        (3, 'Worst', 'worst'),
        (3, 'Worst Video', 'worstvideo'),
        (3, 'Worst Audio', 'worstaudio')
;

CREATE TABLE IF NOT EXISTS collection_type (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO collection_type (name) VALUES ('Channel'), ('Playlist');

CREATE TABLE IF NOT EXISTS update_sched (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    frequency_d INTEGER NOT NULL,
    description TEXT
);
INSERT INTO update_sched (name, frequency_d, description)
    VALUES
        ('Never', 0, 'Never update'),
        ('Weekly', 7, 'Update weekly'),
        ('Monthly', 30, 'Update approximately monthly')
;

CREATE TABLE IF NOT EXISTS video (
    id INTEGER PRIMARY KEY,
    online_id TEXT NOT NULL,
    url TEXT,
    format_id INTEGER REFERENCES format(id),
    duration_s INTEGER,
    upload_date TEXT,
    download_datetime TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS collection_setting (
    id INTEGER PRIMARY KEY,
    title_match_regex TEXT,
    title_reject_regex TEXT,
    playlist_start INTEGER DEFAULT 1,
    playlist_end INTEGER DEFAULT -1
);

CREATE TABLE IF NOT EXISTS collection (
    id INTEGER PRIMARY KEY,
    type_id INTEGER REFERENCES collection_type(id),
    setting INTEGER REFERENCES collection_setting(id),
    update_sched INTEGER REFERENCES update_sched(id),
    online_id TEXT NOT NULL,
    online_title TEXT NOT NULL,
    custom_title TEXT UNIQUE,
    first_download_datetime TEXT DEFAULT (datetime('now')),
    last_download_datetime TEXT DEFAULT (datetime('now')),
    last_update_datetime TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS video_collection_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id),
    ordering_index INTEGER DEFAULT -1
);
