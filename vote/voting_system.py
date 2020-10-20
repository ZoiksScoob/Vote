import math
import warnings
import pandas as pd
import numpy as np
import random as rnd
from vote import exceptions as exc
from itertools import chain
from iteround import saferound


class Vote:
    """
    This class serves to aggregate a collection of votes
    ready for counting in a ballot.

    It can also be used to generate a set of votes for simulation.

    Args:
        votes:
                list/tuple of int/str
                or list/tuple of list/tuple(s) of int/str
            If a list/tuple of str/int then each item is considered as
            a single vote with one choice, otherwise each list/tuple item
            is considered a ranked vote, index 0 being 1st preference,
            with str values if the candidate names are provided,
            or int as an identifier, where the int is an index
            for the candidates.

        candidates:
                list/tuple of str
                default: None
            A list/tuple of names for the candidates.
            If strings are provided in the votes, and the candidates
            argument is not provided then this is constructed from the
            votes using .capitalized() form of the values.
    """

    def __init__(self, votes, candidates=None):
        self.votes = votes
        self.candidates = candidates
        self._validate()

    @property
    def votes(self):
        return self._votes

    @votes.setter
    def votes(self, votes):
        # Check if votes are lists/tuples of choices, i.e. ranked
        if any(isinstance(vote, (tuple, list)) for vote in votes):
            self._votes = votes
        # Otherwise assume we've been passed a list of single choices
        else:
            self._votes = [[vote] for vote in votes]

    def _validate(self):
        # Validate container constraint of votes
        container = (tuple, list)

        assert isinstance(self.votes, container)
        assert all(isinstance(vote, container) for vote in self.votes)

        # Check the votes are comprised of ints or strings
        choices = set(choice for choice in chain.from_iterable(self.votes))

        string_votes = all(isinstance(choice, str) for choice in choices)
        int_votes = all(isinstance(choice, int) for choice in choices)

        assert string_votes or int_votes

        # Handle candidates being supplied
        if self.candidates is not None:
            # Validate container constraint of candidates
            assert isinstance(self.candidates, container)

            # Check candidates are all strings with no duplicates
            assert all(isinstance(cand, str) for cand in self.candidates)
            assert len(self.candidates) == len(set(self.candidates))

            # Check no vote has too many choices
            assert len(self.candidates) >= max(len(v) for v in self.votes)

            # Check string votes are valid choices
            if string_votes:
                choices.issubset(set(self.candidates))
            # Or if int votes, check the range of values are valid indices
            else:
                assert min(choices) >= 0
                assert max(choices) <= len(self.candidates)

            self._agg_replace = True

        else:
            if string_votes:
                self.candidates = tuple(choices)
                self._agg_replace = True
            else:
                self.candidates = tuple(f'candidate_{i + 1}' for i in range(max(choices)))
                self._agg_replace = False

    def aggregate(self, manner='all'):
        """
        Arguments:
            manner - one of "all" if aggregating by all choices in
                     the votes, or "first" if only considering the
                     first choice.

        Returns:
            DataFrame of the form:

            choice | choice2 | choice3 | ... | n_votes
            ...

            Entries are int (float) / np.Nan, corresponding to
            index position of candidate in candidates attribute.

        Method to aggregate the votes into a dataframe for use in
        ballot functions.
        """
        manner = manner.lower() if isinstance(manner, str) else None
        assert manner in ('all', 'first')

        columns = [f'choice{i + 1 if i else ""}'
                   for i in range(len(self.candidates))]

        df = pd.DataFrame(self.votes, columns=columns)

        if manner == 'first':
            columns = ['choice']
            df = df[columns]

        df['n_votes'] = 1

        if self._agg_replace:
            replacements = {nm: i for (i, nm) in enumerate(self.candidates)}

            df.replace(replacements, inplace=True)

        df = df.fillna(-1).groupby(columns, as_index=False).sum()

        df.replace([-1], [np.NaN], inplace=True)

        return df

    @classmethod
    def generate(cls, candidates=5, n_votes: int = 1000):
        """
        Arguments:
            candidates - a non zero int or a list/tuple of
                non-zero int/str

            n_votes - a non-zero int

        This static method serves to produce a Vote class with
        a set of candidates and votes already generated.
        """
        assert n_votes > 0

        if isinstance(candidates, int):
            assert candidates > 0
            candidates = tuple(f'candidate_{i + 1}' for i in range(candidates))

        votes = [rnd.sample(candidates, rnd.randint(1, len(candidates)))
                 for i in range(n_votes)]

        return cls(votes=votes, candidates=candidates)


