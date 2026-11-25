"""AST parity and loader utilities verifying scoped production functions match pinned upstream pretix."""
import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _extract_fn_ast(path: Path, class_name, method_name: str):
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    body = (
        next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == class_name).body
        if class_name
        else module.body
    )
    return next(
        n for n in body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method_name
    )


def assert_ast_matches_upstream(upstream_rel: str, upstream_cls, scoped_cls, method_name: str):
    """Raise AssertionError if the scoped production function AST differs from pinned upstream."""
    upstream_path = PROJECT_ROOT / "upstream" / "pretix" / upstream_rel
    scoped_path = PROJECT_ROOT / "upstream" / "pretix" / "base" / "scoped_business_logic.py"
    up_fn = _extract_fn_ast(upstream_path, upstream_cls, method_name)
    sc_fn = _extract_fn_ast(scoped_path, scoped_cls, method_name)
    assert ast.dump(sc_fn) == ast.dump(up_fn), (
        f"AST drift detected for {method_name} between {scoped_path} and {upstream_path}"
    )


def load_upstream_method(relative_path, class_name, method_name, namespace):
    """Compile a named function directly from the pinned upstream source for isolated execution."""
    source_path = PROJECT_ROOT / "upstream" / "pretix" / relative_path
    method = _extract_fn_ast(source_path, class_name, method_name)
    isolated_module = ast.Module(body=[method], type_ignores=[])
    code = compile(isolated_module, filename=str(source_path), mode="exec")
    exec_namespace = dict(namespace)
    exec(code, exec_namespace)
    return exec_namespace[method_name]
