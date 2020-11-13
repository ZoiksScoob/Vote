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


class TestFirstPastThePost(unittest.TestCase):
    def test_return_result_class(self):
        votes = (5 * [1]) + (4 * [2]) + (30 * [3])
        my_vote = vs.Vote(votes=votes)
        my_result = vs.first_past_the_post(my_vote)

        self.assertIsInstance(my_result, vs.Result)

        types = {type(winner) for winner in my_result}

        self.assertEqual(len(types), 1)
        self.assertIs(types.pop(), vs.Winner)

        self.assertTrue(hasattr(my_result[0], 'name'))
        self.assertTrue(hasattr(my_result[0], 'n_votes'))

    def test_select_correct_winner(self):
        votes = (5 * [1]) + (4 * [2]) + (30 * [3])
        my_vote = vs.Vote(votes=votes)
        my_result = vs.first_past_the_post(my_vote)

        self.assertFalse(my_result.is_tie)
        self.assertEquals(len(my_result), 1)

        self.assertEquals(my_result[0].name, 'candidate_3')
        self.assertEquals(my_result[0].n_votes, 30)

    def test_handle_tie(self):
        votes = (5 * [1]) + (30 * [2]) + (30 * [3])
        my_vote = vs.Vote(votes=votes)
        my_result = vs.first_past_the_post(my_vote)

        self.assertTrue(my_result.is_tie)
        self.assertAlmostEqual(len(my_result.winners), 2)


class TestSingleTransferableVote(unittest.TestCase):
    def test_return_result_class(self):
        votes = (5 * [1]) + (4 * [2]) + (30 * [3])
        my_vote = vs.Vote(votes=votes)
        my_result = vs.single_transferable_vote(my_vote)

        self.assertIsInstance(my_result, vs.Result)

        types = {type(winner) for winner in my_result}

        self.assertEqual(len(types), 1)
        self.assertIs(types.pop(), vs.Winner)

        self.assertTrue(hasattr(my_result[0], 'name'))
        self.assertTrue(hasattr(my_result[0], 'n_votes'))

    def test_select_correct_single_winner(self):
        votes = (5 * [1]) + (4 * [2]) + (30 * [3])
        my_vote = vs.Vote(votes=votes)
        my_result = vs.single_transferable_vote(my_vote)

        self.assertFalse(my_result.is_tie)
        self.assertEquals(len(my_result), 1)

        self.assertEquals(my_result[0].name, 'candidate_3')
        self.assertEquals(my_result[0].n_votes, 30)

    def test_select_correct_single_runoff_winner(self):
        votes = 5 * [['Apple', 'Orange']] + 4 * [['Orange', 'Apple']] + 6 * [['Banana', 'Orange']]
        my_vote = vs.Vote(votes=votes)
        my_result = vs.single_transferable_vote(my_vote)

        self.assertFalse(my_result.is_tie)
        self.assertEquals(len(my_result), 1)
        self.assertEquals(my_result[0].name, 'Apple')
        self.assertEquals(my_result[0].n_votes, 9)

    def test_select_correct_multiple_winners(self):
        votes = 5 * [[1, 2]] + 3 * [[1, 3]] + 2 * [[2, 1]] + 2 * [[2, 3]] + 6 * [[3, 2]]
        my_vote = vs.Vote(votes=votes)
        my_result = vs.single_transferable_vote(my_vote, n_seats=2)

        self.assertFalse(my_result.is_tie)
        self.assertEquals(len(my_result), 2)
        self.assertEquals(my_result[0].name, 'candidate_1')
        self.assertEquals(my_result[0].n_votes, 8)
        self.assertEquals(my_result[1].name, 'candidate_3')
        self.assertEquals(my_result[1].n_votes, 8)
