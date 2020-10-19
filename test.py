import os
import unittest
import coverage
import region as r
import voting_system as vs


class TestRegion(unittest.TestCase):

    def test_generate(self):
        lower_bound, upper_bound = 100, 250

        my_region = r.Region.generate(
            lower_bound=lower_bound, upper_bound=upper_bound)

        self.assertEqual(type(my_region), r.Region)
        self.assertGreaterEqual(my_region.electorate, lower_bound)
        self.assertLessEqual(my_region.electorate, upper_bound)

    def test_simulate_vote(self):
        my_region = r.Region('Aregion', 1000)

        result = my_region.simulate_vote('fptp', candidates=2, n_seats=1)

        self.assertEqual(type(result), vs.Result)


class TestCountry(unittest.TestCase):

    def test_generate(self):
        n_regions = 3
        regional_lower_bound = 1150
        regional_upper_bonud = 1250

        my_country = r.Country.generate(
            n_regions=n_regions, regional_lower_bound=regional_lower_bound, regional_upper_bound=regional_upper_bonud)

        self.assertEqual(type(my_country), r.Country)

        self.assertEqual(len(my_country.regions), n_regions)

        for region in my_country:
            self.assertGreaterEqual(region.electorate, regional_lower_bound)
            self.assertLessEqual(region.electorate, regional_upper_bonud)


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
        votes = [[-1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]

        try:
            vs.Vote(votes=votes)
        except AssertionError:
            pass

        votes = [{1, 3}, [1, 2], [3, 2], [1], [2], [2], [3, 1]]

        try:
            vs.Vote(votes=votes)
        except AssertionError:
            pass

        votes = [[1, 3], ['A', 'C'], [3, 2], [1], [2], [2], [3, 1]]

        try:
            vs.Vote(votes=votes)
        except AssertionError:
            pass 

        votes = [[1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
        candidates = [1, 'B']

        try:
            vs.Vote(votes=votes, candidates=candidates)
        except AssertionError:
            pass

        votes = [[1, 3], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
        candidates = ['B', 'B']

        try:
            vs.Vote(votes=votes, candidates=candidates)
        except AssertionError:
            pass

        votes = [['A', 'C'], ['D', 'B'], ['C', 'B'], ['A'], ['B'], ['B']]
        candidates = ['A', 'B', 'C']

        try:
            vs.Vote(votes=votes, candidates=candidates)
        except AssertionError:
            pass

        votes = [[1, 2, 3, 4], [1, 2], [3, 2], [1], [2], [2], [3, 1]]
        candidates = ['A', 'B', 'C']

        try:
            vs.Vote(votes=votes, candidates=candidates)
        except AssertionError:
            pass


if __name__ == '__main__':
    cov = coverage.coverage(
        omit=['venv/*', '/usr/*', 'test.py']
    )
    cov.start()

    tests = unittest.TestLoader().discover('test')
    result = unittest.TextTestRunner(verbosity=2).run(tests)

    if result.wasSuccessful():
        cov.stop()
        cov.save()

        print('Coverage Summary:')
        cov.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        cov.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        cov.erase()
    else:
        print('Error in running tests.')
