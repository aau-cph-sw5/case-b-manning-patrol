"""Verify every hash chain in the database and report where one breaks.

Run with ``uv run verify-chain`` against the database from DATABASE_URL.
The database is only read.
"""

import asyncio

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine
from src.db.models.integrity_chain_link import ChainName
from src.services.hash_chain.chain_loader import ChainLoader
from src.services.hash_chain.chain_verifier import ChainBreak, ChainVerifier


class ChainResultPrinter:
    """Print the result of checking one chain.

    Only formats and prints; it decides nothing.
    """

    @staticmethod
    def print_intact(chain: ChainName, link_count: int) -> None:
        """Print that the chain is intact and how many links it has."""
        print(f"{chain.value}: OK ({link_count} links)")

    @staticmethod
    def print_broken(chain: ChainName, chain_break: ChainBreak) -> None:
        """Print the first broken link of the chain and why it broke."""
        link = chain_break.link
        print(f"{chain.value}: broken at seq {link.seq} (entry {link.record_id})")
        print(f"    reason: {chain_break.reason.value}")


class VerifyChainCommand:
    """Check every chain in the database and print one result per chain."""

    @staticmethod
    def run() -> None:
        """Check all chains and print the result of each.

        Exits with code 1 if any chain is broken, otherwise with code 0.
        """
        all_intact = asyncio.run(VerifyChainCommand._check_all_chains())
        if not all_intact:
            raise SystemExit(1)

    @staticmethod
    async def _check_all_chains() -> bool:
        """Check each chain and return True if all of them are intact."""
        all_intact = True
        for chain in ChainName:
            chain_intact = await VerifyChainCommand._check_chain(chain)
            if not chain_intact:
                all_intact = False
        await engine.dispose()
        return all_intact

    @staticmethod
    async def _check_chain(chain: ChainName) -> bool:
        """Load, verify and print one chain; return True if intact."""
        async with AsyncSession(engine) as session:
            linked_entries = await ChainLoader.load(session, chain)

        chain_break = ChainVerifier.verify(linked_entries)
        if chain_break is None:
            ChainResultPrinter.print_intact(chain, len(linked_entries))
            return True

        ChainResultPrinter.print_broken(chain, chain_break)
        return False
