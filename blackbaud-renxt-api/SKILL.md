---
name: blackbaud-renxt-api
description: Blackbaud Raiser's Edge NXT SKY API integration reference for building nonprofit fundraising and donor management features. Use when writing code that interacts with the Blackbaud SKY API, including fetchers, normalizers, or any backend integration with Raiser's Edge NXT data. Covers Constituents, Gifts, Fundraising (Campaigns/Funds/Appeals), Opportunities, Actions/Interactions, and Events.
---

# Blackbaud Raiser's Edge NXT SKY API

Reference for integrating with the Blackbaud SKY API for Raiser's Edge NXT (OpenAPI 3.0.1). Sourced from official Blackbaud developer portal specs.

## Base URL

```
https://api.sky.blackbaud.com
```

API modules are accessed via versioned path segments:

| Module | Server URL | Operations |
|--------|-----------|------------|
| Constituent | `https://api.sky.blackbaud.com/constituent/v1` | 159 |
| Gift | `https://api.sky.blackbaud.com/gift/v1` | 28 |
| Gift v2 | `https://api.sky.blackbaud.com/gft-gifts` | 10 |
| Fundraising | `https://api.sky.blackbaud.com/fundraising/v1` | 53 |
| Opportunity | `https://api.sky.blackbaud.com/opportunity/v1` | 19 |
| Event | `https://api.sky.blackbaud.com/event` | 65 |

Note: The Constituent API includes Actions, Ratings, Prospect Status, and Giving Summary endpoints.

## Authentication

**OAuth 2.0 Authorization Code Flow:**

| Detail | Value |
|--------|-------|
| Authorization URL | `https://oauth2.sky.blackbaud.com/authorization` |
| Token URL | `https://oauth2.sky.blackbaud.com/token` |
| Token Lifespan | 60 minutes |
| Scopes | Not currently utilized |

