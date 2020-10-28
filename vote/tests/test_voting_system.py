import unittest
from vote import voting_system as vs


class TestVote(unittest.TestCase):

    def test_valid_init(self):
        votes = [[1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]

        a_vote = vs.Vote(votes=votes)

        self.assertEqual(type(a_vote), vs.Vote)

        a_vote = vs.Vote(votes=votes, candidates=['A', 'B', 'C'])

        self.assertEqual(type(a_vote), vs.Vote)

        votes = [['A', 'C'], ['A', 'B'], ['C', 'B'], ['A'], ['B'], ['B']]

        a_vote = vs.Vote(votes=votes, candidates=['A', 'B', 'C'])

        self.assertEqual(type(a_vote), vs.Vote)

    def test_invalid_init(self):
        with self.assertRaises(AssertionError) as cm:
            # Negative vote values
            votes = [[-1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
            vs.Vote(votes=votes)

        with self.assertRaises(AssertionError) as cm:
            # Unordered type
            votes = [{1, 3}, [1, 2], [3, 2], [1], [2], [2], [3, 1]]
            vs.Vote(votes=votes)

        with self.assertRaises(AssertionError) as cm:
            # Mixed types in votes
            votes = [[1, 3], ['A', 'C'], [3, 2], [1], [2], [2], [3, 1]]
            vs.Vote(votes=votes)

        with self.assertRaises(AssertionError) as cm:
            # Mixed types in candidates
            votes = [[1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
            candidates = [1, 'B']
            vs.Vote(votes=votes, candidates=candidates)

        with self.assertRaises(AssertionError) as cm:
            # Duplicate candidates
            votes = [[1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
            candidates = ['B', 'B']
            vs.Vote(votes=votes, candidates=candidates)

        with self.assertRaises(AssertionError) as cm:
            # Invalid candidate chosen in vote - str
            votes = [['A', 'C'], ['D', 'B'], ['C', 'B'], ['A'], ['B'], ['B']]
            candidates = ['A', 'B', 'C']
            vs.Vote(votes=votes, candidates=candidates)

        with self.assertRaises(AssertionError) as cm:
            # Invalid candidate chosen in vote - int
            votes = [[1, 2, 3, 4], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
            candidates = ['A', 'B', 'C']
            vs.Vote(votes=votes, candidates=candidates)



        votes = [[1, 2, 3, 4], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
        candidates = ['A', 'B', 'C']

        try:
            vs.Vote(votes=votes, candidates=candidates)
        except AssertionError:
            pass
