import unittest
from vote import voting_system as vs, region as r


class TestRegion(unittest.TestCase):

    def test_validation_on_initialisation(self):
        with self.assertRaises(TypeError):
            r.Region(name=1, electorate=1)

        with self.assertRaises(ValueError):
            r.Region(name='', electorate=1)

        with self.assertRaises(TypeError):
            r.Region(name='Hello', electorate=1.0)

        with self.assertRaises(ValueError):
            r.Region(name='Hello', electorate=-10)

        my_region = r.Region(name='Hello', electorate=10)

        self.assertEqual(my_region.name, 'Hello')
        self.assertEqual(my_region.electorate, 10)

    def test_repr(self):
        my_region = r.Region("Velen", 20000)

        self.assertEqual(repr(my_region), "Region(name='Velen', electorate=20000)")

    def test_generate(self):
        lower_bound, upper_bound = 100, 250

        my_region = r.Region.generate(
            lower_bound=lower_bound, upper_bound=upper_bound)

        self.assertEqual(type(my_region), r.Region)
        self.assertGreaterEqual(my_region.electorate, lower_bound)
        self.assertLessEqual(my_region.electorate, upper_bound)

    def test_valid_simulate_vote(self):
        my_region = r.Region('ARegion', 1000)

        result = my_region.simulate_vote('fptp', candidates=2, n_seats=1)

        self.assertEqual(type(result), vs.Result)

        result = my_region.simulate_vote('stv', candidates=3, n_seats=2)

        self.assertEqual(type(result), vs.Result)

    def test_invalid_simulate_vote_method(self):
        my_region = r.Region('ARegion', 1000)

        with self.assertRaises(ValueError):
            my_region.simulate_vote('invalid', candidates=2, n_seats=1)


class TestCountry(unittest.TestCase):

    def test_repr(self):
        my_region1 = r.Region("Velen", 20000)
        my_region2 = r.Region("Karhide", 100000)
        my_country = r.Country("FarAway", my_region1, my_region2)

        self.assertEqual(repr(my_country), f"Country(name='FarAway', regions=({repr(my_region1)}, {repr(my_region2)}))")

    def test_electorate_attr(self):
        my_region1 = r.Region("Velen", 20000)
        my_region2 = r.Region("Karhide", 100000)
        my_country = r.Country("FarAway", my_region1, my_region2)

        self.assertEqual(my_country.electorate, 20000 + 100000)

    def test_regions_attr(self):
        my_region1 = r.Region("Velen", 20000)
        my_region2 = ("Karhide", 100000)

        with self.assertRaises(TypeError):
            r.Country("FarAway", my_region1, my_region2)

    def test_is_sequence_type(self):
        my_region1 = r.Region("Velen", 20000)
        my_region2 = r.Region("Karhide", 100000)
        my_country = r.Country("FarAway", my_region1, my_region2)

        self.assertEqual(my_country[0], my_region1)

    def test_generate(self):
        n_regions = 3
        regional_lower_bound = 1150
        regional_upper_bound = 1250

        my_country = r.Country.generate(
            n_regions=n_regions,
            lower_bound=regional_lower_bound,
            upper_bound=regional_upper_bound)

        self.assertEqual(type(my_country), r.Country)

        self.assertEqual(len(my_country.regions), n_regions)

        for region in my_country:
            self.assertGreaterEqual(region.electorate, regional_lower_bound)
            self.assertLessEqual(region.electorate, regional_upper_bound)

    def test_simulate_vote(self):
        n_regions = 3
        regional_lower_bound = 1150
        regional_upper_bound = 1250

        my_country = r.Country.generate(
            n_regions=n_regions,
            lower_bound=regional_lower_bound,
            upper_bound=regional_upper_bound)

        results = my_country.simulate_vote('fptp', ['Harry', 'Barry'], n_seats=1)

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), n_regions)

        self.assertIsInstance(results[my_country[0].name], vs.Result)
        self.assertIsInstance(results[my_country[1].name], vs.Result)
        self.assertIsInstance(results[my_country[2].name], vs.Result)
