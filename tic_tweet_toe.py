import sys
import json
import logging
import argparse
import daemonocle
from tic_tweet_toe import Server, Twitter, Storage, ReplyService


_logger = logging.getLogger(__name__)


jobs = []


def bootstrap():
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        raw = f.read()
    config = json.loads(raw)

    jobs.append(ReplyService(config, args.db_file, sleep=1))

    for j in jobs:
        j.start()

    twitter = Twitter(**config)
    storage = Storage(args.db_file)

    server = Server(twitter, storage)
    server.main()


def cb_shutdown(message, code):
    _logger.info("Shutdown signal triggered: %s - %s", code, message)
    for j in jobs:
        j.stop()


parser = argparse.ArgumentParser()
parser.add_argument(
    'action',
    type=str,
    choices=['start', 'stop', 'restart', 'status', 'cli'],
)
parser.add_argument(
    '--pid-file',
    type=str,
    default='./tic_tweet_toe.pid',
)
parser.add_argument(
    '--log-file',
    type=str,
    default='./ttt.log',
)
parser.add_argument(
    '--db-file',
    type=str,
    default='./ttt_storage.db'
)
parser.add_argument(
    '--config-file',
    type=str,
    default='./secrets.txt'
)


if __name__ == "__main__":
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s : %(levelname)s : %(name)s : %(message)s"
    )

    if args.action != 'cli':
        daemon = daemonocle.Daemon(
            worker=bootstrap,
            shutdown_callback=cb_shutdown,
            pidfile=args.pid_file,
            workdir="."
        )
        daemon.do_action(args.action)
    else:
        bootstrap()
