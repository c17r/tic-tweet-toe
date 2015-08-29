from services import Storage, Twitter, StoppableProcess


class ReplyService(StoppableProcess):
    _twitter = None
    _storage = None
    _config = None

    def __init__(self, config, *args, **kwargs):
        self._config = config
        super(ReplyService, self).__init__(*args, **kwargs)

    def _setup(self):
        self._twitter = Twitter(**self._config)
        self._storage = Storage()

    def _ping(self):
        reply = self._storage.get_first_message()
        if reply:
            self._twitter.post_reply(
                reply['tweet_id'],
                reply['username'],
                reply['status']
            )
            self._storage.remove_message(reply)
