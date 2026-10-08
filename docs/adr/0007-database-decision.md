# ADR database decision

**Status.** Proposed

**Date.** 08-10-2026

**Deciders.** Maya, Jakob, Sebastian, Signe, Victor, Patrick, Markus

**Related backlog items.**  met-b-003, met-b-004


## Context
The projects needs to store data. It needs to store static data and dynamic data. The static data is tables such as stations and patrol_area where it is used when a connection event needs to know where the steward currently is located (Platform or concourse and the station, etc). The dynamic data consist of events when the steward etiher connects of disconnects. The event is sent to the backend and then stored in the database as events in the event table. The data needs reference data to couple it to events. The control room operators must see where the connection events happen excatly in the metro network and see live status.

## Decision

We choose PostgreSQL as the database for the backend. PostgreSQL is an open-source relational database management system (RDBMS) that we already use in our database systems course, so the teams have experience with it. It also fits our two kinds of data. The static reference data (stations, patrol areas) is naturally relational. The dynamic data (steward connect/disconnect events) is append-only and its payload may evolve over time. PostgreSQL's NoSQL capabilities - the JSON/JSONB column type - let us store each event payload as a flexible document inside the relational event table. 

## Consequences
Advantages of using postgres:
 - Cost effectiveness: Postgres is open-source and has a lower total cost of ownership compared to other databases with a proprietary license.
 - Extensibility: Postgres can be easily customized to meet specific needs. It supports a wide varity of OS, platforms, and programming languages.
 - Advanced features: Such as JSON support, and better performance for complex queries. 

Drawbacks of using postgres:
 - Complexity: Postgres can be complex for new users/beginners.
 - Performance: Postgres can be slower compared to other databases, especially for write-intensive applications.
 - Documentation: Hard to navigate.
 - Scalability: Although postgres scales well, it can be challenging to manage large-scale applications.

## Alternatives considered
We did not consider any alternatives. At the first nexus scrum meeting the teams collectively decided on the database (RDBMS) to be PostgreSQL.


## Notes
Link to source: https://www.quest.com/learn/what-is-postgresql.aspx
