import voting_system as vs
import random as rnd


methods = {
    'fptp': vs.first_past_the_post,
    'stv': vs.single_transferable_vote
}


class Region:
    def __init__(self, name, electorate):
        self.name = name
        self.electorate = electorate
        self._validate()

    def __repr__(self):
        return f'Region(name={repr(self.name)}, electorate={repr(self.electorate)})'

    def _validate(self):
        assert isinstance(self.electorate, int) and self.electorate > 0
        assert isinstance(self.name, str) and self.name

    def simulate_vote(self, method, candidates, n_seats=1):
        func = methods.get(method)

        if func is not None:
            vote = vs.Vote.generate(
                candidates=candidates, n_votes=self.electorate)
            return func(vote, n_seats=n_seats)
        else:
            raise ValueError(f'Unrecognised voting method "{str(method)}". Valid methods are {", ".join(methods)}')

    @classmethod
    def generate(cls, lower_bound=1000, upper_bound=10000, name=None):
        electorate = rnd.randint(lower_bound, upper_bound)
        name = name if name else 'MyRegion'
        return cls(name=name, electorate=electorate)


class Country(Region):
    def __init__(self, name, regions):
        self.regions = regions
        electorate = sum(region.electorate for region in regions)
        super().__init__(name=name, electorate=electorate)

    def __repr__(self):
        return f'Country(name={repr(self.name)}, regions={repr(self.regions)})'

    def __iter__(self):
        return iter(self.regions)

    def __getitem__(self, s):
        return self.regions[s]

    @property
    def regions(self):
        return self._regions

    @regions.setter
    def regions(self, regions):
        region_name_set = {region.name for region in regions}
        assert len(region_name_set) == len(regions)
        self._regions = regions

    def simulate_vote(self, method, candidates, n_seats=1):
        regional_winners = dict()

        for region in self.regions:
            regional_winner = region.simulate_vote(
                method=method, candidates=candidates, n_seats=n_seats)

            regional_winners[region.name] = regional_winner

        return regional_winners

    @classmethod
    def generate(cls, n_regions, regional_lower_bound, regional_upper_bound):
        regions = []

        for i in range(n_regions):
            name = 'MyRegion' + str(i + 1)

            region = Region.generate(
                lower_bound=regional_lower_bound, upper_bound=regional_upper_bound, name=name)

            regions.append(region)

        return cls('MyCountry', regions)
