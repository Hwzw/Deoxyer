# Deoxyer

Synthetic biology construct designer for heterologous protein expression. Look up source sequences, optimize codons for a target host, assemble promoter → Kozak → CDS → terminator constructs, run *in silico* restriction digests, and export to GenBank — all from a text-based terminal UI in the browser.

## Features

- **Gene & Protein Lookup** — Search NCBI Gene, NCBI Protein, and UniProt; pull CDS, mRNA, or protein sequences into your workspace
- **Organism Selection** — Search NCBI Taxonomy and fetch organism-specific codon usage tables (CoCoPUTs + python-codon-tables fallback)
- **Codon Optimization** — DNAchisel-backed `frequency`, `harmonized`, and `balanced` strategies with GC-window and restriction-site avoidance constraints; CAI before/after and GC content reported
- **Kozak Generation** — Clade-aware translation initiation contexts (vertebrate, plant, fly, yeast, algae, slimemold, ciliate, malaria, toxoplasma, trypanosome, E. coli) resolved by tax ID or clade alias
- **Promoter & Terminator Browsing** — Curated synthetic promoters (CMV, EF1α, GAL1, CaMV 35S, …) plus EPD search, and transcription terminators for bacterial, yeast, mammalian, plant, and fungal hosts (B0015, SV40 poly-A, CYC1, NOS, …)
- **Project & Construct Management** — Organize work into projects and constructs; each construct holds a positional list of typed elements (promoter / kozak / cds / terminator / tag / utr / custom) with editable labels
- **Construct Assembly** — Concatenate elements in order, emit the full sequence plus per-element annotations and any validation warnings
- **Restriction Digest** — Pick one or more enzymes; returns cut positions, resulting fragment sizes, and which annotated elements each fragment spans
- **GenBank Export** — Download an assembled construct as a `.gb` file (ready to drop into Benchling, SnapGene, etc.) with feature annotations and assembly-warning comments preserved
- **Session Isolation** — Every browser tab gets an anonymous session ID stored in `localStorage`; all projects, constructs, and jobs are scoped to that session
- **Agent-Friendly Output** — A `--json` flag on any command prints structured JSON instead of the formatted view, for scripting and LLM integration

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Single-file terminal UI (HTML / vanilla JS, zero dependencies) |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Bioinformatics | Biopython, DNAchisel, python-codon-tables |
| Database | PostgreSQL 16, Redis 7 (caching) |
| External APIs | NCBI Entrez, UniProt, Ensembl, CoCoPUTs, EPD, JASPAR |

## Project Structure

```
deoxyer/
├── frontend/
│   └── public/
│       └── terminal.html          Single-file terminal UI (served at /)
│
├── backend/
│   ├── app/
│   │   ├── main.py                FastAPI app (serves terminal + API)
│   │   ├── config.py              Pydantic settings
│   │   ├── dependencies.py        DB + session ID dependencies
│   │   ├── routers/               health, genes, proteins, organisms,
│   │   │                          optimization, regulatory, projects, constructs
│   │   ├── services/              gene, protein, organism, codon_optimization,
│   │   │                          kozak, promoter, terminator, project,
│   │   │                          construct, construct_assembly,
│   │   │                          restriction_digest, genbank_export, cache
│   │   ├── clients/               NCBI, UniProt, Ensembl, CoCoPUTs, EPD, JASPAR
│   │   ├── models/                SQLAlchemy ORM (Project, Construct,
│   │   │                          ConstructElement, OptimizationJob, …)
│   │   ├── schemas/               Pydantic request/response schemas
│   │   ├── utils/                 Sequence tools, CAI, FASTA parsing
│   │   └── db/                    Async engine and session
│   ├── alembic/                   Database migrations
│   └── tests/                     Pytest suite
│
└── docker-compose.yml             PostgreSQL + Redis (optional)
```

## Getting Started

### Prerequisites

- Python 3.12+
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
git clone https://github.com/deoxyer/deoxyer.git
cd deoxyer

# 2. Create the PostgreSQL user and database
createuser deoxyer -P         # set a password when prompted
createdb -O deoxyer deoxyer
psql -U $(whoami) -d deoxyer -c "GRANT ALL ON SCHEMA public TO deoxyer;"

# 3. Set up the backend
cd backend
cp .env.example .env          # edit with your credentials (see below)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head          # run database migrations

