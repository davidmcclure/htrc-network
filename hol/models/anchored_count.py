

from collections import defaultdict, Counter
from functools import partial

from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint
from sqlalchemy.sql import text

from hol.models import Base
from hol.corpus import Corpus
from hol import config



class AnchoredCount(Base):


    __tablename__ = 'anchored_count'

    __table_args__ = (
        PrimaryKeyConstraint('token', 'year', 'anchor_count'),
    )

    token = Column(String, nullable=False)

    year = Column(Integer, nullable=False)

    anchor_count = Column(Integer, nullable=False)

    count = Column(Integer, nullable=False)


    @staticmethod
    def worker(anchor, vol):

        """
        Extract anchored token counts for a volume.

        Args:
            anchor (str)
            vol (Volume)

        Returns:
            tuple (year<int>, counts<dict>)
        """

        counts = vol.anchored_token_counts(anchor)

        return (vol.year, counts)


    @classmethod
    def index(cls, anchor, num_procs=12, page_size=1000):

        """
        Index token counts by year.

        Args:
            anchor (str)
            num_procs (int)
            cache_len (int)
        """

        corpus = Corpus.from_env()

        # Apply the anchor token.
        worker = partial(cls.worker, anchor)

        mapper = corpus.map(worker, num_procs, page_size)

        for i, results in enumerate(mapper):

            # year -> level -> counts
            page = defaultdict(lambda: defaultdict(Counter))

            for year, level_counts in results:
                for level, counts in level_counts.items():
                    page[year][level] += counts

            cls.flush_page(page)

            print((i+1)*page_size)


    @classmethod
    def flush_page(cls, page):

        """
        Flush a page to disk.

        Args:
            page (dict)
        """

        session = config.Session()

        # SQLite "upsert."
        query = text("""

            INSERT OR REPLACE INTO {table!s} (
                token,
                year,
                anchor_count,
                count
            )

            VALUES (
                :token,
                :year,
                :anchor_count,
                :count + COALESCE(
                    (
                        SELECT count FROM {table!s} WHERE (
                            token = :token AND
                            year = :year AND
                            anchor_count = :anchor_count
                        )
                    ),
                    0
                )
            )

        """.format(table=cls.__tablename__))

        for year, level_counts in page.items():
            for level, counts in level_counts.items():
                for token, count in counts.items():

                    # Whitelist tokens.
                    if token in config.tokens:

                        session.execute(query, dict(
                            table=cls.__tablename__,
                            token=token,
                            year=year,
                            anchor_count=level,
                            count=count,
                        ))

        session.commit()