import math
import warnings
import pandas as pd
import numpy as np
import random as rnd
from typing import List, Tuple, Sequence, Literal, Dict
from itertools import chain
from collections import Counter
from iteround import saferound


Candidates = Tuple[str]
Votes = List[Tuple[int]]
Winners = List[Dict[Literal['choice', 'n_votes'], int]]


_typing_doc = """
The candidates are the tuple of people standing for the election.
The votes is a list of tuples, where each tuple contains the choices
of the voter, from 1st choice at the 1st position in the list, etc.
"""


def _validate_votes(candidates: Candidates, votes: Votes) -> None:
    """
    Validates if choices within votes are among those given in candidates,
    and that each vote has at least 1 choice.
    """ + _typing_doc

    smallest_choice = min(chain.from_iterable(votes))
    largest_choice = max(chain.from_iterable(votes))

    if smallest_choice < 0 or largest_choice > (len(candidates) - 1):
        raise ValueError('Invalid options selected in votes.')

    if min((len(vote) for vote in votes)) == 0:
        raise ValueError('Each vote must contain at least 1 choice.')


def first_past_the_post(candidates: Candidates, votes: Votes) \
        -> Tuple[str, int]:
    """
    First Past the Post is a system where each voter has one vote,
    and the candidate with the most votes wins.
    This means if a vote from a voter has more than one choice,
    then only the 1st choice will be considered.
    """ + _typing_doc

    _validate_votes(candidates, votes)

    first_choices = [first_choice for (first_choice, *rest) in votes]

    count = Counter(first_choices)

    [winner] = count.most_common(1)

    # Replace the index position / id of the candidate with the name
    winner[0] = candidates[winner[0]]

    return winner


def _create_votes_dataframe(candidates, votes):
    columns = [f'choice{i+1 if i else ""}' for i in range(len(candidates))]

    votes_df = pd.DataFrame(votes, columns=columns)

    votes_df['n_votes'] = 1

    votes_df = votes_df.fillna(-1).groupby(columns, as_index=False).sum()

    votes_df.replace([-1], [np.NaN], inplace=True)

    return votes_df


def single_transferable_vote(candidates: Candidates, votes: Votes, n_seats: int = 1):
    """
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
    """ + _typing_doc

    _validate_votes(candidates, votes)

    # Additional validation of input data for STV
    # Need a valid value for the number of seats
    if not isinstance(n_seats, int) and n_seats <= 0:
        raise ValueError('The number of seats must be an integer >= 1.')

    quota = math.floor(len(votes) / (n_seats + 1)) + 1

    # Need a minimum number of votes to properly calculate the winners
    # TODO: Handle case of too few votes by considering most votes in this case?
    if len(votes) < (quota * n_seats):
        raise ValueError(
            'Too few votes to allocate all seats; # votes < (quota * # seats).',
            f'{len(votes)} votes cast, need {quota * n_seats}.'
            )

    # Create a table of the votes, grouping like rankings.
    votes_df = _create_votes_dataframe(candidates, votes)

    winners = list()

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
        winners = choices[choices.n_votes >= quota].to_dict(orient='records')

        return winners

    def subtract_votes_from_winners(df, new_winners, quota):
        for winner in new_winners:
            winner_id = winner['choice']

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

        rename_cols = {rename_cols[i + 1]: rename_cols[i] for i in range(len(rename_cols) - 1)}

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

    shift_cols = votes_df.columns[votes_df.columns.str.contains('choice')].tolist()

    i = 0

    while len(winners) < n_seats:
        new_winners = calculate_winners(votes_df, quota)

        winners.extend(new_winners)

        if i == 0:
            if new_winners:
                votes_df = subtract_votes_from_winners(votes_df, new_winners, quota)
        else:
            votes_df = transfer_from_losers(votes_df, shift_cols)

        i = (i + 1) % 2

        if votes_df.empty and len(winners) < n_seats:
            warnings.warn('Unresolvable situation, incomplete set of winners selected')
            break

    return winners


def generate_candidates_and_votes(n_candidates: int, n_votes: int) \
        -> Tuple[List[int], List[List[int]]]:
    assert n_votes > 0 and n_candidates > 0

    candidates = list(range(n_candidates))

    votes = [rnd.sample(candidates, rnd.randint(1, len(candidates)))
             for i in range(n_votes)]

    return candidates, votes


class RoundingError(Exception):
    pass


Strategy = Literal['difference', 'largest', 'smallest']


def proportional_deduction_retain_int(X: pd.Series, n: int, strategy: Strategy = 'difference') \
        -> Sequence[int]:
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
        raise RoundingError(message)

    return X
