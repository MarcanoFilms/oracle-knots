# Security Policy

## Reporting a Vulnerability

We take the security of Oracle Knots and the Bitcoin network extremely seriously. If you find a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.** Public disclosure can expose users to loss of funds or network partitioning.
2. Contact the maintainers directly or use pgp keys if available.
3. Provide a detailed description of the vulnerability, including step-by-step reproduction steps.

We will acknowledge your report promptly and coordinate the fix and release process.

## Scope

consensus rules and network stability are critical. Vulnerabilities affecting:
- Consensus validation logic (causing potential chain splits)
- P2P message parsing (causing memory corruption or remote execution)
- RPC vulnerabilities (unauthorized access or sandbox escape)
are considered critical.
