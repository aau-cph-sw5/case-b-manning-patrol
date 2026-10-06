# Contracts

The contracts describe the interface between the clients and the server. They follow the standardised OpenAPI JSON format.


## Structure

```
contracts/
├── README.md           
├── some-contract/       
│   ├── v1/
│   │   ├── README.md   
│   │   ├── schema.json
│   │   └── CHANGELOG.md
│   └── v2/              
│       ├── README.md
│       ├── schema.json
│       └── CHANGELOG.md
└── another-contract/    
    ├── v1/
    │   ├── README.md
    │   ├── schema.json
    │   └── CHANGELOG.md
    └── v2/
        ├── README.md
        ├── schema.json
        └── CHANGELOG.md
```


## How to update/create a contract

If you want to update a schema, follow the guidelines below:

### Versioning Rules
- If the update **breaks the existing system** (e.g., URL changes, endpoints removed, or fields renamed), create a **new major version** (e.g., `v1.0.0` → `v2.0.0`).
  - Add a new directory (e.g., `v2/`) and copy the latest schema from the old version.
  - Mark the old version as **deprecated** in its `README.md` and `schema.json` (using `"deprecated": true` in OpenAPI).
  - Document the **sunset date** (e.g., "Sunset: 2026-12-01") in the old version's `README.md` and `CHANGELOG.md`.

- If the change is **only an addition** (e.g., new optional fields or endpoints) and does **not break the system**, increment the **minor version** (e.g., `v1.0.0` → `v1.1.0`).
  - Update the `info.version` field in `schema.json`.
  - Document the change in the `CHANGELOG.md` of that version.

- For **bug fixes** (e.g., typos, corrected examples), increment the **patch version** (e.g., `v1.0.0` → `v1.0.1`).
  - Update the `info.version` field in `schema.json`.
  - Document the fix in the `CHANGELOG.md`.
  
### CHANGELOG.md
Each versioned directory (`v1/`, `v2/`, etc.) must include a `CHANGELOG.md` to document changes for that version.
Use this format: