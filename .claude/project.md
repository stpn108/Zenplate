# Project Configuration

**PROJECT_NAME** is a ... (describe your project here).

**Project Path:** `/path/to/project`

## Quick Reference

```
VERSION                 # App version (MAJOR.MINOR), Source of Truth
DECISIONS.md            # Architecture Decision Log (ALWAYS maintain!)
README.md               # Operations, Deployment, Setup
app/                    # Main code
├── main.py            # Application entrypoint
├── database.py        # SQLAlchemy models + migrations
├── utils.py           # Timezone, datetime helpers
├── strings.py         # i18n (DE/EN)
├── tests/             # pytest tests
├── templates/         # Jinja2 templates (if needed)
└── Dockerfile         # Container definition
```
