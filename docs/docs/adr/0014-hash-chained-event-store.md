# ADR 0014. Hash-chained event store.

**Status:** Accepted

**Date:** 2026-11-17

**Deciders:** Rohan Atik, Nichlas Christiansen, Ryan Zachariasen, Jakob Michaelsen, Asbjørn Gosvig, Marcus Hørup, team 8

**Related backlog items:** MET-B-021, MET-B-022

**Extends:** [ADR 0008](0008-append-only-event-store-decision.md)

## Context

ADR 0008 made the event store append-only: there is no code path that updates
or deletes events. But "no code path" only binds our own application. Anyone
with write access to the database can still edit or delete rows directly, and
afterwards nothing in the system shows that it happened. For records that act
as evidence in compliance reports, a rule that cannot be checked is weaker than
evidence that can.

MET-B-021 therefore requires that events are chained such that altering or
removing any one is detectable by verifying the chain. Adjustments are included,
because a supervisor's correction is as much part of the evidence as the event
it corrects.

## Decision

Every stored `Event` and `Adjustment` row is linked onto a hash chain.

- `EntryStringifier` writes each row as one fixed string: keys sorted, no
  whitespace, lowercase UUIDs, all timestamps in UTC, and a `FORMAT_VERSION`
  tag, so the same row always produces the same string. The field lists are
  explicit and must cover every column of the table they hash.
- `EntryHasher` computes three SHA-256 digests per entry: a `content_hash` of
  the stringified entry alone, a `prev_hash` equal to the previous entry's
  `head_hash` (a fixed `GENESIS_HASH` of 64 zeroes for the first entry), and a
  new `head_hash` over `prev_hash` followed by `content_hash`.
- `ChainLinker` combines the two: given the database session and a stored
  entry, it reads the chain's current head hash (falling back to
  `GENESIS_HASH` when the chain is empty), links the entry onto it and
  returns the row to store.
- The digests are stored per entry in the `integritychainlink` table together
  with the chain name, a per-chain sequence number that is unique together with
  the chain name, and the id of the committed row.

Because each `head_hash` includes the one before it, editing or removing any
stored entry changes every `head_hash` after it, and the stored `content_hash`
of the edited entry no longer matches a digest recomputed from the row.
Verification walks the chain in sequence order and recomputes every link.

Events are chained on the events chain and adjustments on the adjustments
chain, each in the order the entries are stored.

Verification (`ChainLoader` and `ChainVerifier`, MET-B-021-TASK-004) walks the
stored links of a chain in sequence order and recomputes every link: the
entry it commits still exists, each link's `prev_hash` is the `head_hash` of
the link before, and stringifying and hashing the entry again gives the stored
`content_hash` and `head_hash`. Verification therefore checks what was
chained, and only what was chained — see the Limits section.

When the chain is first turned on, the events and adjustments already in the
database are linked in one one-time backfill, in insertion order, starting from
`GENESIS_HASH`. The backfill hashes the state of the database as it is at that
moment; it cannot say anything about history from before it ran.

## Consequences

Positive impact

- Altering an event or adjustment is detectable, and the mismatch localizes to
  the exact row through its `content_hash`.
- Removing or reordering an entry is detectable through the broken link to the
  next entry's `prev_hash` and the sequence numbers.
- Events and adjustments gain tamper evidence without changing how they are
  stored and without new infrastructure beyond one table.

Potential drawbacks

- Every insert does one extra stringification, two hashes and one insert; the
  chain is an append in the same transaction as the entry it commits.
- A format change to the stringifier means links made before it can no longer
  be verified against the new code without a migration.
- The chain is wired into the code paths that store events and adjustments
  through an `EventProducer` (MET-B-021-TASK-003, PR #265); a path that
  bypasses the producer stores an unchained row, which walking the chain
  alone does not find (see Limits).

## Limits — what the chain does not protect against

The scheme must not be described as more than it is. An honest list:

1. **Anyone with database write access can recompute the whole chain.** The
   hashes are plain SHA-256 over database rows, so the same access that can
   edit rows can also recompute every link and rewrite the stored digests to
   match. The chain detects accidental and careless changes, not a privileged
   adversary. No secret is needed to forge a consistent chain.
2. **Deleting the newest entries is not detected.** Verification walks forward
   from the first link; remove the last links and what remains is still
   internally consistent. Nothing outside the database anchors the expected
   head hash, so a truncated tail verifies as a shorter, valid chain.
3. **Reference data and configuration are not in the chain.** Only events and
   adjustments are hashed. Stations, lines, patrol areas, trains, steward shift
   identities and the config table can be edited without breaking any link, so
   a changed reference datum changes how an event is interpreted in a report
   although the event itself is unchanged.
4. **The chain proves a record is unchanged, not that it was true when
   written.** A wrong event — wrong steward, wrong beacon, wrong time — hashes
   and chains exactly like a correct one. The chain is integrity for the record,
   not truth for its content.
5. **`overdue_log` and `at_risk_log` are not chained.** They are derived from
   events and stored unchained, so their rows can be edited without detection;
   at best they can be recomputed from the events they derive from.
6. **Entries added outside the chain are not detected by chain verification
   itself.** A row inserted without a link — a direct SQL insert that bypasses
   the `EventProducer` — is simply not on the chain, and verification, which
   walks the stored links, finds nothing missing. Detecting such rows needs a
   completeness check: every stored event and adjustment must also appear
   exactly once as a link. The verifier does not include that check at the
   time of writing, so until it does the chain is tamper evidence for what
   was chained, not proof that every stored row was chained. A privileged
   adversary can additionally forge a link for the inserted row, which limit
   1 already covers.

## Alternatives considered

**Database triggers enforcing the chain.** An insert trigger inside PostgreSQL
could compute and store the link, so no code path can bypass the chain.
Rejected: it does not address the main threat — whoever can edit rows can also
disable or redefine the trigger and recompute — and chain logic in triggers is
harder to test and version than the Python modules.

**Merkle tree.** A tree over the entries gives compact proofs of membership for
subsets. Rejected as overkill: we verify the whole log in order and do not need
partial proofs, and it carries the same weakness against privileged recompute
with a more complex structure to store and verify.

**HMAC instead of plain SHA-256.** A keyed digest means forging a consistent
chain requires the key, not just database access. Rejected for now: in our
deployment the key would live on the same host as the database, which removes
most of the protection, and key management becomes an extra operational
dependency. It is the natural strengthening if the threat model grows.

**External anchor.** Periodically copying the current head hash to a system
outside the database (a hosted append-only log, a signed statement). This is
the only option that detects deletion of the newest entries and forged
recomputation of the whole chain. Rejected for now: it requires a second
trusted system and an operational process the project does not have. It is the
documented way to strengthen the scheme later.

## Notes

- MET-B-022 (data-protection statement) builds on this document; the limits
  above are the honest input it should reflect. The B-022 owner gets the link
  to this ADR when it is merged.
- Open question for the product owner: given limit 3, is reproducing reports
  with today's reference data acceptable for AC3?
- ADR 0008 remains in force; this ADR extends it with tamper evidence and
  supersedes nothing. If the chain is later anchored externally or keyed, a new
  ADR supersedes this one.
