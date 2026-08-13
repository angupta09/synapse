from fastapi import FastAPI

from app.routers import internal, normalize, public

app = FastAPI(title="Team A — Data & Backend Infrastructure")

app.include_router(internal.router)
app.include_router(normalize.router)
app.include_router(public.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
