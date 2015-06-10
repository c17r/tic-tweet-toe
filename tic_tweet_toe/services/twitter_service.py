import twitter as api


class TwitterServiceAuthenticationException(Exception):
    pass


class TwitterServiceNotConfigured(Exception):
    pass


class Twitter(object):

    def __init__(self, token, token_secret, consumer_key, consumer_secret):
        self.token = token
        self.token_secret = token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.auth = None
        self.screen_name = None
        self.twitter = None

        self._verify_credentials()

    def _verify_credentials(self):
        auth = api.OAuth(
            token=self.token,
            token_secret=self.token_secret,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
        )
        twitter = api.Twitter(auth=auth)
        try:
            profile = twitter.account.verify_credentials()
        except api.TwitterHTTPError as e:
            for err in e.response_data['errors']:
                if err['code'] == 89: # invalid token or credentials
                    raise TwitterServiceAuthenticationException
            raise

        self.auth = auth
        self.twitter = twitter
        self.screen_name = profile['screen_name']

    def _verify_configured(self):
        if self.auth is None:
            raise TwitterServiceNotConfigured

    def user_stream(self):
        self._verify_configured()

        stream = api.TwitterStream(auth=self.auth, domain='userstream.twitter.com')
        for msg in stream.user():
            yield msg

    def post_status(self, status):
        self._verify_configured()

        self.twitter.statuses.update(status=status)

    def post_reply(self, message, status):
        self._verify_configured()

        reply = '@' + message['user']['screen_name']
        if reply not in status:
            status = reply + ' ' + status

        self.twitter.statuses.update(in_reply_to_status_id=message['id_str'],
                                     status=status)
