"""Verify every hash chain in the database and report where one breaks.

Run with ``uv run verify-chain`` against the database from DATABASE_URL.
The database is only read.
"""

import asyncio
import sys

from sqlalchemy.exc import SQLAlchemyError
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
    def print_empty(chain: ChainName) -> None:
        """Print that the chain has no links, so nothing was verified."""
        print(f"{chain.value}: empty (nothing to verify)")

    @staticmethod
    def print_broken(chain: ChainName, chain_break: ChainBreak) -> None:
        """Print the first broken link of the chain and why it broke."""
        link = chain_break.link
        print(f"{chain.value}: broken at seq {link.seq} (entry {link.record_id})")
        print(f"    reason: {chain_break.reason.value}")

    @staticmethod
    def print_unlinked(chain: ChainName, unlinked_count: int) -> None:
        """Print how many entries of the chain's table have no link in it."""
        noun = "entry has" if unlinked_count == 1 else "entries have"
        print(f"{chain.value}: {unlinked_count} {noun} no chain link")


class VerifyChainCommand:
    """Check every chain in the database and print one result per chain."""

    @staticmethod
    def run() -> None:
        """Check all chains and print the result of each.

        Exits with code 0 if every chain is intact, 1 if a chain is broken
        or has entries without a link, and 2 if the database could not be
        read, for example because it is down or a table is missing.
        """
        try:
            all_intact = asyncio.run(VerifyChainCommand._check_all_chains())
        except (SQLAlchemyError, OSError) as error:
            message_lines = str(error).splitlines()
            reason = message_lines[0] if message_lines else type(error).__name__
            print(f"verify-chain: could not check chains: {reason}", file=sys.stderr)
            raise SystemExit(2) from None
        if not all_intact:
            raise SystemExit(1)

    @staticmethod
    async def _check_all_chains() -> bool:
        """Check each chain and return True if all of them are intact."""
        all_intact = True
        try:
            for chain in ChainName:
                chain_intact = await VerifyChainCommand._check_chain(chain)
                if not chain_intact:
                    all_intact = False
        finally:
            await engine.dispose()
        return all_intact

    @staticmethod
    async def _check_chain(chain: ChainName) -> bool:
        """Load, verify and print one chain.

        Return True only if no link is broken and every entry has a link.
        An empty chain is intact, but is printed as empty so it is not
        mistaken for a verified one.
        """
        async with AsyncSession(engine) as session:
            linked_entries = await ChainLoader.load(session, chain)
            unlinked_count = await ChainLoader.count_unlinked(session, chain)

        chain_break = ChainVerifier.verify(linked_entries)
        if chain_break is not None:
            ChainResultPrinter.print_broken(chain, chain_break)
        elif linked_entries:
            ChainResultPrinter.print_intact(chain, len(linked_entries))
        else:
            ChainResultPrinter.print_empty(chain)
        if unlinked_count:
            ChainResultPrinter.print_unlinked(chain, unlinked_count)
        return chain_break is None and unlinked_count == 0
