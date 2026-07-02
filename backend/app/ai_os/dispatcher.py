"""
Medical Board Dispatcher
"""


class Dispatcher:

    def build_board(self, capability):

        board = []

        for domain in capability.required_domains:
            board.append(domain)

        for domain in capability.optional_domains:
            board.append(domain)

        board.append("Evidence")

        board.append("Devils Advocate")

        return board