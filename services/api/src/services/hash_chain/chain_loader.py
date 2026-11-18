"""Load a chain's links together with the entries they point to.

Reads from the database and hands the result to ``ChainVerifier``. Also
counts entries that have no link, which the verifier cannot see because it
only follows links. Nothing here hashes, verifies or writes.
"""

from sqlalchemy.exc import NoResultFound
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.repository.adjustment import count_unlinked_adjustments, get_adjustment
from src.db.repository.event import count_unlinked_events, get_event
from src.db.repository.integrity_chain_link import get_chain
from src.services.hash_chain.chain_verifier import LinkedEntry
from src.services.hash_chain.entry_stringifier import ChainEntry


class ChainLoader:
    """Read one chain's links and their entries from the database."""

    @staticmethod
    async def load(session: AsyncSession, chain: ChainName) -> list[LinkedEntry]:
        """Return every link of ``chain`` with its entry, oldest first.

        An entry that no longer exists is returned as None next to its link, so
        the caller can report the deletion instead of failing. Runs one query
        for the links and one more per link for its entry.
        """
        linked_entries = []
        for link in await get_chain(session, chain):
            entry = await ChainLoader._fetch_entry(session, chain, link)
            linked_entries.append(LinkedEntry(link=link, entry=entry))
        return linked_entries

    @staticmethod
    async def count_unlinked(session: AsyncSession, chain: ChainName) -> int:
        """Return how many events or adjustments have no link in ``chain``.

        The app saves every entry together with its link, so a count above 0
        means rows were written to the database directly.
        """
        if chain == ChainName.EVENTS:
            return await count_unlinked_events(session)
        return await count_unlinked_adjustments(session)

    @staticmethod
    async def _fetch_entry(
        session: AsyncSession, chain: ChainName, link: IntegrityChainLink
    ) -> ChainEntry | None:
        """Return the entry ``link`` points to, or None if it was deleted.

        The chain name decides whether the link points to an event or an
        adjustment.
        """
        try:
            if chain == ChainName.EVENTS:
                return await get_event(session, link.record_id)
            return await get_adjustment(session, link.record_id)
        except NoResultFound:
            return None
