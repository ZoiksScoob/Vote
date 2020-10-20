class VoteError:
    def __init__(self):
        raise NotImplementedError


class RoundingError(VoteError):
    pass
