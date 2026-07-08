# DonorDock Public API — Object Schemas

Field definitions for every request/response object, generated from the official Swagger spec. All timestamps are ISO 8601 date-time strings (UTC). No fields are marked required in the spec — provide sensible identifiers (see "Linking records to contacts" in SKILL.md).

## Contents

- [Page envelopes](#page-envelopes)
- [ZapierContact](#zapiercontact)
- [ZapierGift](#zapiergift)
- [ZapierGiftBatch](#zapiergiftbatch)
- [ZapierActivity](#zapieractivity)
- [ZapierCampaign](#zapiercampaign)
- [ZapierAppeal](#zapierappeal)
- [ZapierFund](#zapierfund)
- [ZapierDonorBadge](#zapierdonorbadge)
- [ZapierMarketingListMember](#zapiermarketinglistmember)
- [ZapierEventAttendance](#zapiereventattendance)
- [ZapierTemplateEmail](#zapiertemplateemail)
- [ZapierCustomField](#zapiercustomfield)

Model names carry a `Zapier` prefix in the spec (the API grew out of DonorDock's Zapier integration); they are the general public-API objects.

## Page envelopes

`PageResponse[T]` (all paged lists) and `GiftBatchPageResponse`:

| Field | Type |
|-------|------|
| `TotalRecords` | integer — total matching records |
| `CurrentRecords` | integer — records in this page |
| `Data` | array of T |

## ZapierContact

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | DonorDock internal ID |
| `AccountNumber` | string | DonorDock account number |
| `MemberId` | string | External member ID |
| `IntegrationId` | string | External system's ID (set by your integration) |
| `Source` | string | Origin label for the record |
| `Title`, `FirstName`, `MiddleName`, `LastName`, `Suffix` | string | |
| `FullName`, `DisplayName`, `Nickname`, `FormerName` | string | |
| `OrganizationName` | string | For org contacts |
| `Addressee`, `Salutation` | string | Mail/greeting lines |
| `Email` | string | |
| `DOB` | date-time | |
| `Address1`, `Address2`, `Address3`, `City`, `StateOrProvince`, `PostalCode`, `Country` | string | |
| `MainPhone`, `MobilePhone`, `Fax`, `Website` | string | |
| `DoNotSolicit`, `Deceased` | boolean | |
| `BadAddress`, `Unsubscribed`, `BadMobileNumber`, `SMSUnsubscribed` | boolean | Communication flags |
| `Type` | string | Contact type |
| `Stage` | string | Donor stage |
| `Description`, `ExceptionNotes` | string | |
| `Employer`, `JobTitle` | string | |
| `SpouseFirst`, `SpouseLast` | string | |
| `Owner`, `Affiliation` | string | |
| `Badges` | string | Badge names (string, not array) |
| `MarketingLists` | string | List names (string, not array) |
| `GiftsInDateRange` | number | Read-only rollup |
| `DonationGiftsInDateRange`, `EventTicketGiftsInDateRange`, `MembershipGiftsInDateRange` | number | Read-only rollups |
| `VolunteerHoursInDateRange` | number | Read-only rollup |
| `CustomFields` | array of ZapierCustomField | |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

## ZapierGift

Gift-specific fields:

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | |
| `AccountNumber` | string | Gift account number |
| `ContactId`, `ContactMemberId`, `ContactIntegrationId` | string | Contact link (any one) |
| `ReceivedAmount` | number | |
| `NonDeductibleAmount`, `SoftCreditAmount`, `PledgedAmount` | number | |
| `FeeAmount`, `NetAmount` | number | |
| `FeesCovered` | boolean | |
| `Date` | date-time | Gift date |
| `Status` | string | `Received` (default), `Pledged`, `Cancelled`, `Pending`, `Processing` |
| `Type` | string | Gift type (payment method category) |
| `TransactionType` | string | `Donation`, `Membership`, `EventTicket`, `Grant` |
| `MembershipType`, `MembershipStart`, `MembershipEnd` | string / date-time | For membership gifts |
| `PaymentId` | string | Payment processor ID (searchable) |
| `CampaignName`, `AppealName`, `FundName`, `FundAccountNumber` | string | Attribution by name |
| `TributeDescription`, `PaymentDescription`, `Description` | string | |
| `TrackingCode` | string | |
| `IntegrationId`, `Source` | string | Your integration's keys |
| `DepositDate` | date-time | |
| `ReferenceNumber` | integer | |
| `GiftTags` | string | |
| `SendReceipt` | boolean | Trigger receipt on create |
| `ExceptionNotes` | string | |
| `OwnerName`, `Affiliation` | string | |
| `CustomFields` | array of ZapierCustomField | Gift custom fields |
| `ContactCustomFields` | array of ZapierCustomField | Contact custom fields |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

Plus denormalized contact fields (same meaning as on ZapierContact): `Title`, `FirstName`, `MiddleName`, `LastName`, `FullName`, `DisplayName`, `Nickname`, `FormerName`, `OrganizationName`, `Addressee`, `Salutation`, `Suffix`, `Email`, `DOB`, `Address1–3`, `City`, `StateOrProvince`, `PostalCode`, `Country`, `MainPhone`, `MobilePhone`, `Fax`, `Website`, `DoNotSolicit`, `Deceased`, `DonorType`, `Badges`, `MarketingLists`.

## ZapierGiftBatch

| Field | Type |
|-------|------|
| `Id` | integer |
| `Name` | string |
| `ClosedDate` | date-time |
| `Gifts` | array of ZapierGift |

## ZapierActivity

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | |
| `Subject`, `Body` | string | |
| `Type` | string | Activity type |
| `Status` | string | |
| `Priority` | string | |
| `Location` | string | |
| `Campaign`, `CampaignId`, `Appeal`, `AppealId` | string | Attribution |
| `ScheduledDate`, `DueDate`, `ActivityDate` | date-time | |
| `CompletedDate`, `CompletionNotes`, `CompletedBy` | date-time / string | |
| `ContactName`, `ContactId`, `ContactAccountNumber`, `ContactIntegrationId`, `ContactMemberId`, `ContactEmail` | string | Contact link (any one) |
| `AssignedToEmail`, `UserId` | string | Assignment |
| `VolunteerHours` | string | |
| `AskAmount`, `PlannedAskAmount`, `AskStage`, `AskProbability` | string | Major-gift ask tracking |
| `AddToActionBoard` | boolean | Surface on the Action Board |
| `Badges`, `MarketingLists` | string | |
| `IntegrationId`, `Source` | string | |
| `CustomFields` | array of ZapierCustomField | |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

## ZapierCampaign

| Field | Type |
|-------|------|
| `Id` | string |
| `Name`, `Description` | string |
| `StartDate`, `EndDate` | date-time |
| `IntegrationId`, `Source` | string |
| `CreatedOn`, `ModifiedOn` | date-time |

## ZapierAppeal

Same shape as ZapierCampaign plus:

| Field | Type |
|-------|------|
| `AppealType` | string |

## ZapierFund

| Field | Type |
|-------|------|
| `Id` | string |
| `Name`, `Description` | string |
| `AccountNumber` | string |
| `IntegrationId`, `Source` | string |
| `CreatedOn`, `ModifiedOn` | date-time |

## ZapierDonorBadge

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | |
| `BadgeName` | string | Badge to add/remove |
| `ContactName`, `ContactFirstName`, `ContactLastName` | string | |
| `ContactId`, `ContactAccountNumber`, `ContactMemberId`, `ContactEmail`, `ContactIntegrationId` | string | Contact link (any one) |
| `Source` | string | |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

## ZapierMarketingListMember

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | |
| `MarketingListName` | string | List to add the contact to |
| `ContactName`, `ContactFirstName`, `ContactLastName` | string | |
| `ContactId`, `ContactAccountNumber`, `ContactMemberId`, `ContactEmail` | string | Contact link (any one) |
| `Source` | string | |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

## ZapierEventAttendance

| Field | Type | Notes |
|-------|------|-------|
| `Id` | string | |
| `EventName`, `EventId` | string | |
| `Subject`, `Body` | string | |
| `Appeal` | string | |
| `Date` | date-time | |
| `AttendeeName`, `AttendeeEmail` | string | |
| `ContactId`, `ContactAccountNumber`, `ContactMemberId` | string | Contact link (any one) |
| `Badges`, `MarketingLists` | string | |
| `IntegrationId`, `Source` | string | |
| `CreatedOn`, `ModifiedOn` | date-time | Read-only |

## ZapierTemplateEmail

| Field | Type | Notes |
|-------|------|-------|
| `TemplateId` | string (UUID) | Template to send (or use `TemplateName`) |
| `TemplateName` | string | |
| `Subject` | string | Override subject |
| `FromEmail` | string | |
| `ContactId`, `ContactAccountNumber`, `ContactIntegrationId`, `ContactMemberId`, `ContactEmail` | string | Recipient contact (any one) |

## ZapierCustomField

| Field | Type | Notes |
|-------|------|-------|
| `FieldId` | integer | From `GET /api/v1/MetaData/GetCustomFieldDefinitions` |
| `Label` | string | |
| `Description` | string | |
| `DataType` | string | |
| `Value` | object | Field value |
| `IsArchived` | boolean | |
