from ttt.game import AbstractGame
from ttt.player import AbstractPlayer


class TwitterGame(AbstractGame):

    def __init__(self):
        super(TwitterGame, self).__init__(human, cpu)

    def display_board(self):
        pass

    def display_finale(self):
        pass


class TwitterHumanPlayer(AbstractPlayer):

    def __init__(self, marker, next_move, board):

        self.next_move = next_move
        super(TwitterHumanPlayer, self).__init__(marker)

    def get_square(self, current_board, previous_move, message):
        return self.next_move