def first_past_the_post(vote: Vote, **kwargs):
    """
    Arguments:
        vote - an instance of the Vote class
        kwargs - scoops up other arguments to allow all voting
            funcs to be called in similar fashion.

    Returns:
        A list of dictionaries of the form
        [{'choice': <choice>, 'n_votes': <n_votes>}, ...]

    First Past the Post is a system where each voter has one vote,
    and the candidate with the most votes wins.
    This means if a vote from a voter has more than one choice,
    then only the 1st choice will be considered.
    """

    candidates = vote.candidates

    df = vote.aggregate('first')

    columns = ['choice', 'n_votes']

    mask_winner = (df.n_votes == df.n_votes.max())

    replacements = {i: cand for (i, cand) in enumerate(candidates)}

    winners = df[columns][mask_winner].replace(replacements).to_dict('records')

    return Result(winners)


def single_transferable_vote(vote: Vote, n_seats: int = 1, **kwargs):
    """
    Arguments:
        vote - an instance of the Vote class
        n_seats - an integer between 1 and the number of candidates (inclusive)
        kwargs - scoops up other arguments to allow all voting
            funcs to be called in similar fashion.

    Returns:
        A list of dictionaries of the form
        [{'choice': <choice>, 'n_votes': <n_votes>}, ...]

    Single Transferable Vote is a voting system where each voter ranks
    the candidates in order of preference.

    Candidates are selected as winners in a series of eliminations,
    starting with everyone's first choice, declaring anyone a winner
    who's number of votes exceeds the droop quota defined as

        floor( <# valid votes cast> / <# seats to fill + 1> ) + 1

    If not all seats are filled, then the process continues looping over the
    next 2 described steps until all seats are filled.

    1.) The surplus from the selected winners are transferred proportionally
    to their next choice and the next winners are selected. If all seats are
    filled then the vote is finished, otherwise go to step 2.

    2.) The candidate with the least number of votes is elminated and their
    votes are transferred proportionally to their next choice and the winners
    selected. If all seats are filled then the vote is finished then the vote
    is finished, otherwise go to step 1.

    There are some conditions that the votes need to meet, namely, as
    a winner is one who has met the quota, the number of votes must be
    greater of equal than the (num. seats) * (quota).
    """

    # Additional validation of input data for STV
    # Need a valid value for the number of seats
    if not isinstance(n_seats, int) and n_seats <= 0:
        raise ValueError('The number of seats must be an integer >= 1.')

    candidates, votes = vote.candidates, vote.votes

    quota = math.floor(len(votes) / (n_seats + 1)) + 1

    # Need a minimum number of votes to properly calculate the winners
    # TODO: Handle case of too few votes by considering most votes in this case?
    if len(votes) < (quota * n_seats):
        raise ValueError(
            'Too few votes to allocate all seats; # votes < (quota * # seats).',
            f'{len(votes)} votes cast, need {quota * n_seats}.'
            )

    # Define functions for the iteration where the winners are selected
    # Need a function to calculate winners, subtract spent votes, and transfer from losers
    def calculate_winners(df, quota):
        choices = df.groupby(['choice'], as_index=False).n_votes \
            .sum().copy()

        # Position in the winners list will be determined by round,
        # and within rounds by descending n_votes.
        # Firstly sort the choices.
        choices.sort_values('n_votes', ascending=False, inplace=True)

        # Ensure choices and votes are integers, there should be no NaNs
        choices = choices.astype({'choice': int, 'n_votes': int})

        # Construct dictionaries of the winners as
        # {'choice': <choice>, 'n_votes': <n_votes>}
        winners = choices[choices.n_votes >= quota].copy()

        return winners

    def subtract_votes_from_winners(df, new_winners, quota):
        for winner_id in new_winners['choice']:

            # Get the votes of the winner and have the quota proportionally 
            # deducted across their rows
            values = df[df.choice == winner_id].n_votes.copy()

            deducted_values = proportional_deduction_retain_int(values, quota)

            # Replace the old values with the new
            df = df.join(deducted_values, how='left')

            row_idx_mask = df.deducted.notna()

            df.loc[row_idx_mask, 'n_votes'] = df.loc[row_idx_mask, 'deducted']

            df.drop(['deducted'], axis=1, inplace=True)

        # Delete any rows where all votes are spent
        df = df[df.n_votes != 0]

        return df

    def transfer_from_losers(df, shift_cols):
        # Get the smallest number votes, will transfer all
        df_agg = df.groupby(['choice'], as_index=False).n_votes.sum()

        min_val = df_agg.min().n_votes

        losers = df_agg[df_agg.n_votes == min_val]

        df_losers = df[df.choice.isin(losers.choice)].copy()

        # Rename the columns of the filtered dataframe with the next
        # column over, to "transfer" the votes.
        # The current choice gets set to the be the last and the values
        # are replaced with NaNs.
        last_col = shift_cols[-1:]

        rename_cols = last_col + shift_cols

        rename_cols = {rename_cols[i + 1]: rename_cols[i] 
                       for i in range(len(rename_cols) - 1)}

        df_losers.rename(columns=rename_cols, inplace=True)

        df_losers.loc[:, last_col] = np.NaN

        # Delete the rows on the original dataframe,
        # then concatenate the renamed filtered df
        df.drop(index=df_losers.index, inplace=True)

        df = pd.concat([df, df_losers])

        # Drop rows where all choices are NaN's
        nan_idx = df.loc[df[shift_cols].isnull().all(axis=1), shift_cols].index

        df.drop(index=nan_idx, inplace=True)

        # Reaggregate
        df = df.fillna(-1).groupby(shift_cols, as_index=False).sum()

        df.replace([-1], [np.NaN], inplace=True)

        return df

    # Select winners
    # TODO: Handle exceeding n_seats
    # TODO: Handle ties
    # TODO: Reimplement using Meek algorithm https://blog.opavote.com/2017/04/meek-stv-explained.html

    votes_df = vote.aggregate()

    choice_cols_mask = votes_df.columns.str.contains('choice')
    shift_cols = votes_df.columns[choice_cols_mask].tolist()

    i = 0
    winners = pd.DataFrame()

    while len(winners) < n_seats:
        new_winners = calculate_winners(votes_df, quota)

        winners = pd.concat([winners, new_winners])

        if i == 0:
            if not new_winners.empty:
                votes_df = subtract_votes_from_winners(votes_df, new_winners, quota)
        else:
            votes_df = transfer_from_losers(votes_df, shift_cols)

        i = (i + 1) % 2

        if votes_df.empty and len(winners) < n_seats:
            warnings.warn('Unresolvable situation, incomplete set of winners selected')
            break

    replacements = {i: cand for (i, cand) in enumerate(candidates)}

    winners = winners.replace(replacements).to_dict('records')

    return Result(winners)


