from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://genbit:genbit@localhost:5432/genbit"
    REDIS_URL: str = "redis://localhost:6379/0"

    # NCBI
    NCBI_API_KEY: str = ""
    NCBI_EMAIL: str = ""
    NCBI_CONCURRENT_WITH_KEY: int = 10
    NCBI_CONCURRENT_WITHOUT_KEY: int = 3

    # Application
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"

    # External API base URLs
    EPD_BASE_URL: str = "https://epd.expasy.org/api"
    ENSEMBL_BASE_URL: str = "https://rest.ensembl.org"
    UNIPROT_BASE_URL: str = "https://rest.uniprot.org"
    JASPAR_BASE_URL: str = "https://jaspar.elixir.no/api/v1"
    COCOPUTS_BASE_URL: str = "https://dnahive.fda.gov/dna.cgi"

    # HTTP timeouts (seconds)
    HTTP_TIMEOUT: float = 30.0
    COCOPUTS_TIMEOUT: float = 60.0

    # Cache TTLs (seconds)
    CACHE_TTL_GENE: int = 86400  # 24 hours
    CACHE_TTL_PROTEIN: int = 86400
    CACHE_TTL_ORGANISM: int = 604800  # 7 days
    CACHE_TTL_CODON_TABLE: int = 604800

    # Codon optimization
    GC_CONTENT_WINDOW: int = 50
    REPEAT_AVOIDANCE_PATTERN: str = "9x1mer"
    FALLBACK_CODON_TABLE: str = "e_coli_316407"

    # Scoring thresholds
    PROMOTER_STRONG_THRESHOLD: int = 80
    PROMOTER_MODERATE_THRESHOLD: int = 40
    TERMINATOR_HIGH_THRESHOLD: int = 90
    TERMINATOR_MODERATE_THRESHOLD: int = 80

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
