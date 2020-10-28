from vote import voting_system as vs
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
        return f'{self.__class__.__name__}(name={repr(self.name)}, electorate={repr(self.electorate)})'

    def _validate(self):
        electorate_error_msg = 'Electorate must be a positive integer.'
        name_error_msg = 'Name must be a truthy string.'

        if not isinstance(self.electorate, int):
            raise TypeError(electorate_error_msg)
        elif self.electorate <= 0:
            raise ValueError(electorate_error_msg)
        elif not isinstance(self.name, str):
            raise TypeError(name_error_msg)
        elif not self.name:
            raise ValueError(name_error_msg)

    def simulate_vote(self, method, candidates, n_seats=1):
        method = (method.lower() if isinstance(method, str) else None)
        func = methods.get(method)

        if func is not None:
            vote = vs.Vote.generate(
                candidates=candidates, n_votes=self.electorate)
            return func(vote, n_seats=n_seats)
        else:
            raise ValueError(f'''Invalid voting method "{str(method)}". Valid methods are "{'", "'.join(methods)}"''')

    @classmethod
    def generate(cls, lower_bound=1000, upper_bound=10000, name=None):
        electorate = rnd.randint(lower_bound, upper_bound)
        name = name if name else 'MyRegion'
        return cls(name=name, electorate=electorate)


class Country(Region):
    def __init__(self, name, *regions):
        self.regions = regions
        electorate = sum(region.electorate for region in regions)
        super().__init__(name=name, electorate=electorate)

    def __repr__(self):
        return f'{self.__class__.__name__}(name={repr(self.name)}, regions={repr(self.regions)})'

    def __iter__(self):
        return iter(self.regions)

    def __getitem__(self, s):
        return self.regions[s]

    @property
    def regions(self):
        return self._regions

    @regions.setter
    def regions(self, regions):
        not_regions = {region for region in regions if not isinstance(region, Region)}
        if not_regions:
            raise TypeError('Only a container of Regions are permitted for the region argument.')
        self._regions = regions

    def simulate_vote(self, method, candidates, n_seats=1):
        regional_winners = dict()

        for region in self.regions:
            regional_winner = region.simulate_vote(
                method=method, candidates=candidates, n_seats=n_seats)

            regional_winners[region.name] = regional_winner

        return regional_winners

    @classmethod
    def generate(cls, lower_bound=1000, upper_bound=10000, name=None, n_regions=5):
        regions = []

        for i in range(n_regions):
            r_name = 'MyRegion' + str(i + 1)

            region = Region.generate(
                lower_bound=lower_bound, upper_bound=upper_bound, name=r_name)

            regions.append(region)

        name = f'My{cls.__name__}' if not (isinstance(name, str) and name) else name

        return cls(f'{name}', *regions)
