PRAGMA foreign_keys = ON;

  -- rate_limit_B INTEGER DEFAULT -1,
  -- retries INTEGER DEFAULT 10,
  -- hls_prefer_native INTEGER DEFAULT 0,
  -- hls_prefer_ffmpeg INTEGER DEFAULT 0,
  -- hls_use_mpegts INTEGER DEFAULT 0

CREATE TABLE IF NOT EXISTS setting (
    id INTEGER PRIMARY KEY CHECK (id = 1),      -- allow only 1 row
    version TEXT NOT NULL,
    YDL_SERVER_PROFILE INTEGER REFERENCES profile_setting(id) DEFAULT 1,
    YDL_SERVER_HOST TEXT NOT NULL,
    YDL_SERVER_PORT INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS format_category (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL
);
INSERT INTO format_category (id, category)
    VALUES
        (1, 'Best'),
        (2, 'Profile'),
        (3, 'Video'),
        (4, 'Audio'),
        (5, 'Worst')
;

CREATE TABLE IF NOT EXISTS format (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES format_category(id),
    label TEXT NOT NULL,
    value TEXT NOT NULL
);
INSERT INTO format (category_id, label, value)
    VALUES
        (1, 'Best', 'best'),
        (1, 'Best Video', 'bestvideo'),
        (1, 'Best Audio', 'bestaudio'),
        (2, 'Archival', '(bestvideo[vcodec^=av01][height>=1080][fps>30]/bestvideo[vcodec=vp9.2][height>=1080][fps>30]/bestvideo[vcodec=vp9][height>=1080][fps>30]/bestvideo[vcodec^=av01][height>=1080]/bestvideo[vcodec=vp9.2][height>=1080]/bestvideo[vcodec=vp9][height>=1080]/bestvideo[height>=1080]/bestvideo[vcodec^=av01][height>=720][fps>30]/bestvideo[vcodec=vp9.2][height>=720][fps>30]/bestvideo[vcodec=vp9][height>=720][fps>30]/bestvideo[vcodec^=av01][height>=720]/bestvideo[vcodec=vp9.2][height>=720]/bestvideo[vcodec=vp9][height>=720]/bestvideo[height>=720]/bestvideo)+(bestaudio[acodec=opus]/bestaudio)/best'),
        (3, 'MP4', 'mp4'),
        (3, 'Flash Video (FLV)', 'flv'),
        (3, 'WebM', 'webm'),
        (3, 'Ogg', 'ogg'),
        (3, 'Matroska (MKV)', 'mkv'),
        (3, 'AVI', 'avi'),
        (4, 'AAC', 'aac'),
        (4, 'FLAC', 'flac'),
        (4, 'MP3', 'mp3'),
        (4, 'M4A', 'm4a'),
        (4, 'Opus', 'opus'),
        (4, 'Vorbis', 'vorbis'),
        (4, 'WAV', 'wav'),
        (5, 'Worst', 'worst'),
        (5, 'Worst Video', 'worstvideo'),
        (5, 'Worst Audio', 'worstaudio')
;

CREATE TABLE IF NOT EXISTS profile_setting (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    default_format INTEGER REFERENCES format(id),
    YDL_OUTPUT_TEMPLATE TEXT NOT NULL,
    YDL_WRITE_SUB INTEGER CHECK (YDL_WRITE_SUB = 0 OR YDL_WRITE_SUB = 1),
    YDL_ALL_SUBS INTEGER CHECK (YDL_ALL_SUBS = 0 OR YDL_ALL_SUBS = 1),
    YDL_IGNORE_ERRORS INTEGER CHECK (YDL_IGNORE_ERRORS = 0 OR YDL_IGNORE_ERRORS = 1),
    YDL_CONTINUE_DL INTEGER CHECK (YDL_CONTINUE_DL = 0 OR YDL_CONTINUE_DL = 1),
    YDL_NO_OVERWRITES INTEGER CHECK (YDL_NO_OVERWRITES = 0 OR YDL_NO_OVERWRITES = 1),
    YDL_ADD_METADATA INTEGER CHECK (YDL_ADD_METADATA = 0 OR YDL_ADD_METADATA = 1),
    YDL_WRITE_DESCRIPTION INTEGER CHECK (YDL_WRITE_DESCRIPTION = 0 OR YDL_WRITE_DESCRIPTION = 1),
    YDL_WRITE_INFO_JSON INTEGER CHECK (YDL_WRITE_INFO_JSON = 0 OR YDL_WRITE_INFO_JSON = 1),
    YDL_WRITE_ANNOTATIONS INTEGER CHECK (YDL_WRITE_ANNOTATIONS = 0 OR YDL_WRITE_ANNOTATIONS = 1),
    YDL_WRITE_THUMBNAIL INTEGER CHECK (YDL_WRITE_THUMBNAIL = 0 OR YDL_WRITE_THUMBNAIL = 1),
    YDL_EMBED_THUMBNAIL INTEGER CHECK (YDL_EMBED_THUMBNAIL = 0 OR YDL_EMBED_THUMBNAIL = 1),
    YDL_SUB_FORMAT TEXT NOT NULL,
    YDL_EMBED_SUBS INTEGER CHECK (YDL_EMBED_SUBS = 0 OR YDL_EMBED_SUBS = 1),
    YDL_MERGE_OUTPUT_FORMAT TEXT NOT NULL,
    YDL_RECODE_VIDEO TEXT NOT NULL
);
INSERT INTO profile_setting VALUES (
    1,
    'Basic',
    (SELECT id FROM format WHERE label = 'Best'),
    './downloaded/basic/%(uploader)s/[%(upload_date)s] %(title)s.%(ext)s',
    1,      -- WRITE_SUB
    1,      -- ALL_SUBS
    1,      -- IGNORE_ERRORS
    0,      -- CONTINUE_DL
    1,      -- NO_OVERWRITES
    1,      -- ADD_METADATA
    0,      -- WRITE_DESCRIPTION
    0,      -- WRITE_INFO_JSON
    0,      -- WRITE_ANNOTATIONS
    0,      -- WRITE_THUMBNAIL
    1,      -- EMBED_THUMBNAIL
    'srt',  -- SUB_FORMAT
    1,      -- EMBED_SUBS
    'mkv',  -- MERGE_OUTPUT_FORMAT
    'mkv'   -- RECODE_VIDEO
);
INSERT INTO profile_setting VALUES (
    2,
    'Archival',
    (SELECT id FROM format WHERE label = 'Archival'),
    './downloaded/archival/%(extractor_key)s/%(upload_date)s %(title)s [%(id)s].%(ext)s',
    1,      -- WRITE_SUB
    1,      -- ALL_SUBS
    1,      -- IGNORE_ERRORS
    0,      -- CONTINUE_DL
    1,      -- NO_OVERWRITES
    1,      -- ADD_METADATA
    1,      -- WRITE_DESCRIPTION
    1,      -- WRITE_INFO_JSON
    1,      -- WRITE_ANNOTATIONS
    1,      -- WRITE_THUMBNAIL
    1,      -- EMBED_THUMBNAIL
    'srt',  -- SUB_FORMAT
    1,      -- EMBED_SUBS
    'mkv',  -- MERGE_OUTPUT_FORMAT
    'mkv'   -- RECODE_VIDEO
);
INSERT INTO profile_setting VALUES (
    3,
    'Plex',
    (SELECT id FROM format WHERE label = 'Best'),
    './downloaded/plex/%(uploader)s/%(title)s.%(ext)s',
    1,      -- WRITE_SUB
    1,      -- ALL_SUBS
    1,      -- IGNORE_ERRORS
    0,      -- CONTINUE_DL
    1,      -- NO_OVERWRITES
    1,      -- ADD_METADATA
    1,      -- WRITE_DESCRIPTION
    1,      -- WRITE_INFO_JSON
    1,      -- WRITE_ANNOTATIONS
    1,      -- WRITE_THUMBNAIL
    1,      -- EMBED_THUMBNAIL
    'srt',  -- SUB_FORMAT
    1,      -- EMBED_SUBS
    'mp4',  -- MERGE_OUTPUT_FORMAT
    'mp4'   -- RECODE_VIDEO
);

CREATE TABLE IF NOT EXISTS update_sched (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    frequency_d INTEGER NOT NULL,
    description TEXT,
    UNIQUE (name)
);
INSERT INTO update_sched (name, frequency_d, description)
    VALUES
        ('Never', 0, 'Never update'),
        ('Weekly', 7, 'Update weekly'),
        ('Monthly', 30, 'Update approximately monthly')
;

CREATE TABLE IF NOT EXISTS extractor (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    alt_name TEXT NOT NULL,
    UNIQUE (name)
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
    download_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    filepath TEXT,
    filepath_exists INTEGER DEFAULT 0 CHECK (filepath_exists = 0 OR filepath_exists = 1),
    filepath_last_checked TEXT,
    UNIQUE (online_id, extractor_id)
);

CREATE TABLE IF NOT EXISTS collection_type (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    UNIQUE (name)
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
    first_download_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    last_download_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    last_update_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE (online_id, extractor_id)
);

-- Every video should belong to a channel
-- Even if downloaded as standalone, the channel/owner
-- collection should be recorded here
CREATE TABLE IF NOT EXISTS video_owner_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id),
    PRIMARY KEY (video_id)
);

