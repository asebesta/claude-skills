# DonorDock Public API — Endpoint Catalog

Complete catalog of the DonorDock Public API v1, generated from the official Swagger spec (`https://public-api.donordock.com/swagger/docs/v1`).

All endpoints: HTTP Basic auth (`APIKey:APISecret` Base64 in `Authorization` header), base URL `https://public-api.donordock.com`.

## Contents

- [Common list parameters](#common-list-parameters)
- [Contacts](#contacts)
- [Gifts](#gifts)
- [Gift Batches](#gift-batches)
- [Activities](#activities)
- [Campaigns](#campaigns)
- [Appeals](#appeals)
- [Funds](#funds)
- [Badges](#badges)
- [Marketing Lists](#marketing-lists)
- [Events](#events)
- [Emails](#emails)
- [MetaData](#metadata)

Object field definitions are in [schemas.md](schemas.md).

## Common list parameters

Every "list" (paged GET) endpoint accepts these unless noted:

| Param | Type | Description |
|-------|------|-------------|
| `skip` | integer | Offset |
| `take` | integer | Page size, **max 1000** |
| `fromDate` / `toDate` | date-time | Filter by `CreatedOn` (UTC) |
| `fromDateModified` / `toDateModified` | date-time | Filter by `ModifiedOn` (UTC) |
| `sortBy` | string | `CreatedOn` or `ModifiedOn` |
| `sortDir` | string | `ASC` or `DESC` |

Paged responses: `{ "TotalRecords": int, "CurrentRecords": int, "Data": [...] }`.

Search endpoints (`ContactSearch`, `GiftSearch`, `ActivitySearch`, `CampaignSearch`) take `skip`/`take` plus their own filters but **not** the modified-date/sort params.

## Contacts

```
GET  /api/v1/Contacts                    # List contacts → PageResponse[ZapierContact]
GET  /api/v1/Contacts/{contactId}        # Get contact by ID → ZapierContact
POST /api/v1/Contacts                    # Create contact (body: ZapierContact)
PUT  /api/v1/Contacts/{contactId}        # Update contact (body: ZapierContact)
GET  /api/v1/Contacts/ContactSearch      # Search contacts
```

`ContactSearch` query params: `skip`, `take`, `integrationId`, `accountNumber`, `memberId`, `email`, `phone`, `fromDate`, `toDate`, `badgeFilters`.

## Gifts

```
GET  /api/v1/Gifts                       # List gifts → PageResponse[ZapierGift]
GET  /api/v1/Gifts/{giftId}              # Get gift by ID → ZapierGift
POST /api/v1/Gifts                       # Create gift (body: ZapierGift)
GET  /api/v1/Gifts/GiftSearch            # Search gifts
```

`GET /api/v1/Gifts` extra params (beyond common list params):

| Param | Description |
|-------|-------------|
| `status` | Gift status(es), comma-delimited. `Received` (default), `Pledged`, `Cancelled`, `Pending`, `Processing` |
| `transactionType` | Transaction type(s), comma-delimited. `Donation`, `Membership`, `EventTicket`, `Grant` |

`GiftSearch` query params: `skip`, `take`, `integrationId`, `paymentId`, `contactIntegrationId`, `accountNumber`, `memberId`, `email`, `phone`, `fromDate`, `toDate`, `transactionType`, `status`.

There is **no gift update endpoint**.

## Gift Batches

Read-only. Closed batches only.

```
GET  /api/v1/GiftBatches                 # List closed gift batches → GiftBatchPageResponse
GET  /api/v1/GiftBatches/{id}            # Get a single gift batch by ID (integer id)
```

`GET /api/v1/GiftBatches` params: `skip`, `take` (max 1000), `fromDate`/`toDate` (filter by **ClosedDate**), `sortDir` (sorts by ClosedDate). No `sortBy`/modified-date params.

## Activities

```
GET  /api/v1/Activities                  # List activities → PageResponse[ZapierActivity]
GET  /api/v1/Activities/{activityId}     # Get activity by ID → ZapierActivity
POST /api/v1/Activities                  # Create activity (body: ZapierActivity)
PUT  /api/v1/Activities/{activityId}     # Update activity (body: ZapierActivity)
GET  /api/v1/ActivitySearch              # Search activities (note: NOT under /Activities)
```

`GET /api/v1/Activities` extra param: `excludeBulkEmailActivities` (boolean, default false).

`ActivitySearch` query params: `skip`, `take`, `integrationId`, `contactIntegrationId`, `accountNumber`, `memberId`, `email`, `phone`, `fromDate`, `toDate`, `activityTypes`.

## Campaigns

```
GET  /api/v1/Campaigns                   # List campaigns → PageResponse[ZapierCampaign]
GET  /api/v1/Campaigns/{campaignId}      # Get campaign by ID → ZapierCampaign
POST /api/v1/Campaigns                   # Create campaign (body: ZapierCampaign)
PUT  /api/v1/Campaigns/{campaignId}      # Update campaign (body: ZapierCampaign)
GET  /api/v1/Campaigns/CampaignSearch    # Search campaigns
```

`CampaignSearch` query params: `skip`, `take`, `integrationId`, `name`, `startDate`, `endDate`.

## Appeals

```
GET  /api/v1/Appeals                     # List appeals → PageResponse[ZapierAppeal]
GET  /api/v1/Appeals/{appealId}          # Get appeal by ID → ZapierAppeal
POST /api/v1/Appeals                     # Create appeal (body: ZapierAppeal)
```

No update or search endpoints.

## Funds

```
GET  /api/v1/Funds                       # List funds → PageResponse[ZapierFund]
GET  /api/v1/Funds/{fundId}              # Get fund by ID → ZapierFund
POST /api/v1/Funds                       # Create fund (body: ZapierFund)
```

No update or search endpoints.

## Badges

Badge assignments to contacts (not badge definitions).

```
GET    /api/v1/Badges                    # List contacts with badges → PageResponse[ZapierDonorBadge]
POST   /api/v1/Badges                    # Add a badge to a contact (body: ZapierDonorBadge)
DELETE /api/v1/Badges                    # Remove a badge from a contact (body: ZapierDonorBadge)
```

Note: DELETE takes a **body**, not a path/query ID.

## Marketing Lists

Marketing list memberships (not list definitions).

```
GET  /api/v1/MarketingLists              # List contacts on marketing lists → PageResponse[ZapierMarketingListMember]
POST /api/v1/MarketingLists              # Add a contact to a marketing list (body: ZapierMarketingListMember)
```

No remove endpoint.

## Events

```
GET  /api/v1/Events/Attendance           # List event attendance records → PageResponse[ZapierEventAttendance]
POST /api/v1/Events/Attendance           # Create event attendance record (body: ZapierEventAttendance)
```

## Emails

```
POST /api/v1/Emails/SendTemplateEmail    # Send a template email to a contact (body: ZapierTemplateEmail)
```

Sends the specified email template to the specified contact. **Deducted from marketing email credits.** Identify the template by `TemplateId` (UUID) or `TemplateName`; identify the contact by any of the contact identifier fields.

## MetaData

```
GET /api/v1/MetaData/GetUserList                     # List users
GET /api/v1/MetaData/GetEmailTemplateList            # List email templates
GET /api/v1/MetaData/GetCustomFieldDefinitions       # Custom field definitions (query: entityType)
```

Use `GetCustomFieldDefinitions?entityType=...` to discover `FieldId`s before writing `CustomFields` on contacts, gifts, or activities. Use `GetEmailTemplateList` to find template IDs for `SendTemplateEmail`, and `GetUserList` for owner/assignee values.
