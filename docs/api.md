# Public read-only API contract, version 1

Request: `GET /api/integrations/home-assistant/v1/devices`
Authentication: `Authorization: Bearer <integration access token>`

Response shape:

```json
{
  "api_version": 1,
  "grant_id": "opaque-connection-id",
  "devices": [
    {
      "id": "tracker-id",
      "name": "Example tracker",
      "online": true,
      "last_seen": 1790000000,
      "battery": 80,
      "location": {
        "latitude": 52.1,
        "longitude": 5.1,
        "accuracy": 15,
        "gps_valid": true,
        "updated_at": 1790000000
      }
    }
  ]
}
```

Devices are limited to the connection's selection and current account permissions.
An empty devices array is valid, including after tracker access changes.
Location can be null; battery, last_seen, accuracy and updated_at can be null.
Times are Unix seconds. Accuracy is in metres. IDs are opaque strings.

401/403 requires credential renewal; other non-200 statuses are transient failures.
Clients must not follow redirects. Responses must not be cached.
Only the read-only contract belongs in this repository.
