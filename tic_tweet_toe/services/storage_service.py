import sqlite3 as sql


def _dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Storage(object):

    def __init__(self, db_path=None):
        self._db_name = db_path or "ttt_storage.db"

        conn = sql.connect(self._db_name)
        with conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS version(id INTEGER);")
            cur.execute("SELECT IFNULL(MAX(id), 0) FROM version;")
            version = cur.fetchone()[0]

            if version <= 0:
                cur.executescript("""
                    CREATE TABLE score (
                      twitter_id TEXT PRIMARY KEY,
                      win INTEGER,
                      lose INTEGER,
                      draw INTEGER,
                      date_updated TIMESTAMP);

                    CREATE TABLE game (
                      twitter_id TEXT PRIMARY KEY,
                      marker TEXT,
                      board TEXT,
                      computer_player TEXT,
                      date_started TIMESTAMP,
                      date_updated TIMESTAMP);

                    INSERT INTO version VALUES (1);
                """)

            if version <= 1:
                cur.executescript("""
                    CREATE TABLE message (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tweet_id TEXT,
                        username TEXT,
                        status TEXT,
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

                    CREATE INDEX message_idx
                      on message (date_added ASC);

                    INSERT INTO version VALUES (2);
                """)

    def _get_conn(self):
        conn = sql.connect(
            self._db_name,
            detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES
        )
        conn.row_factory = _dict_factory
        return conn

    def _make_insert(self, table_name, record, modifier=None):
        sql = ''
        fields = ''
        vals = ''
        sep = ''

        for k in record.keys():
            fields += sep + k
            vals += sep + ':' + k
            sep = ', '

        sql = 'INSERT'
        if modifier:
            sql += ' OR ' + modifier
        sql += ' INTO %s (%s) values (%s)' % (table_name, fields, vals)
        return sql

    def get_score(self, twitter_id):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM score WHERE twitter_id = :twitter_id", {
                'twitter_id': twitter_id
            })
            return cur.fetchone()

    def put_score(self, record):
        with self._get_conn() as conn:
            cur = conn.cursor()
            stmt = self._make_insert("score", record, "REPLACE")
            cur.execute(stmt, record)

    def get_game(self, twitter_id):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM game WHERE twitter_id = :twitter_id', {
                'twitter_id': twitter_id
            })
            return cur.fetchone()

    def put_game(self, record):
        with self._get_conn() as conn:
            cur = conn.cursor()
            stmt = self._make_insert("game", record, "REPLACE")
            cur.execute(stmt, record)

    def remove_game(self, record):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM game WHERE twitter_id = :twitter_id",
                         record)

    def add_message(self, record):
        with self._get_conn() as conn:
            cur = conn.cursor()
            stmt = self._make_insert("message", record)
            cur.execute(stmt, record)

    def get_first_message(self):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM message ORDER BY date_added LIMIT 1")
            return cur.fetchone()

    def remove_message(self, record):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM message WHERE id = :id", record)
