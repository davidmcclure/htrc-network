

import pytest
import time

from hol.models import AnchoredCount
from hol import config

from test.helpers import make_vol


pytestmark = pytest.mark.usefixtures('db')


def test_index_year_token_counts(mock_corpus, config):

    """
    AnchoredCount.index() should index per-year counts for tokens that appear
    on the same page with the anchor token, bucketed by anchor token count.
    """

    v1 = make_vol(year=1901, counts=[
        {

            'anchor': {
                'POS': 1
            },

            'one': {
                'POS': 1
            },
            'two': {
                'POS': 2
            },

        },
    ])

    v2 = make_vol(year=1902, counts=[
        {

            'anchor': {
                'POS': 2
            },

            'two': {
                'POS': 3
            },
            'three': {
                'POS': 4
            },

        },
    ])

    v3 = make_vol(year=1903, counts=[
        {

            'anchor': {
                'POS': 3
            },

            'three': {
                'POS': 5
            },
            'four': {
                'POS': 6
            },

        },
    ])

    mock_corpus.add_vol(v1)
    mock_corpus.add_vol(v2)
    mock_corpus.add_vol(v3)

    AnchoredCount.index('anchor')

    assert AnchoredCount.token_year_level_count('one', 1901, 1) == 1
    assert AnchoredCount.token_year_level_count('two', 1901, 1) == 2