# 4. Start the server
make run                      # http://localhost:8000
```

Open **http://localhost:8000** in your browser. Type `help` to see all commands.

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (match your `createuser` password) |
| `REDIS_URL` | Redis connection string (default `redis://localhost:6379/0` is fine) |
| `NCBI_API_KEY` | [NCBI API key](https://www.ncbi.nlm.nih.gov/account/settings/) — raises Entrez rate limit from 3 → 10 req/sec |
| `NCBI_EMAIL` | Required by NCBI Entrez |
| `SECRET_KEY` | Application secret (any random string) |

### Running Tests

```bash
cd backend
python -m pytest
```

## Terminal Commands

### Lookup

| Command | Description |
|---------|-------------|
| `health` | Check API + database + Redis status |
| `gene search <query> [--organism=X]` | Search NCBI Gene |
| `gene get <id>` | Gene details |
| `gene sequence <id> [--type=cds\|mrna] [--name=X] [--seq]` | Fetch sequence, save to workspace |
| `protein search <query> [--organism=X]` | Search UniProt + NCBI Protein |
| `protein get <accession>` | Protein details |
| `protein sequence <accession> [--name=X] [--seq]` | Fetch sequence, save to workspace |
| `organism search <query>` | Search NCBI Taxonomy |
| `organism get <tax_id>` | Organism details |
| `organism codons <tax_id>` | Codon usage table |

### Design

| Command | Description |
|---------|-------------|
| `optimize <name\|accession> <tax_id>` | Codon-optimize a protein for a host |
| — flags | `--strategy=frequency\|harmonized\|balanced`, `--gc-min`, `--gc-max`, `--avoid=EcoRI,BamHI`, `--allow-repeats`, `--name`, `--seq` |
| `kozak <tax_id\|clade> [--start=ATG] [--name=X]` | Generate Kozak context |
| `kozak list` | List clade aliases |
| `promoter search <organism> [--gene=X]` | Search promoter catalog + EPD |
| `promoter get <id> [--name=X]` | Fetch promoter, save to workspace |
| `terminator search <organism>` | Search terminator catalog |
| `terminator get <id> [--name=X]` | Fetch terminator, save to workspace |

### Projects & Constructs

| Command | Description |
|---------|-------------|
| `project list` | List projects |
| `project create <name> [--desc=X]` | Create and activate a project |
| `project use <id>` | Set active project |
| `project get [id]` | Project details (defaults to active) |
| `project update [id] [--name=X] [--desc=X]` | Edit project fields |
| `project rename [id] <new_name>` | Rename project |
| `project delete [id]` | Delete project |
| `construct list [--project=<id>]` | List constructs |
| `construct create <name> [--project=<id>] [--organism=<tax_id>]` | Create construct |
| `construct use <id>` | Set active construct |
| `construct add [id] <workspace_name> [--as=TYPE] [--position=N]` | Add element from workspace (TYPE: promoter / kozak / cds / terminator / tag / utr / custom) |
| `construct get [id]` | Show construct elements |
| `construct rename [id] <new_name>` | Rename construct |
| `construct element rename <pos> <new_label>` | Relabel an element in the active construct |
| `construct delete [id]` | Delete construct |
| `construct assemble [id] [--seq]` | Assemble full sequence + annotations |
| `construct digest [id] <enz1> [enz2 …]` | *In silico* restriction digest (e.g. `EcoRI BamHI`) |
| `construct export [id] [--format=genbank]` | Download `.gb` (Benchling-ready) |

### Workspace & Navigation

| Command | Description |
|---------|-------------|
| `ws` | List workspace objects |
| `ws add <name> <sequence> [--type=TYPE]` | Add a raw sequence |
| `show <name>` | Show sequence (add `--info` for metadata) |
| `rm <name>` | Remove from workspace |
| `rename <old> <new>` | Rename workspace object |
| `rename construct\|project <new_name>` | Rename the active construct / project |
| `cd <name>` | Enter project (from root) or construct (from project) |
| `cd ..` / `cd /` | Go up one level / return to root |
| `status` | Show active project + construct |
| `clear` / `history` | Clear terminal / show command history |
| `set base-url <url>` | Change backend URL |
| `help [command]` | Show help (supports topic help, e.g. `help construct`) |

### Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Print raw JSON instead of formatted output (for scripting and agent use) |
| `--seq` | Print the sequence inline on fetch / assemble / optimize commands |

## Session Isolation

Each browser tab generates a unique anonymous session ID stored in `localStorage`. All projects, constructs, and optimization jobs are scoped to that session — you only see your own data. Clearing browser site data starts a fresh session. Every API call that touches user data requires an `X-Session-ID` header.

## API Docs

Interactive Swagger docs at **http://localhost:8000/docs** when the backend is running.

## License

MIT