-- Every non-standalone video should additionaly be
-- associated with a collection here
CREATE TABLE IF NOT EXISTS video_collection_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id),
    ordering_index INTEGER DEFAULT -1,
    PRIMARY KEY (video_id, collection_id)
);

CREATE TABLE IF NOT EXISTS download_queued (
    video_id INTEGER REFERENCES video(id),
    not_before TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (video_id)
);

CREATE TABLE IF NOT EXISTS download_in_progress (
    video_id INTEGER REFERENCES video(id),
    start_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (video_id)
);

CREATE TABLE IF NOT EXISTS download_failed (
    video_id INTEGER REFERENCES video(id),
    error_text TEXT DEFAULT 'N/A',
    last_fail_datetime TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (video_id)
);


-- Views

DROP VIEW IF EXISTS video_details;
CREATE VIEW video_details AS
    SELECT
        v.id AS id,
        v.online_id AS online_id,
        v.title AS title,
        v.url AS url,
        v.duration_s AS duration_s,
        v.upload_date AS upload_date,
        v.download_datetime AS download_datetime,
        v.filepath AS filepath,
        v.filepath_exists AS filepath_exists,
        v.filepath_last_checked AS filepath_last_checked,
        c.id AS uploader_id,
        c.online_title AS uploader_name,
        c.url AS uploader_url,
        e.id AS extractor_id,
        e.name AS extractor,
        f.id AS format_id,
        f.label AS format_name,
        f.value AS format,
        (v.id IN (SELECT video_id FROM download_queued)) AS queued,
        (v.id IN (SELECT video_id FROM download_in_progress)) AS in_progress,
        (v.id IN (SELECT video_id FROM download_failed)) AS failed
    FROM video AS v
        LEFT JOIN extractor AS e ON v.extractor_id = e.id
        LEFT JOIN format AS f ON v.format_id = f.id
        LEFT JOIN video_owner_xref AS vo ON v.id = vo.video_id
        LEFT JOIN collection AS c ON vo.collection_id = c.id
    ORDER BY download_datetime DESC
