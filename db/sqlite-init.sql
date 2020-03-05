PRAGMA foreign_keys = ON;

  -- rate_limit_B INTEGER DEFAULT -1,
  -- retries INTEGER DEFAULT 10,
  -- hls_prefer_native INTEGER DEFAULT 0,
  -- hls_prefer_ffmpeg INTEGER DEFAULT 0,
  -- hls_use_mpegts INTEGER DEFAULT 0

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),      -- allow only 1 row
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
        (1, 'Best'),
        (2, 'Video'),
        (3, 'Audio'),
        (4, 'Worst')
;

CREATE TABLE IF NOT EXISTS format (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES format_category(id),
    label TEXT NOT NULL,
    value TEXT NOT NULL UNIQUE
);
INSERT INTO format (category_id, label, value)
    VALUES
        (1, 'Default', '(bestvideo[vcodec^=av01][height>=1080][fps>30]/bestvideo[vcodec=vp9.2][height>=1080][fps>30]/bestvideo[vcodec=vp9][height>=1080][fps>30]/bestvideo[vcodec^=av01][height>=1080]/bestvideo[vcodec=vp9.2][height>=1080]/bestvideo[vcodec=vp9][height>=1080]/bestvideo[height>=1080]/bestvideo[vcodec^=av01][height>=720][fps>30]/bestvideo[vcodec=vp9.2][height>=720][fps>30]/bestvideo[vcodec=vp9][height>=720][fps>30]/bestvideo[vcodec^=av01][height>=720]/bestvideo[vcodec=vp9.2][height>=720]/bestvideo[vcodec=vp9][height>=720]/bestvideo[height>=720]/bestvideo)+(bestaudio[acodec=opus]/bestaudio)/best'),
        (1, 'Best', 'best'),
        (1, 'Best Audio', 'bestaudio'),
        (1, 'Best Video', 'bestvideo'),
        (2, 'MP4', 'mp4'),
        (2, 'Flash Video (FLV)', 'flv'),
        (2, 'WebM', 'webm'),
        (2, 'Ogg', 'ogg'),
        (2, 'Matroska (MKV)', 'mkv'),
        (2, 'AVI', 'avi'),
        (3, 'AAC', 'aac'),
        (3, 'FLAC', 'flac'),
        (3, 'MP3', 'mp3'),
        (3, 'M4A', 'm4a'),
        (3, 'Opus', 'opus'),
        (3, 'Vorbis', 'vorbis'),
        (3, 'WAV', 'wav'),
        (4, 'Worst', 'worst'),
        (4, 'Worst Video', 'worstvideo'),
        (4, 'Worst Audio', 'worstaudio')
;

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

CREATE TABLE IF NOT EXISTS extractor (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    pretty_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS video (
    id INTEGER PRIMARY KEY,
    online_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    extractor_id INTEGER REFERENCES extractor(id),
    format_id INTEGER REFERENCES format(id),
    duration_s INTEGER,
    upload_date TEXT,
    download_datetime TEXT DEFAULT (datetime('now')),
    filepath TEXT,
    filepath_exists INTEGER DEFAULT 0 CHECK (filepath_exists = 0 OR filepath_exists = 1),
    filepath_last_checked TEXT,
    UNIQUE (online_id, extractor_id)
);

CREATE TABLE IF NOT EXISTS collection_type (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO collection_type (name) VALUES ('Channel'), ('Playlist');

CREATE TABLE IF NOT EXISTS collection_setting (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    title_match_regex TEXT DEFAULT '.*',
    title_reject_regex TEXT DEFAULT '',
    playlist_start INTEGER DEFAULT 1,
    playlist_end INTEGER DEFAULT -1
);
INSERT INTO collection_setting (title, description) VALUES ('Everything', 'Match everything');

CREATE TABLE IF NOT EXISTS collection (
    id INTEGER PRIMARY KEY,
    type_id INTEGER REFERENCES collection_type(id),
    setting INTEGER DEFAULT 1 REFERENCES collection_setting(id),
    update_sched_id INTEGER DEFAULT 1 REFERENCES update_sched(id),
    extractor_id INTEGER REFERENCES extractor(id),
    online_id TEXT NOT NULL,
    online_title TEXT NOT NULL,
    custom_title TEXT,
    url TEXT,
    first_download_datetime TEXT DEFAULT (datetime('now')),
    last_download_datetime TEXT DEFAULT (datetime('now')),
    last_update_datetime TEXT DEFAULT (datetime('now')),
    UNIQUE (online_id, extractor_id)
);

-- Every video should belong to a channel
-- Even if downloaded as standalone, the channel/owner
-- collection should be recorded here
CREATE TABLE IF NOT EXISTS video_owner_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id),
    PRIMARY KEY (video_id, collection_id)
);

-- Every non-standalone video should additionaly be
-- associated with a collection here
CREATE TABLE IF NOT EXISTS video_collection_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id),
    ordering_index INTEGER DEFAULT -1,
    PRIMARY KEY (video_id, collection_id)
);

CREATE TABLE IF NOT EXISTS download_in_progress (
    video_id INTEGER REFERENCES video(id),
    start_datetime TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (video_id)
);

CREATE TABLE IF NOT EXISTS download_failed (
    video_id INTEGER REFERENCES video(id),
    last_fail_datetime TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (video_id)
);


-- Views

DROP VIEW IF EXISTS all_download;
CREATE VIEW all_download AS
    SELECT
        v.id AS video_id,
        download_datetime AS datetime,
        e.pretty_name AS extractor,
        url,
        title,
        (v.id IN (SELECT video_id FROM download_in_progress)) AS in_progress,
        (v.id IN (SELECT video_id FROM download_failed)) AS failed
    FROM video AS v
        LEFT JOIN extractor AS e ON v.extractor_id = e.id
    ORDER BY download_datetime DESC
;

DROP VIEW IF EXISTS download_queue;
CREATE VIEW download_queue AS
    SELECT *
    FROM all_download
    WHERE
        in_progress = 1
        AND failed = 0
;

DROP VIEW IF EXISTS download_history;
CREATE VIEW download_history AS
    SELECT *
    FROM all_download
    WHERE
        in_progress = 0
        AND failed = 0
;
