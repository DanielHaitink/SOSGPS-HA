# Security

Do not report vulnerabilities or share access tokens in public issues.

Use GitHub's **Security → Report a vulnerability** feature if enabled. If it is unavailable, contact the repository owner through a private channel before sharing details.

For an exposed token, revoke it in SOSGPS immediately, then create a replacement. Protect Home Assistant's configuration and backups; they contain the integration credential and may contain location history.

This repository contains the Home Assistant client and its public API contract. Server authorization and account-management implementation are maintained separately.
