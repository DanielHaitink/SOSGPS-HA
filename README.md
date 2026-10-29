# SOSGPS for Home Assistant

Read-only GPS tracking for trackers you can access in SOSGPS. Each authorized tracker provides a map location, battery percentage, connectivity, and last-seen timestamp.

## Requirements

- Home Assistant 2026.10 or newer.
- A reachable SOSGPS installation with the Home Assistant API enabled by its server release.
- An HTTPS server URL with a certificate trusted by Home Assistant.
- A dedicated SOSGPS Home Assistant access token.

## Install

### HACS custom repository

1. In HACS, open **Custom repositories**.
2. Add `https://github.com/DanielHaitink/SOSGPS-HA` as an **Integration**.
3. Download SOSGPS and restart Home Assistant.

This repository can be added manually to HACS; it is not a claim of inclusion in the default HACS catalogue.

### Manual

Copy `custom_components/sosgps` into your Home Assistant configuration directory under `custom_components/`, then restart Home Assistant.

## Connect

1. Open **SOSGPS → Account → Home Assistant**.
2. Enter a connection name, select the trackers to share, choose an expiry, and confirm your current password.
3. Create the token and copy it before closing the one-time display.
4. In Home Assistant, open **Settings → Devices & services → Add integration → SOSGPS**.
5. Enter the HTTPS server origin (for example `https://trackers.example.com`) and token. Do not include `/app` or `/api`.

The integration reads the latest stored data once per minute. It does not ask trackers for new GPS fixes or change their reporting interval.

Location entities work with Home Assistant maps, persons and zone automations. Battery and last-seen are separate sensors. Online means the tracker is communicating with SOSGPS; it is separate from whether Home Assistant can reach the server.

The map shows the last known position, including while the tracker is offline. The tracker attributes include `gps_valid` and `position_updated_at` (Unix seconds when available). Use last-seen and position age when deciding whether a location is current.

## Change trackers or renew access

To change scope, revoke the existing token in SOSGPS and create a replacement with the desired trackers. Home Assistant will offer reauthentication after its next failed poll. Enter the replacement token to preserve existing entity identities and automations. Newly authorized trackers are added automatically; trackers no longer returned become unavailable.

Revocation stops future API access. Previously received locations can remain in Home Assistant's recorder, backups, logs from other integrations, or dashboards. Manage Home Assistant history and backup retention separately.

## Connection security

The client requires HTTPS, validates certificates, refuses redirects, and uses a dedicated read-only credential. Never paste a token into an issue or a screenshot. Home Assistant stores integration credentials in its configuration; protect that installation and its backups.

No SOSGPS account password is entered into this integration. See [SECURITY.md](SECURITY.md) for reporting guidance.

## Development

Run the client smoke checks with Python and aiohttp:

```sh
python -m pip install aiohttp
python -m unittest discover -s tests -v
```

The API contract is documented in [docs/api.md](docs/api.md).
