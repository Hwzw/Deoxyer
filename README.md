# GenBit

Synthetic biology construct designer for heterologous protein expression. Design genetic sequences with codon optimization, Kozak sequences, promoter selection, and construct assembly — all from a text-based terminal interface.

## Features

- **Gene & Protein Lookup** — Search NCBI Gene, NCBI Protein, and UniProt for source sequences
- **Organism Selection** — Pick a target expression host from NCBI Taxonomy with organism-specific codon tables
- **Codon Optimization** — Frequency-based, harmonized, or balanced optimization via DNAchisel with GC content and restriction site constraints
- **Kozak Sequence Generation** — Species-specific translation initiation contexts (vertebrate, yeast, plant, Drosophila, E. coli)
- **Promoter Selection** — Browse synthetic promoters (CMV, EF1a, GAL1, CaMV 35S, etc.) and search the Eukaryotic Promoter Database
- **Construct Assembly** — Build constructs from promoter → Kozak → CDS → terminator with validation and assembly
- **Project Management** — Save, organize, and revisit construct designs
- **Session Isolation** — Each browser session gets its own workspace; projects and data are scoped per user
- **Agent-Friendly Output** — `--json` flag on any command for machine-readable JSON output

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Single-file terminal UI (HTML/JS, zero dependencies) |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic |
| Bioinformatics | Biopython, DNAchisel, python-codon-tables |
| Database | PostgreSQL 16, Redis 7 |
| External APIs | NCBI Entrez, UniProt, Ensembl, CoCoPUTs, EPD, JASPAR |

## Project Structure

```
GenBit/
├── frontend/
│   └── public/
│       └── terminal.html    Single-file terminal UI (served at /)
│
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI app (serves terminal + API)
│   │   ├── routers/          API endpoints
│   │   ├── services/         Business logic
│   │   ├── clients/          External API wrappers (NCBI, UniProt, etc.)
│   │   ├── models/           SQLAlchemy ORM models
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── utils/            Sequence tools, CAI calculation, FASTA parsing
│   │   └── db/               Database engine and session
│   ├── alembic/              Database migrations
│   └── tests/                Pytest test suite
│
└── docker-compose.yml        PostgreSQL + Redis (optional)
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+

Install with Homebrew (macOS):

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Hwzw/GenBit.git
cd GenBit

# 2. Create PostgreSQL user and database
createuser genbit -P          # set a password when prompted
createdb -O genbit genbit
psql -U $(whoami) -d genbit -c "GRANT ALL ON SCHEMA public TO genbit;"

# 3. Set up the backend
cd backend
cp .env.example .env          # edit with your credentials (see below)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head          # run database migrations

# 4. Start the server
make run                       # http://localhost:8000
```

Open **http://localhost:8000** in your browser. Type `help` to see all commands.

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (update password to match your `createuser` step) |
| `REDIS_URL` | Redis connection string (default `redis://localhost:6379/0` is fine) |
| `NCBI_API_KEY` | [NCBI API key](https://www.ncbi.nlm.nih.gov/account/settings/) — raises rate limit from 3 to 10 req/sec |
| `NCBI_EMAIL` | Required by NCBI Entrez API |
| `SECRET_KEY` | Application secret (any random string) |

### Running Tests

```bash
cd backend
python -m pytest
```

## Terminal Commands

| Command | Description |
|---------|-------------|
| `health` | Check API + database + Redis status |
| `gene search <query> [--organism=X]` | Search NCBI Gene |
| `gene get <id>` | Get gene details |
| `gene sequence <id> [--type=cds]` | Get gene sequence |
| `protein search <query> [--organism=X]` | Search UniProt + NCBI Protein |
| `protein get <accession>` | Get protein details |
| `protein sequence <accession>` | Get protein sequence |
| `organism search <query>` | Search NCBI Taxonomy |
| `organism get <tax_id>` | Get organism details |
| `organism codons <tax_id>` | Get codon usage table |
| `optimize <seq> --organism=<tax_id>` | Run codon optimization |
| `kozak <tax_id>` | Generate Kozak sequence |
| `promoter search <organism>` | Search promoters |
| `project list` | List your projects |
| `project create <name>` | Create a new project |
| `construct create <name> --project=<id>` | Create a construct |
| `construct add <id> <workspace_name>` | Add element to construct |
| `construct get <id>` | View construct elements |
| `construct assemble <id> [--seq]` | Assemble full sequence |
| `ws` | List workspace objects |
| `show <name>` | View a saved sequence |
| `help` | Show all commands with full flag options |

### Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Output raw JSON instead of formatted text (useful for scripting and agent integration) |
| `--seq` | Print the sequence inline (on fetch/assemble commands) |

## Session Isolation

Each browser tab generates a unique anonymous session ID (stored in `localStorage`). All projects, constructs, and optimization jobs are scoped to your session — you only see your own data. Clearing browser site data starts a fresh session.

## API Docs

Interactive Swagger docs at **http://localhost:8000/docs** when the backend is running. All endpoints that create or access user data require an `X-Session-ID` header.

## License

MIT
