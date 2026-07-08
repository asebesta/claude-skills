---
name: donordock-api
description: DonorDock Public API integration reference for building nonprofit CRM and donor management integrations. Use when writing code that interacts with the DonorDock API (public-api.donordock.com), including syncing or importing Contacts, Gifts, Activities, Campaigns, Appeals, Funds, Badges, Marketing Lists, Event Attendance, Gift Batches, or sending template emails. Triggers on DonorDock, donordock.com, or DonorDock donor/gift/contact sync tasks.
---

# DonorDock Public API

Reference for integrating with the **DonorDock Public API (v1)** — a REST API over the DonorDock nonprofit CRM. Covers contacts (donors), gifts, activities, campaigns, appeals, funds, badges, marketing lists, event attendance, closed gift batches, template emails, and metadata (users, email templates, custom field definitions).

**For every endpoint's parameters and every object's fields, see [references/endpoints.md](references/endpoints.md) (endpoint catalog) and [references/schemas.md](references/schemas.md) (object schemas).**

## Base URL

```
https://public-api.donordock.com/api/v1
```

## Authentication

HTTP Basic over HTTPS: `APIKey:APISecret` Base64-encoded, sent in the `Authorization` header. Keys are generated in the DonorDock UI (Settings → Integrations → API key).

```bash
curl -u "$DD_API_KEY:$DD_API_SECRET" "https://public-api.donordock.com/api/v1/Contacts?take=10"
```

## Pagination and Common Query Parameters

List endpoints share a common shape:

| Parameter | Meaning |
|-----------|---------|
| `skip` / `take` | Offset pagination. `take` max is **1000** |
| `fromDate` / `toDate` | Filter by `CreatedOn` (UTC) |
| `fromDateModified` / `toDateModified` | Filter by `ModifiedOn` (UTC) |
| `sortBy` | `CreatedOn` or `ModifiedOn` |
| `sortDir` | `ASC` or `DESC` |

List responses are wrapped in a page envelope:

```json
{ "TotalRecords": 1234, "CurrentRecords": 100, "Data": [ ... ] }
```

Page until `skip + CurrentRecords >= TotalRecords`.

## API Categories

| Category | Endpoints | Notes |
|----------|-----------|-------|
| Contacts | list, get, create, update, search | Donor records; search by email, phone, accountNumber, memberId, integrationId |
| Gifts | list, get, create, search | Filter by `status` and `transactionType`; no update endpoint |
| Activities | list, get, create, update, search | Notes, tasks, asks; can add to Action Board |
| Campaigns | list, get, create, update, search | |
| Appeals | list, get, create | |
| Funds | list, get, create | |
| Badges | list, add, remove | Badge ↔ contact assignments |
| MarketingLists | list members, add member | No remove endpoint |
| Events | list attendance, create attendance | |
| GiftBatches | list closed batches, get by ID | Read-only; filtered/sorted by `ClosedDate` |
| Emails | send template email | Deducts marketing email credits |
| MetaData | user list, email template list, custom field definitions | |

## Key Endpoints

```
GET    /api/v1/Contacts                      # List contacts (paged)
GET    /api/v1/Contacts/{contactId}          # Get contact
POST   /api/v1/Contacts                      # Create contact
PUT    /api/v1/Contacts/{contactId}          # Update contact
GET    /api/v1/Contacts/ContactSearch        # Search (email, phone, accountNumber, ...)

GET    /api/v1/Gifts                         # List gifts (status/transactionType filters)
POST   /api/v1/Gifts                         # Create gift
GET    /api/v1/Gifts/GiftSearch              # Search (paymentId, integrationId, contact keys, ...)

GET    /api/v1/Activities                    # List activities
POST   /api/v1/Activities                    # Create activity
POST   /api/v1/Emails/SendTemplateEmail      # Send template email to a contact
```

## Linking Records to Contacts

Objects that belong to a contact (gifts, activities, badges, marketing list members, event attendance, template emails) accept several alternative contact identifiers on create — provide **one** of:

- `ContactId` — DonorDock internal ID
- `ContactAccountNumber` — DonorDock account number
- `ContactMemberId` — your member ID
- `ContactIntegrationId` — your external system's ID
- `ContactEmail` — contact's email

## Gift Enums

- `Status`: `Received` (default), `Pledged`, `Cancelled`, `Pending`, `Processing`
- `TransactionType`: `Donation`, `Membership`, `EventTicket`, `Grant`

Both filters accept comma-delimited multiple values on `GET /api/v1/Gifts`.

## Best Practices

1. **Set `IntegrationId` and `Source`** on records you create — they identify your integration's records and are the search keys (`integrationId` params) on the search endpoints. Search before create to avoid duplicates; there is no server-side upsert.
2. **Incremental sync**: poll with `fromDateModified` + `sortBy=ModifiedOn` (no webhooks exist in the public API).
3. **Custom fields**: fetch definitions first via `GET /api/v1/MetaData/GetCustomFieldDefinitions?entityType=...`, then write values through the `CustomFields` array (`FieldId`, `Value`).
4. **Gifts have no update endpoint** — create them with correct amounts/attribution the first time. Contact name/address fields on a gift are denormalized contact data, not gift data.
5. **SendTemplateEmail consumes marketing email credits** — confirm before bulk sends.

## Disclaimer

This skill is not affiliated with, endorsed by, or sponsored by DonorDock. It references the publicly available Swagger specification (https://public-api.donordock.com/swagger/docs/v1) for educational and integration purposes. The information may be outdated or incomplete. Always refer to the official DonorDock documentation for current API specifications.
