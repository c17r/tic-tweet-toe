import logging
from services import Storage, Twitter, StoppableProcess


_logger = logging.getLogger(__name__)


class ReplyService(StoppableProcess):
    _twitter = None
    _storage = None
    _config = None
    _db_path = None

    def __init__(self, config, db_path, *args, **kwargs):
        self._config = config
        self._db_path = db_path
        super(ReplyService, self).__init__(*args, **kwargs)

    def _setup(self):
        self._twitter = Twitter(**self._config)
        self._storage = Storage(db_path=self._db_path)

    def _teardown(self):
        msg = self.name + " shutting down"
        if self.exit.is_set():
            msg += ", via signal"
        _logger.info(msg)

    def _ping(self):
        reply = self._storage.get_first_message()
        if reply:
            self._twitter.post_reply(
                reply['tweet_id'],
                reply['username'],
                reply['status']
            )
            self._storage.remove_message(reply)
