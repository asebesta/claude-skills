---
name: donorperfect-api
description: DonorPerfect Online XML API integration reference for nonprofit donor management and fundraising features. Use when writing code that interacts with the DonorPerfect XML API, including fetchers, normalizers, importers, or any backend integration with DP donor data. Covers donor/constituent records, gifts, pledges, recurring gifts, soft credits, split gifts, gift adjustments, contacts, tributes, flags, checkbox fields, UDFs, codes, addresses, links, EFT payment methods, and direct SQL SELECT queries against DP tables.
---

# DonorPerfect Online XML API

Reference for integrating with the **DonorPerfect Online (DP) XML API** (SofterWare, Inc.) — User Manual v7.1, corresponding to DonorPerfect Online 2024.02.16. The DP API is an HTTPS-only XML-returning API exposing both predefined stored-procedure-like calls and ad-hoc SQL SELECT queries against the underlying MS SQL Server 2019 database.

## Base URL

```
https://www.donorperfect.net/prod/xmlrequest.asp
```

All requests are HTTPS GET. There is one endpoint — operations are dispatched via the `action` query parameter.

## Authentication

Single API key per DP user account, provided by DonorPerfect Support / API Help Desk (`api@softerware.com`).

```
?apikey=<your-api-key>
```

| Rule | Detail |
|------|--------|
| Quoting | API key must NOT be wrapped in quotes |
| URL encoding | API key must NOT be URL-encoded |
| Position | Can appear before OR after `action`+`params` |
| User binding | Tied to a DP user account, but DP user permissions DO NOT restrict API calls — the key has full data access |
| Password rotation | DP user password expiry does NOT affect the API key |

> **Audit trail:** Most write calls accept an `@user_id` parameter (≤20 chars) for audit logging. This is a free-form string — not validated against actual DP users. Use your application name (e.g., `'MyAppName'`) so changes can be attributed.

## Request Anatomy

```
https://www.donorperfect.net/prod/xmlrequest.asp?apikey=xxxxx&action=dp_gifts&params=@donor_id=640
```

| Segment | Purpose |
|---------|---------|
| Preamble | `https://www.donorperfect.net/prod/xmlrequest.asp` — fixed |
| `apikey=...` | Credentials (no quotes, not URL-encoded) |
| `action=...` | Either a predefined procedure name (`dp_savegift`, etc.) OR a raw SQL statement (`SELECT ...`) |
| `params=...` | Comma-separated parameter list for predefined procedures; URL-encoded |

### Parameter Formats

**Named parameters (recommended — order-independent, easier to debug):**
```
&params=@donor_id=0, @first_name='Orianthi', @last_name='Panagaris', @user_id='MyAppName'
```

**Positional parameters (legacy, still supported):**
```
&params=0,'Orianthi','Panagaris',null,null,...
```

| Rule | Detail |
|------|--------|
| Date format | `'MM/DD/YYYY'` only — time values are NOT supported |
| Strings | Single-quoted |
| Escapes | Embed apostrophe as two single quotes: `'O''Reilly'` |
| Unicode | Prefix string with `N`: `@field=N'Phúc cho những'` (system must be Unicode-enabled by DP Support) |
| Empty/missing | Use `null`, NOT `''`. Searching `''` returns nothing |
| Mixing | Cannot mix named and positional parameters in a single call |
| URL encoding | Everything after `action=` should be URL-encoded; the apikey must NOT be |
| Whitespace | Do NOT put spaces in the leading portion of the URL — causes "@donor_id not supplied" errors |

## Response Format

All responses are XML. Each row is a `<record>` containing one `<field>` per column:

```xml
<result>
  <record>
    <field name="donor_id" id="donor_id" value="147"/>
    <field name="first_name" id="first_name" value="Orianthi"/>
    <field name="last_name" id="last_name" value="Panagaris"/>
    ...
  </record>
</result>
```

For create/update calls, the result is a single `<field>` with the new/affected ID:

```xml
<result>
  <record>
    <field name="" id="" value="10230" />
  </record>
</result>
```

## Limits & Admin

