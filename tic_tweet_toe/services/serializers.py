import json
from ttt import Board, ComputerPlayer


class BoardSerializerException(Exception):
    pass


def board_load(board_json):
    data = json.loads(board_json)

    if 'size' not in data or 'squares' not in data:
        raise BoardSerializerException("Missing required properties")

    if type(data['size']) is not int:
        raise BoardSerializerException("Invalid size property: %s" % type(data['size']))

    if type(data['squares']) is not list:
        raise BoardSerializerException("Invalid squares property")

    if len(data['squares']) != data['size']:
        raise BoardSerializerException("Length of squares doesn't match size property")

    for idx, square in enumerate(data['squares']):
        if square not in [None, u'O', u'X']:
            raise BoardSerializerException("Invalid item in squares property")
        if square is not None:
            data['squares'][idx] = str(square)

    board = Board(data['size'])
    board.squares = data['squares'][:]

    return board


def board_store(board):
    data = {
        'size': board.size,
        'squares': board.squares[:]
    }
    return json.dumps(data)


class PlayerSerializerException(Exception):
    pass


def player_load(player_json):
    data = json.loads(player_json)

    player = ComputerPlayer(str(data['marker']))
    player.count = data['count']
    player.opp_moves = str(data['opp_moves'])

    if data['style'] == 1:
        player.style = player.first_player
    elif data['style'] == 2:
        player.style = player.second_player
    elif data['style'] is None:
        player.style = None
    else:
        raise PlayerSerializerException("Unknown Player Style")

    return player


def player_store(player):
    if player.style == player.first_player:
        style = 1
    elif player.style == player.second_player:
        style = 2
    elif player.style is None:
        style = None
    else:
        raise PlayerSerializerException("Unknown Player Style")

    data = {
        'count': player.count,
        'opp_moves': player.opp_moves,
        'marker': player.marker,
        'style': style
    }
    return json.dumps(data)
