import unittest
from vote import voting_system as vs, region as r


class TestRegion(unittest.TestCase):

    def test_generate(self):
        lower_bound, upper_bound = 100, 250

        my_region = r.Region.generate(
            lower_bound=lower_bound, upper_bound=upper_bound)

        self.assertEqual(type(my_region), r.Region)
        self.assertGreaterEqual(my_region.electorate, lower_bound)
        self.assertLessEqual(my_region.electorate, upper_bound)

    def test_simulate_vote(self):
        my_region = r.Region('ARegion', 1000)

        result = my_region.simulate_vote('fptp', candidates=2, n_seats=1)

        self.assertEqual(type(result), vs.Result)


class TestCountry(unittest.TestCase):

    def test_generate(self):
        n_regions = 3
        regional_lower_bound = 1150
        regional_upper_bound = 1250

        my_country = r.Country.generate(
            n_regions=n_regions, regional_lower_bound=regional_lower_bound, regional_upper_bound=regional_upper_bound)

        self.assertEqual(type(my_country), r.Country)

        self.assertEqual(len(my_country.regions), n_regions)

        for region in my_country:
            self.assertGreaterEqual(region.electorate, regional_lower_bound)
            self.assertLessEqual(region.electorate, regional_upper_bound)
