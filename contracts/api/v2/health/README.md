# Health API

Backend API contract for health checks. Used by clients, dashboards, and infrastructure to verify the backend is running and connected to the database.

## Endpoints

- `GET api/v2/health` - Liveness check; reports that the backend is running
- `GET api/v2/health/db` - Database health check; verifies the database connection

## Implementation Notes

`GET /api/v2/health` never touches the database, so it answers even when the database is down. `GET /api/v2/health/db` runs a trivial query and only answers `200` when the database is reachable.

## Data Models

### HealthStatus
- `status`: string — always `"ok"`
- `message`: string — human-readable status message

### DatabaseHealthStatus
- `database`: string — always `"up"`
