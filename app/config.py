from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://teama:teama@localhost:5432/team_a"

    disease_area: str = "type 2 diabetes"
    clinicaltrials_condition_query: str = "type 2 diabetes mellitus"
    openfda_condition_query: str = "type 2 diabetes"

    raw_storage_backend: str = "local"
    raw_storage_dir: str = "./raw_data"
    s3_bucket: str = ""
    aws_region: str = "us-east-1"

    convoke_data_present: bool = False


settings = Settings()