class Winner:
    def __init__(self, name, n_votes):
        self.name = name
        self.n_votes = n_votes

    def _validate(self):
        assert isinstance(self.name, str) and self.name
        assert isinstance(self.n_votes, int) and self.n_votes > 0


class Result:
    def __init__(self, winners):
        self.winners = winners

    def __iter__(self):
        return iter(self.winners)

    def __getitem__(self, s):
        return self.winners[s]

    @property
    def winners(self):
        return self._winners

    @winners.setter
    def winners(self, winners):
        self._winners = [Winner(name=winner['choice'], n_votes=winner['n_votes']) 
                         for winner in winners]


def proportional_deduction_retain_int(X: pd.Series, n: int, strategy = 'difference'):
    """
    This function deducts an amount across a sequence of values, and then uses
    iteround.saferound (strategy='largest') to adjust to integer values, to
    return a sequence of integers who's sum is n less than the original.

    This may perform oddly in some cases where there are a small number of
    votes.
    """
    # Validation checks
    if n < 0:
        raise ValueError('Cannot deduct a negative amount.')

    if min(X) < 0:
        raise ValueError('Sequence must contain only positive integers.')

    strategies = ('difference', 'largest', 'smallest')
    if strategy not in strategies:
        raise ValueError(f'Strategy must be one of {",".join(strategies)}.')

    sum_X = sum(X)

    if sum_X < n:
        raise ValueError('Cannot deduct more than the sum of the sequence.')

    # reduce the item values so that the sum is n less
    mult = (1 - ((n * 1.0) / sum(X)))

    X = X * mult

    index = X.index

    X = saferound(X, places=0, strategy='largest')

    X = pd.Series(X, index=index)

    X.rename('deducted', inplace=True)

    # Safety check
    if sum_X != (sum(X) + n):
        diff = sum_X - (sum(X) + n)
        message = f'Difference of {diff} between sum of the original values and the new + n).'
        message += f'\nResulting X is {X}'
        raise exc.RoundingError(message)

    return X
