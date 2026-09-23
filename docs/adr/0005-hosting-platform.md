# ADR 0005. Ucloud as cloud platform.

**Status.** Proposed
**Date.** 2026-09-23
**Deciders.** Peter Rasmussen, Sebastian Milo, team 3
**Related backlog items.** MET-b-004, MET-b-005, MET-b-012, MET-b-013, MET-b-020, MET-b-021, MET-b-023, MET-b-025

## Context

Creating a simulation for case-b-manning-patrol requires a common platform to extensively test and run the application(s), in an environment as close to production as possible.
It serves as a baseline from which the teams can build from and against. Even if the application(s) are not deployed directly into Metro Service systems, the teams still have functioning software, emulating a real-world software environment.
Ucloud is a new hosting service provided by AAU, which provides a secure and safe environment, targeting students for easy collaboration and high accessibility.
The first choice was STRATO, but it has been deprecated for student use^1.

## Decision

We will host our application(s) on AAU Ucloud servers as a safe staging environment, with the possibility to expand the pipeline to deployment in the future.

## Consequences

Pros
Ucloud is accessible for all students and the recommended platform from CLAAUDIA support^1. It removes some liability in the case of data privacy from the student onto AAU, compared to external/corporate cloud services.

Cons
Ucloud is a new and unknown service to all the teams, which will incur an additional on-boarding cost setting it up correctly. This cost is entirely unknown, so planning resources for it is guess work in the beginning.
As with any early decision, this commits us in the long run and can provide costly to reverse later in the process.

## Alternatives considered

**AWS/Azure/Cloudfire - Large cloud hyperscale platforms.** Although close to production-like environment, these options are unnecessary for the scope and requirements for case-b-manning-patrol. Could turn costly if freemium plan provides inadequate features/tools.

**Vercel/Heroku/Render - PaaS application platforms.** Closer to the scope of the project compared to the large providers, but working with 'in-house' hosting from Ucloud seems more suitable for a student project.

**STRATO** - The previous AAU/CLAAUDIA service, now restricted to researchers and not students.

**Localhost.** Not hosting online lowers the environment fidelity, not emulating a real world scenario of software development/scenario.

## Notes
1. Screenshot from CLAAUDIA support in commit history. Also https://hpc.aau.dk/ outlining the different access privileges of CLAAUDIA services.
