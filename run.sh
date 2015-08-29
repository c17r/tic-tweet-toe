#!/usr/bin/env bash

/home/tic_tweet_toe/run/current/venv/bin/python \
    /home/tic_tweet_toe/run/current/src/tic_tweet_toe.py \
    $1 \
    --pid-file /home/tic_tweet_toe/run/tic-tweet-toe.pid \
    --log-file /home/tic_tweet_toe/run/tic-tweet-toe.log \
    --db-file /home/tic_tweet_toe/run/ttt_storage.db \
    --config-file /home/tic_tweet_toe/run/secrets.txt
