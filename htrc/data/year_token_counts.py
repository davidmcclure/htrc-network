

import os

from vedis import Vedis
from collections import defaultdict, Counter
from multiprocessing import Pool
from wordfreq import top_n_list

from htrc.corpus import Corpus
from htrc.volume import Volume



class Writer:


    def __init__(self, path):

        """
        Canonicalize the data path.

        Args:
            path (str)
        """

        self.path = os.path.abspath(path)


    @property
    def db(self):

        """
        Get a database connection.

        Returns: Vedis
        """

        return Vedis(self.path)


    def index(self, num_procs=8, cache_len=1000):

        """
        Index total token counts by year.

        Args:
            num_procs (int)
        """

        corpus = Corpus.from_env()

        groups = corpus.path_groups(cache_len)

        with Pool(num_procs) as pool:

            for i, group in enumerate(groups):

                # Queue volume jobs.
                jobs = pool.imap_unordered(worker, group,)
                cache = defaultdict(Counter)

                # Accumulate the counts.
                for year, counts in jobs:
                    cache[year] += counts

                # Flush to disk.
                self.flush_cache(cache)
                print(i*cache_len)


    def flush_cache(self, cache):

        """
        Flush a cache to the Redis.

        Args:
            cache (dict)
        """

        for year, counts in cache.items():
            for token, count in counts.items():
                self.db.incr_by((token, year), count)



def worker(path):

    """
    Extract a token counts for a volume.

    Args:
        path (str): A volume path.

    Returns:
        tuple (year<int>, counts<Counter>)
    """

    vol = Volume(path)

    return (vol.year, vol.cleaned_token_counts())