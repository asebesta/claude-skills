# Claude Skills

A collection of reusable skills for AI agents. These skills provide procedural knowledge that enhances agent capabilities for specific tasks.

## Installation

Install any skill using [skills.sh](https://skills.sh):

```bash
npx skills add asebesta/claude-skills/<skill-name>
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [blackbaud-renxt-api](./blackbaud-renxt-api) | Blackbaud Raiser's Edge NXT SKY API integration reference for nonprofit fundraising and donor management |
| [bloomerang-api](./bloomerang-api) | Bloomerang CRM API integration reference for donor management features |
| [donorperfect-api](./donorperfect-api) | DonorPerfect Online XML API integration reference for donor management, gifts, pledges, tributes, and EFT |
| [ios-app-store-competitor-research](./ios-app-store-competitor-research) | Extract app metadata and screenshots from Apple App Store listings for competitive analysis |
| [paligo-api](./paligo-api) | Paligo CCMS REST API reference for content round-trips: tree walking, pulling/editing/validating/pushing topic XML, checkout, release status, and translations |
| [veo-video](./veo-video) | Generate videos using Google's Veo 3.1 API via the @google/genai SDK |
| [trmnl-plugins](./trmnl-plugins) | Build custom private plugins and dashboards for TRMNL e-ink displays (incl. TRMNL X): data strategies, Liquid templating, and Design Framework 3.1 markup |
| [virtuous-api](./virtuous-api) | Virtuous CRM API integration reference for donor management features |

### blackbaud-renxt-api

Reference for integrating with the Blackbaud SKY API for Raiser's Edge NXT. Use when writing code that interacts with the Blackbaud SKY API for nonprofit fundraising and donor management, including Constituents, Gifts, Fundraising (Campaigns/Funds/Appeals), Opportunities, Actions/Interactions, and Events.

**Install:**
```bash
npx skills add asebesta/claude-skills/blackbaud-renxt-api
```

**Triggers on:**
- Code involving Blackbaud SKY API or Raiser's Edge NXT integration
- Nonprofit fundraising and donor management features using Blackbaud
- Questions about Blackbaud RE NXT endpoints, authentication, or data models

### bloomerang-api

Reference for integrating with the Bloomerang CRM REST API. Use when writing code that interacts with the Bloomerang API for donor management, including Constituents, Transactions, Pledges, Campaigns, Appeals, Interactions, Tasks, and Relationships.

**Install:**
```bash
npx skills add asebesta/claude-skills/bloomerang-api
```

**Triggers on:**
- Code involving Bloomerang API integration
- Donor management features using Bloomerang
- Questions about Bloomerang endpoints, authentication, or data models

### donorperfect-api

Reference for integrating with the DonorPerfect Online XML API. Use when writing code that interacts with the DonorPerfect API for nonprofit donor management, including donor/constituent records, gifts, pledges, recurring gifts, soft credits, split gifts, gift adjustments, contacts, tributes, flags, checkbox fields, UDFs, codes, addresses, links, EFT payment methods, and direct SQL SELECT queries against DP tables.

**Install:**
```bash
npx skills add asebesta/claude-skills/donorperfect-api
```

**Triggers on:**
- Code involving DonorPerfect Online XML API integration
- Donor management features using DonorPerfect (SofterWare)
- Questions about DP procedures (`dp_savegift`, `dp_savedonor`, etc.), DP tables (DPGIFT, DPCODES, DPUDF, etc.), or DP data models
- XML API calls returning `<result>`/`<record>` from `donorperfect.net/prod/xmlrequest.asp`

### ios-app-store-competitor-research

Research competitor apps on the Apple App Store. Extracts comprehensive metadata including title, description, ratings, pricing, and downloads all screenshots at high resolution.

**Install:**
```bash
npx skills add asebesta/claude-skills/ios-app-store-competitor-research
```

**Triggers on:**
- App Store URLs (apps.apple.com)
- Requests like "research this app", "analyze competitor", "get app store info"

### paligo-api

Reference for integrating with the Paligo CCMS REST API. Covers walking the folder/publication tree, pulling full topic XML, safely editing DocBook-based content (preserving Paligo-managed `xinfo:*` and `xml:id` identifiers), validating edits with a bundled pre-push validator script, pushing content back, and handling checkout locks, release status, versioning, and translation impact.

**Install:**
```bash
npx skills add asebesta/claude-skills/paligo-api
```

**Triggers on:**
- Code involving the Paligo REST API (`{instance}.paligoapp.com/api/v2`)
- Walking Paligo folders, publications, or forks; bulk content export/import
- Round-trip editing of Paligo topic XML and pre-push validation
- Questions about Paligo checkout, release status, versioning, or translation behavior

### veo-video

Generate videos using Google's Veo 3.1 API. Includes prompting guide with shot types, camera movements, lighting, and style keywords, plus full API reference for all generation modes.

**Install:**
```bash
npx skills add asebesta/claude-skills/veo-video
```

**Triggers on:**
- Mentions of Veo, video generation, text-to-video, image-to-video, AI video
- Building applications with Google's Veo API
- Video prompt crafting and optimization

### virtuous-api

Reference for integrating with the Virtuous CRM REST API. Use when writing code that interacts with the Virtuous API for donor management, including Contacts, Individuals, Gifts, Projects, Campaigns, Events, Grants, Tasks, and Webhooks.

**Install:**
```bash
npx skills add asebesta/claude-skills/virtuous-api
```

**Triggers on:**
- Code involving Virtuous API integration
- Donor management features using Virtuous
- Questions about Virtuous endpoints, authentication, or data models

### trmnl-plugins

Build custom private plugins and dashboards for TRMNL e-ink displays, including the TRMNL X (10.3", 1872×1404, 16-level grayscale). Covers the data layer (webhook push, polling, plugin-merge), Liquid templating with TRMNL's custom filters, and the Design Framework 3.1 markup (views, mashups, items, tables, charts, typography, responsive/bit-depth utilities). Includes copy-paste layout scaffolds and chart/dashboard recipes.

**Install:**
```bash
npx skills add asebesta/claude-skills/trmnl-plugins
```

**Triggers on:**
- Creating or editing a TRMNL private plugin or dashboard
- Writing plugin markup/Liquid or sending data via webhook or polling
- Designing TRMNL layouts, embedding charts, or troubleshooting screen rendering
- Mentions of TRMNL, TRMNL X, usetrmnl, private plugins, or "merge variables"

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md          # Skill metadata and documentation
└── scripts/          # Implementation scripts
```

The `SKILL.md` file contains YAML frontmatter with the skill name and description, followed by usage documentation.

## Contributing

To add a new skill:

1. Create a directory with your skill name
2. Add a `SKILL.md` with frontmatter containing `name` and `description`
3. Add any scripts or resources in a `scripts/` directory
4. Document usage in the `SKILL.md`

## Disclaimer

These skills are provided as-is, without warranty of any kind. Use at your own risk. You are responsible for ensuring your use complies with applicable terms of service and laws.

## License

MIT
