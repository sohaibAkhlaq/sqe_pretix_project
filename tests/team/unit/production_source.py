"""Compile one named function from the pinned upstream source for isolated tests.

Only its collaborators are stubbed. The executed function body is taken directly
from the checked-in upstream file, so copied/retyped production logic is avoided.
"""
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_upstream_method(relative_path, class_name, method_name, namespace):
    source_path = PROJECT_ROOT / "upstream" / "pretix" / relative_path
    source = source_path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(source_path))
    owner = next(
        node for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    method = next(
        node for node in owner.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == method_name
    )
    isolated_module = ast.Module(body=[method], type_ignores=[])
    code = compile(isolated_module, filename=str(source_path), mode="exec")
    exec_namespace = dict(namespace)
    exec(code, exec_namespace)
    return exec_namespace[method_name]
