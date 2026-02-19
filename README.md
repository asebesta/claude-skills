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
| [bloomerang-api](./bloomerang-api) | Bloomerang CRM API integration reference for donor management features |
| [ios-app-store-competitor-research](./ios-app-store-competitor-research) | Extract app metadata and screenshots from Apple App Store listings for competitive analysis |
| [veo-video](./veo-video) | Generate videos using Google's Veo 3.1 API via the @google/genai SDK |
| [virtuous-api](./virtuous-api) | Virtuous CRM API integration reference for donor management features |

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

### ios-app-store-competitor-research

Research competitor apps on the Apple App Store. Extracts comprehensive metadata including title, description, ratings, pricing, and downloads all screenshots at high resolution.

**Install:**
```bash
npx skills add asebesta/claude-skills/ios-app-store-competitor-research
```

**Triggers on:**
- App Store URLs (apps.apple.com)
- Requests like "research this app", "analyze competitor", "get app store info"

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
