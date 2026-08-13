"""The one check worth keeping: the Patient Portal cannot reach internal data.

Run: python test_boundary.py
"""

from fastapi.testclient import TestClient

from app import backend
from app.main import app

client = TestClient(app)


def test_public_client_refuses_internal_paths():
    for bad in ["/internal/repurposing", "/internal/trial-risk", "/public-ish/x", "/"]:
        try:
            backend.public.get(bad)
        except backend.BoundaryViolation:
            continue
        raise AssertionError(f"PublicClient accepted {bad!r}")


def test_internal_client_refuses_public_paths():
    try:
        backend.internal.get("/public/options")
    except backend.BoundaryViolation:
        return
    raise AssertionError("InternalClient accepted a /public/ path")


def test_portals_render():
    for path in ["/", "/patient", "/trial-design", "/rd"]:
        assert client.get(path).status_code == 200, path


def test_patient_results_render_with_citations():
    body = client.get("/patient", params={"condition": "ALS"}).text
    assert "Riluzole" in body
    assert "Sources" in body, "patient detail must surface its source"
    assert "not medical advice" in body


def test_trial_design_surfaces_why_stopped():
    body = client.get("/trial-design", params={"disease": "ALS"}).text
    assert "whyStopped" in body, "citations are the credibility feature, don't bury them"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all good")