;

DROP VIEW IF EXISTS collection_details;
CREATE VIEW collection_details AS
    SELECT
        c.id AS id,
        c.online_id AS online_id,
        c.online_title AS online_title,
        c.custom_title AS title,
        c.url AS url,
        c.first_download_datetime AS first_download_datetime,
        c.last_download_datetime AS last_download_datetime,
        c.last_update_datetime AS last_update_datetime,
        ct.id AS type_id,
        ct.name AS type,
        cs.id AS setting_id,
        cs.title AS setting_title,
        cs.description AS setting_description,
        u.id AS schedule_id,
        u.title AS schedule_title,
        u.description AS schedule_description,
        e.id AS extractor_id,
        e.name AS extractor
    FROM collection AS c
        LEFT JOIN connection_type AS ct ON c.type_id = t.id
        LEFT JOIN collection_setting AS cs ON c.setting_id = s.id
        LEFT JOIN update_sched AS u ON c.update_sched_id = u.id
        LEFT JOIN extractor AS e ON c.extractor = e.id
    ORDER BY title DESC
;

-- Testing/Research

CREATE TABLE IF NOT EXISTS _uploader_alternative (
    id INTEGER PRIMARY KEY,
    extractor TEXT,
    webpage_url TEXT,
    uploader_id TEXT,
    uploader TEXT,
    uploader_url TEXT,
    creator TEXT,
    channel_id TEXT,
    channel TEXT,
    channel_url TEXT,
    playlist_uploader_id, TEXT,
    playlist_uploader TEXT,
    artist TEXT,
    album_artist TEXT
);
