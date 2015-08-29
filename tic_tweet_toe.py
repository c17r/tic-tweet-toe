import sys
import json
import logging
import daemonocle
from tic_tweet_toe import Server, Twitter, Storage, ReplyService


logging.basicConfig(
    filename="/var/log/tic_tweet_toe/ttt.log",
    level=logging.INFO,
    format="%(asctime)s : %(levelname)s : %(name)s : %(message)s"
)


jobs = []


def bootstrap():
    with open("secrets.txt", "r") as f:
        raw = f.read()
    config = json.loads(raw)

    jobs.append(ReplyService(config, sleep=1))

    for j in jobs:
        j.start()

    twitter = Twitter(**config)
    storage = Storage()

    server = Server(twitter, storage)
    server.main()


def cb_shutdown(message, code):
    logging.info("Shutdown signal triggered: %s - %s", code, message)
    for j in jobs:
        j.stop()


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        daemon = daemonocle.Daemon(
            worker=bootstrap,
            shutdown_callback=cb_shutdown,
            pidfile="/var/run/tic_tweet_toe/tic_tweet_toe.pid",
            workdir="."
        )
        daemon.do_action(sys.argv[1])
    else:
        bootstrap()
