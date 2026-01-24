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
| [ios-app-store-competitor-research](./ios-app-store-competitor-research) | Extract app metadata and screenshots from Apple App Store listings for competitive analysis |

### ios-app-store-competitor-research

Research competitor apps on the Apple App Store. Extracts comprehensive metadata including title, description, ratings, pricing, and downloads all screenshots at high resolution.

**Install:**
```bash
npx skills add asebesta/claude-skills/ios-app-store-competitor-research
```

**Triggers on:**
- App Store URLs (apps.apple.com)
- Requests like "research this app", "analyze competitor", "get app store info"

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
