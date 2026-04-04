# GenBit

Synthetic biology construct designer for heterologous protein expression. Design genetic sequences with codon optimization, Kozak sequences, promoter selection, and construct assembly — all in one workspace.

## Features

- **Gene & Protein Lookup** — Search NCBI Gene, NCBI Protein, and UniProt for source sequences
- **Organism Selection** — Pick a target expression host from NCBI Taxonomy with organism-specific codon tables
- **Codon Optimization** — Frequency-based, harmonized, or balanced optimization via DNAchisel with GC content and restriction site constraints
- **Kozak Sequence Generation** — Species-specific translation initiation contexts (vertebrate, yeast, plant, Drosophila, E. coli)
- **Promoter Selection** — Browse synthetic promoters (CMV, EF1a, GAL1, CaMV 35S, etc.) and search the Eukaryotic Promoter Database
- **Construct Assembly** — Drag-and-drop builder for ordering promoter → Kozak → CDS → terminator with validation and linear map preview
- **Project Management** — Save, organize, and revisit construct designs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Zustand, React Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic |
| Bioinformatics | Biopython, DNAchisel, python-codon-tables |
| Database | PostgreSQL 16, Redis 7 |
| External APIs | NCBI Entrez, UniProt, Ensembl, CoCoPUTs, EPD, JASPAR |

## Project Structure

```
GenBit/
├── frontend/          Next.js app
│   └── src/
│       ├── app/           Pages (landing, designer, projects)
│       ├── components/    UI components by domain
│       ├── lib/api/       Typed API client layer
│       ├── hooks/         React Query hooks
│       ├── store/         Zustand state management
│       ├── types/         TypeScript interfaces
│       └── utils/         Sequence helpers, validation
│
├── backend/           FastAPI app
│   ├── app/
│   │   ├── routers/       API endpoints
│   │   ├── services/      Business logic (codon optimization, Kozak, assembly)
│   │   ├── clients/       External API wrappers (NCBI, UniProt, Ensembl)
│   │   ├── models/        SQLAlchemy ORM models
│   │   ├── schemas/       Pydantic request/response schemas
│   │   ├── utils/         Sequence tools, CAI calculation, FASTA parsing
│   │   └── db/            Database engine and session
│   ├── alembic/           Database migrations
│   └── tests/             Pytest test suite
│
└── docker-compose.yml PostgreSQL + Redis
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Hwzw/GenBit.git
cd GenBit

# 2. Start PostgreSQL and Redis
docker compose up -d

# 3. Set up the backend
cd backend
cp .env.example .env          # edit with your NCBI API key
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head           # run database migrations

# 4. Set up the frontend
cd ../frontend
cp .env.local.example .env.local
npm install

# 5. Start development servers (in separate terminals)
make dev-backend               # http://localhost:8000
make dev-frontend              # http://localhost:3000
```

### Environment Variables

Copy `.env.example` and fill in:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `NCBI_API_KEY` | [NCBI API key](https://www.ncbi.nlm.nih.gov/account/settings/) — raises rate limit from 3 to 10 req/sec |
| `NCBI_EMAIL` | Required by NCBI Entrez API |
| `SECRET_KEY` | Application secret |

### Running Tests

```bash
cd backend
python -m pytest
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check (DB + Redis) |
| `GET /api/genes/search?q=` | Search NCBI Gene |
| `GET /api/proteins/search?q=` | Search UniProt + NCBI Protein |
| `GET /api/organisms/search?q=` | Search NCBI Taxonomy |
| `GET /api/organisms/{tax_id}/codon-table` | Codon usage frequencies |
| `POST /api/optimization/optimize` | Run codon optimization |
| `POST /api/regulatory/kozak` | Generate Kozak sequence |
| `GET /api/regulatory/promoters/search` | Search promoters |
| `POST /api/constructs` | Create a construct |
| `POST /api/constructs/{id}/assemble` | Assemble full sequence |
| `GET/POST /api/projects` | Project CRUD |

Full interactive docs available at `http://localhost:8000/docs` when the backend is running.

## License

MIT
