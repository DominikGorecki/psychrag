
```
psychRAG/                  # Root folder (usually a Git repo)
├── src/
│   └── psychRAG/         # Your actual package (importable name)
│       ├── __init__.py        # Makes it a package (can be empty or export __version__, API)
│       ├── core.py
│       ├── utils.py
│       ├── utils.py
│       ├── vectorization/       #scripts/library files for vectorizing chunks 
│       ├── chunking/       #scripts/library files for chunking markdown files formats to markdown
│           ├── __init__.py
│           └── ... 
│       ├── conversions/       #scripts/library files for converting file formats to markdown
│           ├── __init__.py
│           └── conv_epub2md.py
│       └── data/
│           ├── __init__.py
│           └── models.py
├── tests/                    # pytest discovers this automatically
│   ├── __init__.py          # optional
│   ├── unit/
│   │   ├── test_core.py
│   │   └── test_utils.py
│   └── integration/
├── scripts/                 # Optional: CLI entry points or useful dev scripts
│   └── generate_report.py
├── docs/                    # Optional but common (Sphinx or mkdocs)
├── .github/                  # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── pyproject.toml             # The only required build file in 2025 (replaces setup.py/setup.cfg)
├── README.md
├── LICENSE
└── ruff.toml                 # Most people use ruff in 2025 (linting + formatting)
```