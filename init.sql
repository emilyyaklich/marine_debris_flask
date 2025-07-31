
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT NOT NULL,
    gps TEXT NOT NULL,
    category TEXT NOT NULL,
    country TEXT NOT NULL);