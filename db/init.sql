PRAGMA foreign_keys = ON;

  -- rate_limit_B INTEGER DEFAULT -1,
  -- retries INTEGER DEFAULT 10,
  -- hls_prefer_native INTEGER DEFAULT 0,
  -- hls_prefer_ffmpeg INTEGER DEFAULT 0,
  -- hls_use_mpegts INTEGER DEFAULT 0
CREATE TABLE IF NOT EXISTS settings (
    version TEXT DEFAULT '',
    ytdl_version TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS quality (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO quality (name)
    VALUES
        ('best'),
        ('worst'),
        ('bestvideo'),
        ('worstvideo'),
        ('bestaudio'),
        ('worstaudio');

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
        ('Monthly', 30, 'Update approximately monthly');

CREATE TABLE IF NOT EXISTS video (
    id INTEGER PRIMARY KEY,
    youtube_id TEXT NOT NULL,
    url TEXT,
    quality INTEGER REFERENCES quality(id),
    size_B INTEGER
);

CREATE TABLE IF NOT EXISTS collection_setting (
    id INTEGER PRIMARY KEY,
    title_match_regex TEXT,
    title_reject_regex TEXT,
    playlist_start INTEGER DEFAULT 1,
    playlist_end INTEGER DEFAULT -1,
    playlist_elems TEXT
);

CREATE TABLE IF NOT EXISTS collection (
    id INTEGER PRIMARY KEY,
    youtube_id TEXT NOT NULL,
    type INTEGER REFERENCES collection_type(id),
    setting INTEGER REFERENCES collection_setting(id),
    youtube_name TEXT NOT NULL,
    friendly_name TEXT UNIQUE,
    start_date TEXT DEFAULT (datetime('now')),
    update_sched INTEGER REFERENCES update_sched(id)
);

CREATE TABLE IF NOT EXISTS video_collection_xref (
    video_id INTEGER REFERENCES video(id),
    collection_id INTEGER REFERENCES collection(id)
);
