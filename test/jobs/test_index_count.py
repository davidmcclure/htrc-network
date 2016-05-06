

import pytest
import time

from click.testing import CliRunner

from hol.models import Count
from hol.jobs import index_count
from hol import config

from test.helpers import make_page, make_vol


pytestmark = pytest.mark.usefixtures('db')
pytestmark = pytest.mark.skip()


def test_index_year_token_counts(mock_corpus, config):

    """
    Count.index() should index per-year token counts.
    """

    v1 = make_vol(year=1901, pages=[
        make_page(counts={
            'one': {
                'POS': 1
            },
            'two': {
                'POS': 2
            },
        }),
    ])

    v2 = make_vol(year=1902, pages=[
        make_page(counts={
            'two': {
                'POS': 3
            },
            'three': {
                'POS': 4
            },
        }),
    ])

    v3 = make_vol(year=1903, pages=[
        make_page(counts={
            'three': {
                'POS': 5
            },
            'four': {
                'POS': 6
            },
        }),
    ])

    mock_corpus.add_vol(v1)
    mock_corpus.add_vol(v2)
    mock_corpus.add_vol(v3)

    index_count.callback()

    assert Count.token_year_count('one',    1901) == 1
    assert Count.token_year_count('two',    1901) == 2
    assert Count.token_year_count('two',    1902) == 3
    assert Count.token_year_count('three',  1902) == 4
    assert Count.token_year_count('three',  1903) == 5
    assert Count.token_year_count('four',   1903) == 6


def test_merge_year_counts(mock_corpus, config):

    """
    Token counts for the same years should be merged.
    """

    v1 = make_vol(year=1901, pages=[
        make_page(counts={
            'one': {
                'POS': 1
            },
            'two': {
                'POS': 2
            },
        }),
    ])

    v2 = make_vol(year=1901, pages=[
        make_page(counts={
            'one': {
                'POS': 11
            },
            'two': {
                'POS': 12
            },
        }),
    ])

    mock_corpus.add_vol(v1)
    mock_corpus.add_vol(v2)

    index_count.callback()

    assert Count.token_year_count('one', 1901) == 1+11
    assert Count.token_year_count('two', 1901) == 2+12