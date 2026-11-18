"""Link a stored event or adjustment onto the hash chain.

Combines ``EntryStringifier`` and ``EntryHasher``: the entry is turned into its
fixed string, which is then hashed and chained onto the previous head hash.
Events and adjustments share one chain. Nothing here reads or writes the
database; the caller passes in the chain's current head hash and stores the
result.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.db.repository.integrity_chain_link import get_head_hash
from src.services.hash_chain.entry_hasher import EntryHasher
from src.services.hash_chain.entry_stringifier import ChainEntry, EntryStringifier


class ChainLinker:
    """Turn a stored entry into its chain hashes, linked onto a previous hash."""

    def __init__(self, session: AsyncSession, entry: ChainEntry):
        self.session = session
        self.entry = entry
        self.chain_name = self._get_chain_name()

    async def link(self, source: str) -> IntegrityChainLink:
        event_string = EntryStringifier.stringify_entry(self.entry)

        hashed_entry = EntryHasher.hash_text(
            text=event_string, prev_hash=await self._get_prev_hash()
        )

        chain_link = IntegrityChainLink(
            chain=self.chain_name,
            record_id=self._get_record_id(),
            source=source,
            prev_hash=hashed_entry.prev_hash,
            content_hash=hashed_entry.content_hash,
            head_hash=hashed_entry.head_hash,
            server_timestamp=ChainLinker._now_utc(),
        )

        return chain_link

    async def _get_prev_hash(self) -> str:
        prev_hash = await get_head_hash(self.session, chain=self.chain_name)
        if prev_hash is None:
            prev_hash = EntryHasher.GENESIS_HASH
        return prev_hash

    def _get_record_id(self) -> UUID:
        return (
            self.entry.adjustment_id
            if (isinstance(self.entry, Adjustment))
            else self.entry.event_id
        )

    def _get_chain_name(self) -> ChainName:
        return (
            ChainName.EVENTS
            if (isinstance((self.entry), Event))
            else ChainName.ADJUSTMENTS
        )

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)