**Required credentials:**
- **Application ID** (client_id) — from [Blackbaud developer portal](https://developer.blackbaud.com/)
- **Client Secret** — from app registration
- **API Subscription Key** — from [subscriptions page](https://developer.blackbaud.com/subscriptions/)

**Required headers on every API call:**
```
Authorization: Bearer {access_token}
Bb-Api-Subscription-Key: {subscription_key}
Content-Type: application/json
```

## Pagination

- Uses `limit` and `offset` query parameters
- Default limit: 500 records
- Maximum limit: 5,000 records (some endpoints allow up to 10,000)
- List responses include a `count` field

## Rate Limits & Throttling

- **Rate limit exceeded**: HTTP `429` with `Retry-After` header
- **Quota limit exceeded**: HTTP `403` with `Retry-After` header
- Implement exponential backoff when receiving 429/403

## Key Endpoints

### Constituent API (159 operations)

Server: `https://api.sky.blackbaud.com/constituent/v1`

**Constituents:**
```
GET    /constituents                                    # Constituent list
POST   /constituents                                    # Constituent (Create)
GET    /constituents/search                             # Constituent (Search)
GET    /constituents/duplicatesearch                    # Constituent (Duplicate search)
POST   /constituents/convert/{non_constituent_id}       # Constituent (Convert)
GET    /constituents/{constituent_id}                   # Constituent (Get)
PATCH  /constituents/{constituent_id}                   # Constituent (Edit)
DELETE /constituents/{constituent_id}                   # Constituent (Delete)
```

**Constituent sub-resources** (list on constituent, full CRUD via top-level):
```
/addresses                    # Addresses (GET all, POST, PATCH, DELETE)
/aliases                      # Aliases (POST, PATCH, DELETE)
/constituentcodes             # Constituent codes (POST, PATCH, DELETE)
/educations                   # Education records (GET all, POST, PATCH, DELETE)
/emailaddresses               # Email addresses (GET all, POST, PATCH, DELETE)
/nameformats                  # Name formats (POST, PATCH, DELETE)
/primarynameformats           # Primary name formats (POST, PATCH, DELETE)
/notes                        # Notes (GET all, POST, GET by id, PATCH, DELETE)
/onlinepresences              # Online presences (GET all, POST, PATCH, DELETE)
/phones                       # Phones (GET all, POST, PATCH, DELETE)
/relationships                # Relationships (GET all, POST, PATCH, DELETE)
/ratings                      # Ratings (POST, PATCH, DELETE)
/communicationpreferences     # Communication prefs (GET, POST, PATCH, DELETE)
/constituents/attachments     # Attachments (POST, PATCH, DELETE)
/constituents/customfields    # Custom fields (GET all, POST, PATCH, DELETE)
/documents                    # Document upload (POST)
```

**Constituent sub-resource lists** (GET on a single constituent):
```
/constituents/{id}/actions                       # Actions
/constituents/{id}/addresses                     # Addresses
/constituents/{id}/aliases                       # Aliases
/constituents/{id}/appeals                       # Appeals
/constituents/{id}/attachments                   # Attachments
/constituents/{id}/communicationpreferences      # Communication prefs
/constituents/{id}/constituentcodes              # Constituent codes
/constituents/{id}/customfields                  # Custom fields
/constituents/{id}/educations                    # Education records
/constituents/{id}/emailaddresses                # Email addresses
/constituents/{id}/fundraiserassignments         # Fundraiser assignments
/constituents/{id}/fundraisers                   # Fundraisers
/constituents/{id}/memberships                   # Memberships
/constituents/{id}/nameformats/summary           # Name format summary
/constituents/{id}/notes                         # Notes
/constituents/{id}/onlinepresences               # Online presences
/constituents/{id}/phones                        # Phones
/constituents/{id}/profilepicture                # Profile picture (GET, PATCH)
/constituents/{id}/prospectstatus                # Prospect status
/constituents/{id}/prospectstatushistories       # Prospect status history
/constituents/{id}/ratings                       # Ratings
/constituents/{id}/relationships                 # Relationships
```

**Giving summaries** (GET on constituent):
```
/constituents/{id}/givingsummary/first           # First gift
/constituents/{id}/givingsummary/greatest        # Greatest gift
/constituents/{id}/givingsummary/latest          # Latest gift
/constituents/{id}/givingsummary/lifetimegiving  # Lifetime giving
```

**Batch/collection create endpoints:**
```
POST   /constituents/{id}/aliascollection          # Alias collection (Create)
POST   /constituents/{id}/customfieldcollection    # Custom field collection (Create)
POST   /phonescollection                           # Phone collection (Create)
```

**Education sub-resources:**
```
POST   /educations/customfields                    # Education custom field (Create)
PATCH  /educations/customfields/{id}               # Education custom field (Edit)
DELETE /educations/customfields/{id}               # Education custom field (Delete)
GET    /educations/{id}/customfields               # Education custom field list
```

**Actions (included in Constituent API):**
```
GET    /actions                                    # Action list (All constituents)
POST   /actions                                    # Action (Create)
GET    /actions/{action_id}                        # Action (Get)
PATCH  /actions/{action_id}                        # Action (Edit)
DELETE /actions/{action_id}                        # Action (Delete)
POST   /actions/attachments                        # Attachment (Create)
PATCH  /actions/attachments/{id}                   # Attachment (Edit)
DELETE /actions/attachments/{id}                   # Attachment (Delete)
GET    /actions/{id}/attachments                   # Attachment list
POST   /actions/customfields                       # Custom field (Create)
PATCH  /actions/customfields/{id}                  # Custom field (Edit)
DELETE /actions/customfields/{id}                  # Custom field (Delete)
GET    /actions/{id}/customfields                  # Custom field list
```

**Type/lookup endpoints** (GET):
```
/actionlocations              /actionstatustypes          /actiontypes
/addresstypes                 /aliastypes                 /attachmenttags
/constituentcodetypes         /countries                  /currencyconfiguration
/emailaddresstypes            /genders                    /maritalstatuses
/nameformatconfigurations     /nameformattypes            /notetypes
/onlinepresencetypes          /organizationcontacttypes   /phonetypes
/ratings/categories           /ratings/categories/values  /ratings/sources
/relationshiptypes            /suffixes                   /titles
/educations/degreeclasses     /educations/degrees         /educations/departments
/educations/faculties         /educations/schools         /educations/statuses
/educations/subjects          /educations/types
```

### Gift API (28 operations)

Server: `https://api.sky.blackbaud.com/gift/v1`

```
GET    /gifts                                          # Gift list
POST   /gifts                                          # Gift (Create)
POST   /gifts/list                                     # Gift list (by criteria)
GET    /gifts/{gift_id}                                # Gift (Get)
PATCH  /gifts/{gift_id}                                # Gift (Edit)
DELETE /gifts/{gift_id}                                # Gift (Delete)
POST   /giftbatches/{batch_id}/gifts                   # Gift (Batch)
PATCH  /giftacknowledgements/{acknowledgement_id}      # Gift acknowledgement (Edit)
PATCH  /giftreceipts/{receipt_id}                       # Gift receipt (Edit)
```

**Gift sub-resources:**
```
POST   /gifts/attachments                              # Attachment (Create)
PATCH  /gifts/attachments/{id}                         # Attachment (Edit)
DELETE /gifts/attachments/{id}                         # Attachment (Delete)
GET    /gifts/{id}/attachments                         # Attachment list
GET    /gifts/customfields                             # Custom field list (All gifts)
POST   /gifts/customfields                             # Custom field (Create)
POST   /gifts/customfields/categories                  # Custom field category (GetOrCreate)
PATCH  /gifts/customfields/{id}                        # Custom field (Edit)
DELETE /gifts/customfields/{id}                        # Custom field (Delete)
GET    /gifts/{id}/customfields                        # Custom field list (Single gift)
POST   /gifts/{id}/customfieldcollection               # Custom field collection (Create)
```

**Recurring gifts:**
```
GET    /recurringgifts/{gift_id}/canbeconverted        # Recurring gift eligibility for automation
POST   /recurringgifts/{gift_id}/converttoautomatic    # Automate recurring gift
PUT    /recurringgifts/{gift_id}/status                # Gift status (Edit)
```

**Lookups:**
```
GET    /attachmenttags                                 # Attachment tags
GET    /giftsubtypes                                   # Gift subtypes
POST   /documents                                      # Document (Create)
GET    /gifts/customfields/categories                  # Gift custom field categories
GET    /gifts/customfields/categories/values           # Gift custom field category values
```

### Gift v2 API (10 operations, PREVIEW)

Server: `https://api.sky.blackbaud.com/gft-gifts`

```
POST   /v2/gifts                                       # Create a gift
POST   /v2/gifts/generateinstallments                  # Generate pledge installments from schedule
GET    /v2/gifts/{gift_id}/installments                # Get pledge installments
POST   /v2/gifts/{gift_id}/installments                # Add pledge installments
GET    /v2/gifts/{gift_id}/pledgepayments              # Get pledge payments
POST   /v2/gifts/{gift_id}/stock/sell                  # Sell a stock gift
GET    /v2/batchgifts/{batchGiftId}                    # Get batch gift
PATCH  /v2/batchgifts/{batchGiftId}                    # Edit batch gift
POST   /v2/batchgifts/{batchId}                        # Add gifts to batch
PATCH  /v2/recurringgifts/{gift_id}/amendments/paymentinformation  # Edit recurring gift payment info
```

### Fundraising API (53 operations)

Server: `https://api.sky.blackbaud.com/fundraising/v1`

**Campaigns:**
```
GET    /campaigns                                      # Campaign list
GET    /campaigns/{campaign_id}                        # Campaign (Get)
GET    /campaigns/categories                           # Campaign categories
POST   /campaigns/attachments                          # Attachment (Create)
PATCH  /campaigns/attachments/{id}                     # Attachment (Edit)
DELETE /campaigns/attachments/{id}                     # Attachment (Delete)
GET    /campaigns/{id}/attachments                     # Attachment list
POST   /campaigns/customfields                         # Custom field (Create)
PATCH  /campaigns/customfields/{id}                    # Custom field (Edit)
DELETE /campaigns/customfields/{id}                    # Custom field (Delete)
GET    /campaigns/{id}/customfields                    # Custom field list
GET    /campaigns/customfields/categories              # Custom field categories
GET    /campaigns/customfields/categories/values       # Custom field category values
```

**Funds:**
```
GET    /funds                                          # Fund list
GET    /funds/{fund_id}                                # Fund (Get)
GET    /funds/categories                               # Fund categories
POST   /funds/attachments                              # Attachment (Create)
PATCH  /funds/attachments/{id}                         # Attachment (Edit)
DELETE /funds/attachments/{id}                         # Attachment (Delete)
GET    /funds/{id}/attachments                         # Attachment list
POST   /funds/customfields                             # Custom field (Create)
PATCH  /funds/customfields/{id}                        # Custom field (Edit)
DELETE /funds/customfields/{id}                        # Custom field (Delete)
GET    /funds/{id}/customfields                        # Custom field list
GET    /funds/customfields/categories                  # Custom field categories
GET    /funds/customfields/categories/values           # Custom field category values
```

**Appeals:**
```
GET    /appeals                                        # Appeal list
GET    /appeals/{appeal_id}                            # Appeal (Get)
GET    /appeals/categories                             # Appeal categories
POST   /appeals/attachments                            # Attachment (Create)
PATCH  /appeals/attachments/{id}                       # Attachment (Edit)
DELETE /appeals/attachments/{id}                       # Attachment (Delete)
GET    /appeals/{id}/attachments                       # Attachment list
POST   /appeals/customfields                           # Custom field (Create)
PATCH  /appeals/customfields/{id}                      # Custom field (Edit)
DELETE /appeals/customfields/{id}                      # Custom field (Delete)
GET    /appeals/{id}/customfields                      # Custom field list
GET    /appeals/customfields/categories                # Custom field categories
GET    /appeals/customfields/categories/values         # Custom field category values
```

**Packages:**
```
GET    /packages                                       # Package list
GET    /packages/{package_id}                          # Package (Get)
```

**Fundraisers:**
```
POST   /fundraisers/assignments                        # Assignment (Create)
PATCH  /fundraisers/assignments/{id}                   # Assignment (Edit)
DELETE /fundraisers/assignments/{id}                   # Assignment (Delete)
GET    /fundraisers/{id}/assignments                   # Assignment list
POST   /fundraisers/goals                              # Goal (Create)
PATCH  /fundraisers/goals/{id}                         # Goal (Edit)
DELETE /fundraisers/goals/{id}                         # Goal (Delete)
GET    /fundraisers/goals/categories                   # Goal categories
GET    /fundraisers/types                              # Fundraiser types
GET    /fundraisers/{id}/goals                         # Goal list
```

**Other:**
```
GET    /attachmenttags                                 # Attachment tags
POST   /documents                                      # Document (Create)
```

### Opportunity API (19 operations)

Server: `https://api.sky.blackbaud.com/opportunity/v1`

```
GET    /opportunities                                  # Opportunity list
POST   /opportunities                                  # Opportunity (Create)
GET    /opportunities/{opportunity_id}                 # Opportunity (Get)
PATCH  /opportunities/{opportunity_id}                 # Opportunity (Edit)
GET    /opportunities/{id}/statushistories             # Status history
POST   /opportunities/attachments                      # Attachment (Create)
PATCH  /opportunities/attachments/{id}                 # Attachment (Edit)
DELETE /opportunities/attachments/{id}                 # Attachment (Delete)
GET    /opportunities/{id}/attachments                 # Attachment list
POST   /opportunities/customfields                     # Custom field (Create)
PATCH  /opportunities/customfields/{id}                # Custom field (Edit)
DELETE /opportunities/customfields/{id}                # Custom field (Delete)
GET    /opportunities/{id}/customfields                # Custom field list
GET    /opportunities/customfields/categories          # Custom field categories
GET    /opportunities/customfields/categories/values   # Custom field category values
GET    /opportunitypurposes                            # Opportunity purposes
GET    /opportunitystatuses                            # Opportunity statuses
GET    /attachmenttags                                 # Attachment tags
POST   /documents                                      # Document (Create)
```

### Event API (65 operations)

Server: `https://api.sky.blackbaud.com/event`

**Events:**
```
GET    /v1/eventlist                                    # Event list
POST   /v1/events                                      # Event (Create)
GET    /v1/events/{event_id}                           # Event (Get)
PATCH  /v1/events/{event_id}                           # Event (Edit)
DELETE /v1/events/{event_id}                           # Event (Delete)
GET    /v2/events/{event_id}                           # Event v2 (Get, PREVIEW)
```

**Event sub-resources:**
```
/v1/events/{id}/attachments                     # Attachments (GET list, POST, GET by id, PATCH, DELETE)
/v1/events/{id}/eventfees                       # Event fees (GET, POST)
/v1/events/{id}/eventparticipantoptions         # Participant options (GET, POST)
/v1/events/{id}/participants                    # Participants (GET, POST)
/v1/events/{id}/expenses                        # Expenses (GET, POST, PREVIEW)
/v1/events/{id}/customfields                    # Custom fields (GET, PREVIEW)
```

**Event categories & levels:**
```
GET    /v1/eventcategories                             # Event categories
POST   /v1/eventcategories                             # Create category
PATCH  /v1/eventcategories/{id}                        # Edit category
DELETE /v1/eventcategories/{id}                        # Delete category
GET    /v1/participationlevels                         # Participation levels
POST   /v1/participationlevels                         # Create level
PATCH  /v1/participationlevels/{id}                    # Edit level
DELETE /v1/participationlevels/{id}                    # Delete level
```

**Event fees & options (top-level edit/delete):**
```
PATCH  /v1/eventfees/{fee_id}                          # Edit event fee
DELETE /v1/eventfees/{fee_id}                          # Delete event fee
PATCH  /v1/eventparticipantoptions/{option_id}         # Edit event participant option
DELETE /v1/eventparticipantoptions/{option_id}         # Delete event participant option
```

**Event custom fields (PREVIEW):**
```
POST   /v1/events/customfields                         # Create
PATCH  /v1/events/customfields/{id}                    # Edit
DELETE /v1/events/customfields/{id}                    # Delete
GET    /v1/events/customfields/categories/details      # Category details
GET    /v1/events/customfields/categories/values       # Category values
```

**Participants:**
```
GET    /v1/participants/{participant_id}               # Participant (Get)
PATCH  /v1/participants/{participant_id}               # Participant (Edit)
DELETE /v1/participants/{participant_id}               # Participant (Delete)
GET    /v1/participants/{id}/donations                 # Donations (GET, POST)
GET    /v1/participants/{id}/fees                      # Fees (GET, POST)
GET    /v1/participants/{id}/feepayments               # Fee payments (GET, POST)
GET    /v1/participants/{id}/participantoptions        # Options (GET, POST)
GET    /v1/participants/{id}/pledges                   # Pledges (GET, PREVIEW)
GET    /v1/participants/{id}/seating                   # Seating (GET, PATCH, PREVIEW)
GET    /v1/constituents/{id}/eventparticipation        # Constituent participation (GET, PREVIEW)
```

**Participant sub-resource deletes:**
```
DELETE /v1/participantdonations/{id}                   # Delete donation
DELETE /v1/participantfees/{id}                        # Delete fee
DELETE /v1/participantfeepayments/{id}                 # Delete fee payment
PATCH  /v1/participantoptions/{option_id}              # Edit option
DELETE /v1/participantoptions/{option_id}              # Delete option
```

**Other:**
```
GET    /v1/eventattachmenttags                         # Attachment tags
POST   /v1/eventattachmentupload                       # Attachment upload
GET    /v1/eventgroups                                 # Event groups (PREVIEW)
POST   /v1/events/copyparticipantoptions               # Copy participant options (PREVIEW)
GET    /v1/expenses/{expense_id}                       # Expense (Get, PREVIEW)
PATCH  /v1/expenses/{expense_id}                       # Expense (Edit, PREVIEW)
DELETE /v1/expenses/{expense_id}                       # Expense (Delete, PREVIEW)
GET    /v1/expensetypes                                # Expense types (PREVIEW)
```

## Key Entities

| Entity | Description |
|--------|-------------|
| Constituent | Individual or organization donor/contact record |
| Gift | A donation, pledge, recurring gift, or gift-in-kind |
| Campaign | Top-level fundraising initiative |
| Fund | Financial designation for a gift |
| Appeal | A solicitation effort within a campaign |
| Package | Specific mailing or communication within an appeal |
| Opportunity | A prospective major gift being tracked |
| Action | An interaction/activity logged against a constituent |
| Event | A fundraising or stewardship event |
| Participant | A constituent registered for an event |
| Rating | Prospect/wealth rating on a constituent |
| Relationship | Connection between two constituents |
| Education | Educational history of a constituent |
| Membership | Membership records for a constituent |

## Common Patterns

- **Fuzzy dates**: `{ "d": int, "m": int, "y": int }` — allows partial dates
- **Currency values**: `{ "value": 100.00 }` — wrapped in an object
- **Lookup IDs**: User-defined identifiers for external system mapping
- **Custom fields**: Available on most entities via `/customfields` sub-endpoints
- **Attachments**: Available on most entities via `/attachments` sub-endpoints
- **Collection endpoints**: Batch-create multiple sub-resources in one call (e.g., `/aliascollection`, `/customfieldcollection`)
- **Type/lookup endpoints**: Dynamic picklist values (e.g., `/addresstypes`, `/genders`, `/notetypes`)
- **List responses**: `{ "count": int, "value": [...] }`
- **Filtering**: Most list endpoints support `date_added`, `last_modified`, `include_inactive`
- **PREVIEW endpoints**: Marked as preview — may change without notice

## Full API Reference

For complete endpoint specifications, request/response schemas, and parameter details, search the OpenAPI 3.0.1 spec files (do not read full files — they total ~2.5MB):

```
references/constituent.json     # 159 operations — constituents, actions, ratings, giving summaries
references/gift.json            # 28 operations  — gifts, acknowledgements, receipts, recurring
references/gift-v2.json         # 10 operations  — gift v2, pledges, batch gifts (PREVIEW)
references/fundraising.json     # 53 operations  — campaigns, funds, appeals, packages, fundraisers
references/opportunity.json     # 19 operations  — opportunities, status histories
references/event.json           # 65 operations  — events, participants, fees, expenses
```

Search patterns (use grep or jq):
- All paths: `jq '.paths | keys' references/constituent.json`
- Specific endpoint: `jq '.paths["/constituents/{constituent_id}"]' references/constituent.json`
- All schemas: `jq '.components.schemas | keys' references/gift.json`
- Specific schema: `jq '.components.schemas["GiftCreate"]' references/gift.json`

## Disclaimer

This skill is not affiliated with, endorsed by, or sponsored by Blackbaud. It references publicly available API documentation for educational and integration purposes. The information may be outdated or incomplete. Always refer to the official Blackbaud documentation for the most current API specifications.
