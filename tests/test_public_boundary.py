"""Verifies the /public/* safety boundary explicitly, per the definition of
done: "The public API route cannot return anything derived from Convoke
data — verify this explicitly, don't just assume it."
"""

import ast
import inspect
import re

from app import schemas
from app.routers import public

FORBIDDEN_TERMS = {"target", "targets", "hgnc", "gene", "genes", "convoke"}


def _executable_source(module) -> str:
    """Module source with docstrings and comments stripped, so the check
    covers real code paths rather than prose about the boundary."""
    tree = ast.parse(inspect.getsource(module))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


def test_public_router_code_never_references_target_entities():
    # Word-level match so `generic_name` doesn't read as a `gene` reference.
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", _executable_source(public))}
    leaked = words & FORBIDDEN_TERMS
    assert not leaked, (
        f"app/routers/public.py must never reference {sorted(leaked)} in executable code — "
        "the public route must be structurally incapable of returning "
        "Convoke-derived (target/gene) data, not just filtered at query time."
    )


def test_public_trial_schema_excludes_sensitive_and_target_fields():
    public_fields = set(schemas.TrialPublicOut.model_fields)
    internal_only = {"why_stopped", "sponsor", "eligibility_text", "condition_ids", "intervention_ids"}
    assert public_fields.isdisjoint(internal_only)


def test_public_drug_label_schema_excludes_internal_ids():
    public_fields = set(schemas.DrugLabelPublicOut.model_fields)
    internal_only = {"drug_id", "condition_id", "mechanism_text", "approval_date"}
    assert public_fields.isdisjoint(internal_only)


def test_public_and_internal_routers_are_separate_modules():
    from app.routers import internal

    assert public.__file__ != internal.__file__
    assert public.router is not internal.router
