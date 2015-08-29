import random
import logging
import arrow
import services.serializers as serializers
from ttt import Board, ComputerPlayer, AbstractPlayer, AbstractGame

logger = logging.getLogger(__name__)

random.seed()


class NetworkException(Exception):
    pass


class ServiceException(Exception):
    pass


class Server(object):

    def __init__(self, twitter, storage):
        self._twitter = twitter
        self._storage = storage

        self._help_msg = '\n'.join([
            '',
            'Commands:',
            'START,NEW [X|O]',
            'SHOW,LAST',
            '1,2,3,4,5,6',
            'SCORE,STATS',
            'HELP',
            'VERSION'
        ])
        self._unknown_msg = 'I don\'t know that.' + self._help_msg
        self._commands = {
            'HELP': self._show_help,
            'SCORE': self._show_score,
            'STATS': self._show_score,
            'SHOW': self._show_board,
            'LAST': self._show_board,
            'START': self._start_game,
            'NEW': self._start_game,
            '1': self._player_move,
            '2': self._player_move,
            '3': self._player_move,
            '4': self._player_move,
            '5': self._player_move,
            '6': self._player_move,
            '7': self._player_move,
            '8': self._player_move,
            '9': self._player_move,
            'VERSION': self._show_version,
        }

    def main(self):
        self._loop_for_relevant_messages(self._process_message)

    def _loop_for_relevant_messages(self, func):

        break_count = 0
        while True:
            try:
                for msg in self._twitter.user_stream():
                    if 'hangup' in msg and msg['hangup'] is True:
                        break_count += 1
                        if break_count > 5:
                            raise NetworkException("Repeated Connection Failures")
                        break

                    break_count = 0

                    if 'event' in msg and msg['event'] == 'access_revoked':
                        raise ServiceException("Access to Stream Revoked")

                    if 'text' in msg:
                        if msg['retweeted'] is True:
                            continue
                        if msg['in_reply_to_screen_name'] != self._twitter.screen_name:
                            continue
                        if 'entities' in msg \
                                and 'user_mentions' in msg['entities'] \
                                and len(msg['entities']['user_mentions']) > 1:
                            continue

                        func(msg)
            except KeyboardInterrupt:
                logging.info("Shutdown signal caught, shutting down server")
                return
            except Exception as e:
                logging.exception(e)

    def _relevant_data(self, message):
        text = message['text'].upper()
        pieces = text.split(" ")
        cmd = pieces[1]
        args = pieces[2:]
        data = {
            'text': text,
            'cmd': cmd,
            'args': args,
            'person': message['user']['screen_name'],
            'id': message['id_str'],
            'lang': message['lang'],
            'in_reply_to': message['in_reply_to_screen_name'].lower(),
        }
        return data

    def _process_message(self, message):
        data = self._relevant_data(message)
        cmd = self._commands.get(data['cmd'], self._unknown_cmd)
        cmd(data, message)

    def _start_game(self, data, message):
        markers = ['X', 'O']
        game = self._storage.get_game(data['person'])
        reply = '\n'

        if game is not None:
            reply += "Game already in progress\n"
            return self._show_board(data, message, reply)

        if len(data['args']) > 0:
            if data['args'][0] not in markers:
                reply += "Invalid marker choice, try again"
                return self._send_reply(message, reply)
            else:
                human = data['args'][0]
        else:
            human = random.choice(markers)

        cpu = 'X' if human == 'O' else 'O'

        board = Board(9)
        computer = ComputerPlayer(cpu)
        if cpu == "X":
            move = computer.get_square(board, None, None)
            board.place(move, cpu)

        game = {
            'twitter_id': data['person'],
            'marker': human,
            'board': serializers.board_store(board),
            'computer_player': serializers.player_store(computer),
            'date_started': arrow.utcnow().datetime,
            'date_updated': arrow.utcnow().datetime
        }
        self._storage.put_game(game)

        reply += "You're %s" % game["marker"]
        reply += "\n" + self._pretty_board(board)

        self._send_reply(message, reply)

    def _player_move(self, data, message):
        game = self._storage.get_game(data['person'])
        reply = '\n'
        if game is None:
            reply += "No current game"
            return self._send_reply(message, reply)

        square = int(data['cmd']) - 1  # board is zero-based
        board = serializers.board_load(game['board'])
        if not board.square_free(square):
            reply += "Invalid square, pick again\n"
            return self._show_board(data, message, reply)

        human = AbstractPlayer(game['marker'])
        cpu = serializers.player_load(game['computer_player'])
        engine = AbstractGame(human, cpu)
        engine.board = board

        board.place(square, game["marker"])
        if engine.check_for_winner() or board.is_full():
            return self._handle_endgame(data, message, game, engine, board)

        move = cpu.get_square(board, square, None)
        board.place(move, cpu.marker)
        if engine.check_for_winner() or board.is_full():
            return self._handle_endgame(data, message, game, engine, board)

        game['board'] = serializers.board_store(board)
        game['computer_player'] = serializers.player_store(cpu)
        game['date_updated'] = arrow.utcnow().datetime
        self._storage.put_game(game)

        reply += "You're %s" % game["marker"]
        reply += "\n" + self._pretty_board(board)

        self._send_reply(message, reply)

    def _show_board(self, data, message, existing_reply=None):
        game = self._storage.get_game(data['person'])
        reply = '\n' if existing_reply is None else existing_reply

        if game is None:
            reply += "No current game"
            return self._send_reply(message, reply)

        board = serializers.board_load(game["board"])
        last = arrow.get(game['date_started']).humanize()

        reply += "You're %s" % game["marker"]
        reply += "\nLast move: %s" % last
        reply += "\n" + self._pretty_board(board)

        self._send_reply(message, reply)

    def _show_score(self, data, message):
        score = self._storage.get_score(data['person'])
        game = self._storage.get_game(data['person'])
        reply = '\n'

        if score is None:
            reply += "No games completed yet"
        else:
            last = arrow.get(score['date_updated']).humanize()

            reply += "W/L/D is %(win)d/%(lose)d/%(draw)d" % score
            reply += "\nLast finish: %s" % last

        if game is None:
            reply += "\nNo current game"
        else:
            reply += "\nGame in progress"

        self._send_reply(message, reply)

    def _show_help(self, data, message):
        self._send_reply(message, self._help_msg)

    def _show_version(self, data, message):
        self._send_reply(message, 'v0.2')

    def _unknown_cmd(self, data, message):
        self._send_reply(message, self._unknown_msg)

    def _pretty_board(self, board):
        pb = []

        for i in xrange(board.size):
            if not board.squares[i]:
                pb.append((i + 1))
            else:
                pb.append(board.squares[i])

        data = '\n'.join([
            ' %s | %s | %s' % tuple(pb[0:3]),
            '---+---+---',
            ' %s | %s | %s' % tuple(pb[3:6]),
            '---+---+---',
            ' %s | %s | %s' % tuple(pb[6:9]),
        ])

        rtn = ""
        for i, c in enumerate(data):
            if c == ' ':
                c = unichr(0x3000)
            elif c != '\n':
                c = unichr(0xFEE0 + ord(c))
            rtn += c

        return rtn

    def _handle_endgame(self, data, message, game, engine, board):
        score = self._storage.get_score(data['person'])
        reply = '\n'

        if score is None:
            score = {
                "twitter_id": data['person'],
                "win": 0,
                "lose": 0,
                "draw": 0,
            }

        if engine.check_for_winner() is None and board.is_full():
            score['draw'] += 1
            reply += "Draw, great game!"
        elif engine.check_for_winner() == game['marker']:
            score['win'] += 1
            reply += "You won, awesome!"
        else:
            score['lose'] += 1
            reply += "You lost, sorry!"

        reply += "\nW/L/D is %(win)d/%(lose)d/%(draw)d" % score
        reply += "\n" + self._pretty_board(board)

        score['date_updated'] = arrow.utcnow().datetime
        self._storage.put_score(score)
        self._storage.remove_game(game)

        self._send_reply(message, reply)

    def _send_reply(self, message, status):
        self._storage.add_message({
            'tweet_id': message['id_str'],
            'username': message['user']['screen_name'],
            'status': status
        })