| Limit | Value |
|-------|-------|
| Row retrieval limit | **500 rows per query** — paginate with `TOP 500 ... WHERE id > {last_id} ORDER BY id` |
| Concurrent user blocking | None for API |
| SmartActions | **NOT triggered** by API writes |
| Logging | All API requests are logged by DP for troubleshooting and fraud detection |
| Service guarantee | Best effort — no SLA |
| API change policy | SofterWare reserves the right to change the interface; tracked in [DP Community Release Notes](https://softerware.force.com/dpcommunity/s/global-search/%22Release%20Notes%22) |

## Two Execution Modes

The DP API has **two distinct ways** to call it. Prefer Predefined Procedures whenever one fits.

### 1. Predefined Procedures

Stored-procedure-style calls. Invoked as `action=dp_<name>` with `&params=` containing named parameters.

### 2. Dynamic Queries (SQL SELECT)

Raw ANSI SQL passed as the action value — runs against the underlying MS SQL Server 2019 database.

```
&action=SELECT donor_id, first_name, last_name FROM dp WHERE last_name = 'bacon'
```

Supports `JOIN`, wildcards (`%`), `TOP N`, `ORDER BY`, `COALESCE`, etc. Only the SQL features documented in this skill are guaranteed to work — DP supports a limited SQL subset.

**Avoid `SELECT *` in production code** — slow and brittle to schema changes. Use it only for ad-hoc exploration of a single record.

## Predefined Procedures

### Donor / Constituent

| Procedure | Purpose |
|-----------|---------|
| `dp_donorsearch` | Search donors by demographic fields (`%` wildcard, NULL = match anything) |
| `dp_savedonor` | Create (`@donor_id=0`) or update donor; updates OVERWRITE existing values |
| `dp_saveaddress` | Create/update secondary "seasonal" address on DPADDRESS |
| `dp_saveotherinfo` | Create/update Other Info entry on DPTHERINFO (returns `other_id` for UDF saves) |
| `dp_savecontact` | Create/update Contact (activity/task) on DPCONTACT |
| `dp_savelink` | Create relationship link between two donors (reciprocal auto-created) |

### Gifts, Pledges, EFT

| Procedure | Purpose |
|-----------|---------|
| `dp_gifts` | List a predefined set of fields for all gifts of a donor |
| `dp_savegift` | Create/update gift, pledge payment, soft credit, split gift entry, or gift adjustment |
| `dp_savepledge` | Create/update a parent pledge (recurring gift schedule) |
| `dp_PaymentMethod_Insert` | Insert EFT payment method (DPPAYMENTMETHOD) — requires SafeSave Customer Vault ID |
| `dp_PaymentMethod_Update` | Update EFT payment method — MUST re-supply all existing values |

### Tributes (In Honor Of / In Memory Of)

| Procedure | Purpose |
|-----------|---------|
| `dp_tribAnon_MyTribSummary` | List all tributes (or active only) |
| `dp_tribAnon_Search` | Search tributes by name keyword |
| `dp_tribAnon_Create` | Create a new tribute |
| `dp_tribAnon_AssocTribsToGift` | Associate one or more tributes with a gift |
| `dp_tribAnon_SaveTribRecipient` | Add a notification recipient for one specific gift |
| `dp_tribNotif_Save` | Create the actual notification gift record (follow-up to `SaveTribRecipient`) |
| `dp_tribAnon_Update` | Update tribute properties AND recipient list (full set replace — include existing!) |

### Custom Fields, Codes, Checkboxes, Flags

| Procedure | Purpose |
|-----------|---------|
| `dp_save_udf_xml` | Save a single UDF value — `@matching_id` selects table (donor_id→DPUDF, gift_id→DPGIFTUDF, contact_id→DPCONTACTUDF, other_id→DPTHERINFOUDF, address_id→DPADDRESSUDF) |
| `dp_savecode` | Add/update DPCODES drop-down values (GL codes, solicit codes, campaigns, etc.) |
| `mergemultivalues` | **Preferred** — set the full set of checked codes for a checkbox field; unspecified codes get unchecked |
| `dp_savemultivalue_xml` | Set a single checkbox value (legacy — prefer `mergemultivalues`) |
| `dp_deletemultivalues_xml` | Delete ALL checked checkboxes on a screen tab for a donor |
| `dp_saveflag_xml` | Set a single flag on a donor (DPFLAGS — Main tab) |
| `dp_delflags_xml` | Delete ALL flags for a donor (individual flag delete is not supported) |

> Full parameter tables for every procedure are in **`references/procedures.json`**.

## Database Tables (Dynamic Queries)

Sources of truth for SELECT-style retrieval and for understanding the data model behind the procedures.

| Table | Purpose |
|-------|---------|
| `DP` | Primary donor / constituent record |
| `DPUDF` | User-defined fields on donors |
| `DPCODES` | Drop-down code values for all coded fields |
| `DPUSERMULTIVALUES` | Checkbox values (one row per checked code per donor) |
| `DPFLAGS` | Donor flags (top of Main tab) |
| `DPGIFT` | Gift / pledge / transaction records |
| `DPGIFTUDF` | UDFs on gifts (incl. `EFT` field that enables auto-charge) |
| `DPADDRESS` | Secondary / seasonal addresses (Address tab) |
| `DPADDRESSUDF` | UDFs on addresses |
| `DPLINK` | Donor-to-donor relationships (Links tab) |
| `DPCONTACT` | Contact / activity / task records (Contacts tab) |
| `DPCONTACTUDF` | UDFs on contacts |
| `DPTHERINFO` | "Other Info" tab records |
| `DPTHERINFOUDF` | UDFs on Other Info (Quebec Law 25 `PO_*` fields live here) |
| `DPTRIBUTESANON` | Tributes — name, type, active flag, notification person |
| `DPTRIBUTESANON_GIFTASSOC` | Gift ↔ tribute many-to-many association |
| `DPTRIBUTESANON_RECIPIENTS` | Tribute recipient list |
| `DPPAYMENTMETHOD` | EFT payment methods (Accounts tab) |
| `SD_FIELD` | Field metadata — query before UDF writes to check field exists |

> Full column lists and notes are in **`references/tables.json`**.

## Key Entities & Relationships

| Entity | Description |
|--------|-------------|
| Donor / Constituent | Individual or organization (`ORG_REC='Y'`) record on DP |
| Gift | A donation, pledge, pledge payment, soft credit, or adjustment on DPGIFT |
| Pledge | Recurring-gift schedule (`RECORD_TYPE='P'`); payments are separate `RECORD_TYPE='G'` gifts linked via `PLINK` |
| Split Gift | A gift split across designations: Main (`M`) + children (`G` with `GLINK`→Main, `SPLIT_GIFT='Y'`) |
| Soft Credit | A "credit" gift (`RECORD_TYPE='S'`) with `GLINK`→actual gift |
| Adjustment | 3-record chain: Original (`A`) + Adjustment (`H`) + Resulting (`G`/`C`/`J`), linked via `GLINK`/`ALINK` |
| Contact | Activity / task / interaction record on DPCONTACT |
| Other Info | Generic dated record on DPTHERINFO (anchor for arbitrary UDFs) |
| Tribute | "In Honor Of" / "In Memory Of" designation with recipients and gift associations |
| Flag | A simple boolean tag on the donor (Main tab) — uses DPCODES with `FIELD_NAME='FLAG'` |
| Checkbox field | Multi-value selection (e.g., Donor Interests) stored as rows in DPUSERMULTIVALUES |
| UDF (User Defined Field) | Custom field on donor / gift / contact / other / address — typed C/D/N |
| EFT Payment Method | Stored payment method on DPPAYMENTMETHOD, tied to SafeSave Customer Vault |

## Common Patterns

### Pagination Around the 500-Row Limit

```sql
SELECT TOP 500 code, description FROM dpcodes
WHERE field_name='SOLICIT_CODE' AND code > '{last code}'
ORDER BY code
```

### Delta Sync — Recent Gift Changes

```sql
SELECT TOP 500 gift_id, amount, created_date, modified_date, gl_code
FROM dpgift
WHERE COALESCE(DPGIFT.MODIFIED_DATE, DPGIFT.CREATED_DATE) >= '{date}'
  AND gift_id > {last_gift_id}
ORDER BY gift_id
```

`COALESCE` returns `modified_date` if non-null, otherwise `created_date` — so new and modified gifts both come through.

### Created / Modified Audit Fields

Not directly writable, but populated automatically:

- `@user_id` → `created_by` on new records, `modified_by` on updates to existing records
- `created_date` → today on new records
- `modified_date` → today on updates to existing records

### Soft Credits

A soft credit recognizes Donor B for a gift that Donor A actually made.

```
RECORD_TYPE = 'S'
DONOR_ID    = <recognized donor>
GLINK       = <gift_id of the actual gift>
AMOUNT      = <same as actual gift>
```

Create with `dp_savegift` with `@record_type='S'` and `@glink=<actual gift_id>`.

### Split Gifts

A split gift divides one transaction across multiple designations (e.g., $100 split $75 Building Fund / $25 General).

| Role | record_type | split_gift | glink | Financial fields |
|------|-------------|------------|-------|------------------|
| Main (header) | `M` | `N` | (none) | Set to literal `'SEE_SPLIT'`: `@gl_code='SEE_SPLIT'`, `@solicit_code='SEE_SPLIT'`, etc. |
| Each child | `G` | `Y` | `<Main gift_id>` | Real code values |

Create Main first, then each child with `glink=<main gift_id>`.

### Pledges & Pledge Payments

1. **Create the parent pledge** with `dp_savepledge` — `RECORD_TYPE='P'`, `@total`, `@bill`, `@frequency` (`M`/`Q`/`S`/`A`).
2. **For EFT auto-processing**, set the parent pledge's `DPGIFTUDF.EFT='Y'` using `dp_save_udf_xml`:
   ```
   action=dp_save_udf_xml&params=@matching_id={pledge gift_id}, @field_name='EFT',
     @data_type='C', @char_value='Y', @date_value=null, @number_value=null, @user_id='MyApp'
   ```
3. **Populate `@vault_id`** on the pledge with the SafeSave Vault ID — required for the pledge to be active.
4. **Create a payment method** via `dp_PaymentMethod_Insert` (after creating the SafeSave Customer Vault ID).
5. **Subsequent pledge payments** are regular gifts (`dp_savegift` with `@record_type='G'`, `@pledge_payment='Y'`, `@plink=<parent pledge gift_id>`) — or DP processes them automatically via EFT once set up.

### Gift Adjustments (e.g., Refunds)

DonorPerfect represents an adjustment as a **three-record chain**:

| Role | record_type | gift_id | gift_date | amount | Links |
|------|-------------|---------|-----------|--------|-------|
| Original | `A` (was `G`) | existing | original date | original amount | — |
| Adjustment | `H` | new | today | delta (negative for refund) | `glink`=original gift_id |
| Resulting | `G` (or `C`/`J` if reduced to 0) | new | original date | new amount | `alink`=original gift_id |

Workflow:
1. SELECT existing gift to capture all field values.
2. Update original gift via `dp_savegift` setting `@record_type='A'` (everything else unchanged).
3. Create Adjustment gift via `dp_savegift` with delta amount and `@glink`.
4. Create Resulting gift via `dp_savegift` with new amount, `@alink`, and `gift_narrative` appended.

If the original gift had UDF or other extra field data, the Resulting gift should mirror it.

### Checkbox Fields vs. Flags

These are NOT the same — keep them separate:

| | Checkbox Fields | Flags |
|---|---|---|
| Stored in | `DPUSERMULTIVALUES` | `DPFLAGS` |
| UI location | Bio / Other tabs (e.g., Donor Interests) | Main tab top |
| Set | `mergemultivalues` (preferred) | `dp_saveflag_xml` |
| Unset/replace | `mergemultivalues` (omit codes to unset) | `dp_delflags_xml` (deletes ALL flags only) |
| Field types | Per-field (`FIELD_NAME` in DPUSERMULTIVALUES) | Single field with `FIELD_NAME='FLAG'` in DPCODES |

**Reading currently-set checkbox values:**
```sql
SELECT field_name, matching_id, code FROM dpusermultivalues
WHERE field_name='DONINTS' AND matching_id={donor_id}
```

**Reading currently-set flags:**
```sql
SELECT * FROM dpflags WHERE donor_id={donor_id}
```

**Discovering valid codes for a field:**
```sql
SELECT code, description FROM dpcodes WHERE field_name='{field name}'
```

### Tributes Workflow

To add a tribute and notify a recipient about one specific gift:

1. **Lookup or create the tribute.** Use `dp_tribAnon_Search` to find existing, or `dp_tribAnon_Create` with `@DPCodeID` from `SELECT CODE, CODE_ID, DESCRIPTION FROM DPCODES WHERE FIELD_NAME='MEMORY_HONOR'` (typically `707`=In Honor Of, `708`=In Memory Of).
2. **Associate to the gift** with `dp_tribAnon_AssocTribsToGift`.
3. **Add a recipient for this gift** with `dp_tribAnon_SaveTribRecipient` (named-parameter syntax required).
4. **Create the notification record** with `dp_tribNotif_Save` — most fields mirror the original gift; markers are `@gift_type='SN'`, `@record_type='N'`, `@ty_letter_no='NT'`.

To update the recipient list for ALL gifts on a tribute, use `dp_tribAnon_Update` — but you MUST include existing recipients or they'll be removed:

```sql
SELECT r.tributeid, t.name, r.donor_id, r.createddate, t.activeflg
FROM dptributesanon t, dptributesanon_recipients r
WHERE t.tributeid = r.tributeid AND t.tributeid = {desired tributeid}
```

Then call with `@recipients=N'105|43256|323387|137'` (pipe-delimited, `N`-prefixed).

### User Defined Fields (UDFs)

`dp_save_udf_xml` writes to whichever UDF table matches your `@matching_id`:

| @matching_id | Table written |
|--------------|---------------|
| donor_id | DPUDF |
| gift_id | DPGIFTUDF |
| contact_id | DPCONTACTUDF |
| other_id | DPTHERINFOUDF |
| address_id | DPADDRESSUDF |

Set ONE of `@char_value` / `@date_value` / `@number_value` based on `@data_type` (`C`/`D`/`N`); set the other two to `null`. The UDF field must already exist in the DP system (Code Maintenance > Field Definitions).

### Codes (DPCODES) — Drop-Down Values

All coded fields (GL Code, Solicit Code, Campaign, Memory/Honor, Flag, Address Type, Donor Type, etc.) draw their valid values from `DPCODES`.

```sql
SELECT code, description FROM dpcodes WHERE field_name='{FIELD_NAME}'
```

Add/update via `dp_savecode`. Behavior of `@original_code`:

| Condition | Result |
|-----------|--------|
| `@original_code=@code` AND code exists | UPDATE the existing code |
| `@original_code=NULL` AND code exists | Returns `'2'`, no change |
| `@original_code=NULL` OR `@original_code=@code` AND code does NOT exist | CREATE new code |

Set `@inactive='N'` to ensure the code shows in UI dropdowns.

### Multi-Currency

Pass `@currency='USD'` / `'CAD'` / etc. on `dp_savegift` and `dp_savepledge`. If omitted on a pledge, defaults to USD.

### Receipt Delivery (`@receipt_delivery_g`)

| Code | Meaning |
|------|---------|
| `N` | Do not acknowledge |
| `E` | Email only |
| `B` | Email and letter |
| `L` | Letter only |

Canadian sites also have `@acknowledgepref`: `1AR` (Ack+Receipt), `2AD` (Ack/no Receipt), `3DD` (no Ack/no Receipt).

### UK Gift Aid

DP includes these fields for the UK Gift Aid tax incentive program:

| Table | Field | Purpose |
|-------|-------|---------|
| DP | `GIFT_AID_ELIGIBLE` | `'Y'`/`'NO'` — donor eligibility |
| DPUDF | `GA_TITLE` | Title used on gift aid charity donation |
| DPUDF | `GA_ADDRESS` | Foreign (non-UK) address textbox |
| DPGIFT | `GIFT_AID_ELIGIBLE_G` | `'Y'`/`'N'` — gift eligibility |
| DPGIFT | `GIFT_AID_DATE` | Date submitted to HMRC |
| DPGIFT | `GIFT_AID_AMT` | Portion eligible for tax relief |
| DPTHERINFO | `GA_START_DT` | Declaration start |
| DPTHERINFO | `GA_END_DT` | Declaration end |
| DPTHERINFO | `GA_DECL_ACTIVE` | `'Y'`/`'N'` — declaration active |

### Quebec Law 25 (Privacy & Consent)

Stored as UDFs — must be present in the DP system before writing. **Test first:**

```sql
SELECT DISTINCT field_name FROM sd_field
WHERE field_name LIKE 'PM_%' OR field_name LIKE 'PO_%'
```

`PM_*` fields live on DPUDF (Main); `PO_*` fields live on DPTHERINFOUDF (Other Info):

| Table | Field | Purpose |
|-------|-------|---------|
| DPUDF | `PM_CONSENT` | Consent given (Yes/No) |
| DPUDF | `PM_CONSENT_DT` | Actual consent date |
| DPUDF | `PM_CONSENT_EXPIRY` | Actual consent expiry date |
| DPUDF | `PM_DELETE` | Erasure requested (Yes/No) |
| DPUDF | `PM_DELETE_DT` | Erasure requested on |
| DPTHERINFOUDF | `PO_CONSENT`, `PO_CONSENT_DT`, `PO_CONSENT_EXPIRY`, `PO_DELETE`, `PO_DELETE_DT`, `PO_EXPORT_DT`, `PO_NOTES` | Per-event privacy/consent profile |

Save via `dp_save_udf_xml` with `@matching_id=@donor_id` for `PM_*` and `@matching_id=@other_id` for `PO_*`.

### Unicode

DP systems must be Unicode-enabled by Support to store UCS-2/UTF-16. Then prefix strings with `N`:

```
@first_name=N'Phúc cho những người'
```

> **Gotcha:** `dp_save_udf_xml` does NOT currently support Unicode via the `=N'xxx'` syntax — Unicode characters land as `?`. Workaround: contact DP API Desk.

## URL Encoding Example (PHP)

```php
$preamble = "https://www.donorperfect.net/prod/xmlrequest.asp?apikey=";
$key = "xxxxxxxxxxxxxxxxxx";
$action = "&action=dp_save_udf_xml&params=";
$payload = "@matching_id=640, @field_name='MRWMEMO', @char_value='Basic math = 5',
            @date_value=null, @number_value=null, @user_id='APITestCall'";
$encoded_APIcall = $preamble . $key . $action . urlencode($payload);
```

The apikey appears BEFORE `urlencode()`; only the payload is encoded.

## Full Reference

For complete parameter tables, edge cases, and original sample calls, the PDF and structured JSON are in `references/`:

```
references/procedures.json                                 # All 25 procedures with full parameter tables
references/tables.json                                     # All DP tables with column lists and notes
references/DPO_SUP_Manual_XML_API_Documentation050324.pdf  # Source v7.1 (May 2024)
```

Search patterns:
- All procedures: `jq '.procedures | keys' references/procedures.json`
- One procedure: `jq '.procedures.dp_savegift' references/procedures.json`
- All tables: `jq '.tables | keys' references/tables.json`
- Table columns: `jq '.tables.DPGIFT.key_columns' references/tables.json`
- PDF deep dive: `Read references/DPO_SUP_Manual_XML_API_Documentation050324.pdf` with a pages range

## Support

| Channel | Detail |
|---------|--------|
| API Help Desk | `api@softerware.com` (Mark Warren, XML API Consultant) |
| Phone | 1-888-637-7745 |
| Hours | Mon–Fri 8:30am–5:00pm EST |
| Emergencies | Additional email to `support@donorperfect.com` |

API support covers: call syntax, recommendations, error explanations, restoring API service after DP outages. It does NOT cover: writing/debugging your application, creating custom docs, or any work on code outside the DP API itself.

## Disclaimer

This skill is not affiliated with, endorsed by, or sponsored by SofterWare or DonorPerfect. It references publicly available API documentation for educational and integration purposes. The information may be outdated or incomplete — always refer to the official DonorPerfect documentation and release notes for the most current API specifications. Field availability (e.g., Quebec Law 25 UDFs, Unicode, EFT) depends on per-client configuration and add-ons; always test for field presence before writing.
