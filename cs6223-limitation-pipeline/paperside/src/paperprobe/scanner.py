"""Read-only, deterministic discovery of syntactic testing opportunities.

Python uses the standard-library AST. Other supported languages use a deliberately
limited lexical fallback. Neither path imports or executes the inspected source.
Discovered conditions are observations, not verified contracts or reachable tests.
"""

from __future__ import annotations

import ast
import hashlib
import math
import os
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

_EXTENSIONS = {
    ".py": "python", ".pyi": "python", ".c": "c", ".h": "c_cpp",
    ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".hxx": "cpp", ".cu": "cuda", ".cuh": "cuda",
}
_EXCLUDED = {".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"}
_OPS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=", ast.Is: "is", ast.IsNot: "is not"}
_INVERSE = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "==", "!=": "!=", "is": "is", "is not": "is not"}
_STATE_NAME = re.compile(r"(?:^|[._])(?:state|status|phase)(?:$|[_ .])", re.I)
_IDENT = r"[A-Za-z_]\w*(?:(?:::|->|\.)[A-Za-z_]\w*)*"
_NUMBER = r"[+-]?(?:0[xX][0-9a-fA-F]+(?:[uUlL]*)|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?[fFuUlL]*)"


def _constant(node: ast.AST) -> tuple[bool, Any]:
    if isinstance(node, ast.Constant) and (node.value is None or type(node.value) in (bool, int, float, str)):
        return True, node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        ok, value = _constant(node.operand)
        if ok and type(value) in (int, float):
            return True, -value if isinstance(node.op, ast.USub) else value
    return False, None


def _literal_type(value: Any) -> str:
    return {bool: "boolean", int: "integer", float: "float", str: "string", type(None): "null"}.get(type(value), "unknown")


def _direct_binding(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return True
    return isinstance(node, ast.Attribute) and _direct_binding(node.value)


def _condition(path: str, language: str, expression: str, variable: str, operator: str,
               threshold: Any, quote: str, start: int, end: int, symbol: str,
               *, value_type: str | None = None, **extra: Any) -> dict[str, Any]:
    value_type = value_type or _literal_type(threshold)
    kind = "state" if _STATE_NAME.search(variable) else (
        "boundary" if type(threshold) in (int, float) else "configuration"
    )
    fingerprint = f"{path}:{start}:{extra.get('column_start', 0)}:{expression}"
    return {
        "condition_id": "cond-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:16],
        "path": path, "line_start": start, "line_end": end, "symbol": symbol,
        "language": language, "expression": expression, "kind": kind,
        "variable": variable, "operator": operator, "threshold": threshold,
        "value_type": value_type,
        "evidence": {"path": path, "line_start": start, "line_end": end,
                     "quote": quote, "sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest()},
        "backend": "deterministic_heuristic", "scope_status": "unknown",
        "verification_status": "static_observation_not_executed", **extra,
    }


class _PythonScanner(ast.NodeVisitor):
    def __init__(self, source: str, path: str, tree: ast.AST):
        self.source, self.path = source, path
        self.conditions: list[dict[str, Any]] = []
        self.symbols: list[str] = []
        self.type_scopes: list[dict[str, str]] = [{}]
        self._collect_types(tree, self.type_scopes[0], descend_functions=False)

    def _collect_types(self, tree: ast.AST, destination: dict[str, str], *, descend_functions: bool) -> None:
        nodes = list(ast.iter_child_nodes(tree))
        while nodes:
            node = nodes.pop(0)
            if not descend_functions and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, ast.AnnAssign):
                annotation = ast.unparse(node.annotation)
                kind = {"bool": "boolean", "int": "integer", "float": "float", "str": "string"}.get(annotation)
                if kind:
                    destination[ast.unparse(node.target)] = kind
            elif isinstance(node, ast.Assign):
                ok, value = _constant(node.value)
                if ok and value is not None:
                    for target in node.targets:
                        if _direct_binding(target):
                            variable, inferred = ast.unparse(target), _literal_type(value)
                            if variable in destination and destination[variable] != inferred:
                                destination[variable] = "unknown"
                            else:
                                destination[variable] = inferred
            nodes.extend(ast.iter_child_nodes(node))

    def _type(self, variable: str) -> str | None:
        for scope in reversed(self.type_scopes):
            if variable in scope:
                return scope[variable]
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(node.name)
        self.generic_visit(node)
        self.symbols.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.symbols.append(node.name)
        types: dict[str, str] = {}
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            if argument.annotation:
                kind = {"bool": "boolean", "int": "integer", "float": "float", "str": "string"}.get(ast.unparse(argument.annotation))
                if kind:
                    types[argument.arg] = kind
        self._collect_types(node, types, descend_functions=False)
        self.type_scopes.append(types)
        self.generic_visit(node)
        self.type_scopes.pop()
        self.symbols.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _record_test(self, test: ast.AST, control: str) -> None:
        quote = ast.get_source_segment(self.source, test) or ast.unparse(test)
        expression = ast.unparse(test)

        def record(variable_node: ast.AST, operator: str, threshold: Any, atomic: str,
                   prerequisites: list[str], context: str) -> None:
            if type(threshold) is float and not math.isfinite(threshold):
                return
            variable = ast.unparse(variable_node)
            declared = self._type(variable)
            kind = declared or _literal_type(threshold)
            self.conditions.append(_condition(
                self.path, "python", atomic, variable, operator, threshold, quote,
                test.lineno, test.end_lineno or test.lineno, ".".join(self.symbols) or "<module>",
                value_type=kind, test_expression=expression, control_flow=control,
                activation_preconditions=prerequisites, boolean_context=context,
                column_start=test.col_offset, column_end=test.end_col_offset,
                input_binding="unconfirmed" if _direct_binding(variable_node) else "derived_expression",
                value_type_source="annotation_or_literal_assignment" if declared else "comparison_literal_probe",
                numeric_format="float64" if kind == "float" else None,
                parser="python_ast",
            ))

        def atoms(node: ast.AST, prerequisites: list[str], context: str) -> None:
            if isinstance(node, ast.BoolOp):
                conjunction = isinstance(node.op, ast.And)
                for index, child in enumerate(node.values):
                    others = [ast.unparse(other) for i, other in enumerate(node.values) if i != index]
                    extra = others if conjunction else [f"Other disjunct must be false: {other}" for other in others]
                    atoms(child, prerequisites + extra, "and" if conjunction else "or")
            elif isinstance(node, ast.Compare):
                operands = [node.left, *node.comparators]
                segments = [f"{ast.unparse(left)} {_OPS.get(type(op), '?')} {ast.unparse(right)}"
                            for left, op, right in zip(operands, node.ops, operands[1:])]
                for index, (left, op, right) in enumerate(zip(operands, node.ops, operands[1:])):
                    operator = _OPS.get(type(op))
                    if operator is None:
                        continue
                    left_literal, left_value = _constant(left)
                    right_literal, right_value = _constant(right)
                    extra = [item for i, item in enumerate(segments) if i != index]
                    if right_literal and not left_literal:
                        record(left, operator, right_value, segments[index], prerequisites + extra, context)
                    elif left_literal and not right_literal:
                        record(right, _INVERSE[operator], left_value,
                               f"{ast.unparse(right)} {_INVERSE[operator]} {ast.unparse(left)}",
                               prerequisites + extra, context)
            elif isinstance(node, (ast.Name, ast.Attribute)):
                record(node, "truthy", True, ast.unparse(node), prerequisites, context)
                if self._type(ast.unparse(node)) is None:
                    self.conditions[-1]["value_type"] = "unknown"
                    self.conditions[-1]["value_type_source"] = "truthiness_not_boolean_type"
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not) and isinstance(node.operand, (ast.Name, ast.Attribute)):
                record(node.operand, "falsy", False, ast.unparse(node), prerequisites, context)
                if self._type(ast.unparse(node.operand)) is None:
                    self.conditions[-1]["value_type"] = "unknown"
                    self.conditions[-1]["value_type_source"] = "truthiness_not_boolean_type"
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                # Preserve original comparison orientation; the complete test
                # and context explicitly record that its Boolean value is negated.
                atoms(node.operand, prerequisites, "negated")

        atoms(test, [], "single")

    def visit_If(self, node: ast.If) -> None:
        self._record_test(node.test, "if")
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._record_test(node.test, "while")
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._record_test(node.test, "conditional_expression")
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._record_test(node.test, "assert")
        self.generic_visit(node)


def _mask_noncode(source: str) -> str:
    """Mask comments and literals while retaining offsets and newlines."""
    result = list(source)
    index = 0
    while index < len(source):
        start = index
        if source.startswith("//", index):
            stop = source.find("\n", index)
            index = len(source) if stop < 0 else stop
        elif source.startswith("/*", index):
            stop = source.find("*/", index + 2)
            index = len(source) if stop < 0 else stop + 2
        elif source.startswith('R"', index):
            opening = source.find("(", index + 2, index + 20)
            if opening < 0:
                index += 1
                continue
            delimiter = source[index + 2:opening]
            stop = source.find(")" + delimiter + '"', opening + 1)
            index = len(source) if stop < 0 else stop + len(delimiter) + 2
        elif source[index] in ('"', "'"):
            delimiter = source[index]
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                elif source[index] == delimiter:
                    index += 1
                    break
                else:
                    index += 1
        else:
            index += 1
            continue
        for offset in range(start, min(index, len(source))):
            if source[offset] != "\n":
                result[offset] = " "
    return "".join(result)


def _cpp_number(token: str) -> Any:
    if re.fullmatch(r"[+-]?0[xX][0-9a-fA-F]+[uUlL]*", token):
        return int(re.sub(r"[uUlL]+$", "", token), 0)
    numeric = re.sub(r"[fFuUlL]+$", "", token)
    if "." in numeric or "e" in numeric.lower() or token.lower().endswith("f"):
        value = float(numeric)
        if token.lower().endswith("f"):
            try:
                return struct.unpack("!f", struct.pack("!f", value))[0]
            except (OverflowError, struct.error):
                return math.copysign(math.inf, value)
        return value
    unsigned = numeric.lstrip("+-")
    # A leading zero selects octal for a C/C++ integral literal.
    return int(numeric, 8 if len(unsigned) > 1 and unsigned.startswith("0") else 10)


def _scan_cpp(source: str, path: str, language: str) -> list[dict[str, Any]]:
    masked = _mask_noncode(source)
    types = {match.group(2): match.group(1) for match in re.finditer(
        r"\b(bool|float|double|int|long|short|size_t|uint\d+_t|int\d+_t)\s+(\w+)\b", masked)}
    conditions: list[dict[str, Any]] = []
    atom_pattern = re.compile(rf"(?<![\w.])(?P<var>{_IDENT})\s*(?P<op><=|>=|==|!=|<|>)")
    for header in re.finditer(r"\b(if|while)\s*(?:constexpr\s*)?\(", masked):
        start = header.end()
        depth, stop = 1, start
        while stop < len(masked) and depth:
            depth += (masked[stop] == "(") - (masked[stop] == ")")
            stop += 1
        if depth:
            continue
        end = stop - 1
        context, quote = masked[start:end], source[start:end]
        line_start, line_end = source.count("\n", 0, start) + 1, source.count("\n", 0, end) + 1
        declarations = list(re.finditer(rf"\b({_IDENT})\s*\([^;{{}}]*\)\s*(?:const\s*)?{{", masked[:header.start()]))
        symbol = declarations[-1].group(1) if declarations else "<unknown>"
        if symbol in {"if", "while", "for", "switch"}:
            symbol = "<unknown>"

        def append(variable: str, operator: str, threshold: Any, *, declared: str | None = None) -> None:
            kind = {"bool": "boolean", "float": "float", "double": "float"}.get(declared, "integer" if declared else None)
            inferred = kind or _literal_type(threshold)
            expression = f"{variable} {operator} {threshold!r}"
            conditions.append(_condition(
                path, language, expression, variable, operator, threshold, quote, line_start, line_end, symbol,
                value_type=inferred, parser="limited_cpp_regex", test_expression=quote,
                control_flow=header.group(1), input_binding="unconfirmed",
                value_type_source="lexical_declaration" if declared else "comparison_literal_probe",
                numeric_format="float32" if declared == "float" else "float64" if inferred == "float" else None,
                activation_preconditions=[] if "&&" not in context and "||" not in context else [
                    "Establish other clauses and isolate this comparison in the complete condition: " + quote],
                limitations=["Lexical fallback does not resolve macros, templates, types or control-flow reachability."],
                column_start=start - (source.rfind("\n", 0, start) + 1),
            ))

        for atom in atom_pattern.finditer(context):
            prefix = context[:atom.start()].rstrip()
            if prefix and not (prefix.endswith("(") or prefix.endswith("&&") or prefix.endswith("||")):
                continue  # Reject e.g. the x fragment of n / x < 3.
            rhs_offset = start + atom.end()
            while rhs_offset < end and source[rhs_offset].isspace():
                rhs_offset += 1
            rhs = source[rhs_offset:end]
            token = re.match(rf"(?:{_NUMBER}|true\b|false\b)", rhs)
            value: Any = None
            if token:
                literal = token.group()
                tail = masked[rhs_offset + token.end():end].lstrip()
                if tail and not tail.startswith((")", "&&", "||")):
                    continue  # Reject partial matches such as n < 32 * stride.
                try:
                    value = literal == "true" if literal in ("true", "false") else _cpp_number(literal)
                except ValueError:
                    continue  # Malformed numeric source is not an inferred threshold.
            elif rhs.startswith('"'):
                string = re.match(r'"(?:[^"\\]|\\.)*"', rhs)
                if not string:
                    continue
                tail = masked[rhs_offset + string.end():end].lstrip()
                if tail and not tail.startswith((")", "&&", "||")):
                    continue
                try:
                    value = ast.literal_eval(string.group())
                except (ValueError, SyntaxError):
                    continue
            else:
                continue
            if type(value) is float and not math.isfinite(value):
                continue
            variable = atom.group("var")
            append(variable, atom.group("op"), value, declared=types.get(re.split(r"::|->|\.", variable)[-1]))

        truth = re.fullmatch(rf"\s*(?P<not>!)?\s*(?P<var>{_IDENT})\s*", context)
        if truth:
            variable = truth.group("var")
            declared = types.get(re.split(r"::|->|\.", variable)[-1])
            append(variable, "falsy" if truth.group("not") else "truthy", not bool(truth.group("not")), declared=declared)
            if declared != "bool":
                conditions[-1]["value_type"] = "unknown"
                conditions[-1]["value_type_source"] = "truthiness_not_boolean_type"
    return conditions


def scan_repository(repo_path: Path, max_files: int = 500, max_file_bytes: int = 256000,
                    include_paths: list[str | Path] | None = None) -> dict[str, Any]:
    """Scan bounded local source files, never following symlinks out of a repo."""
    if type(max_files) is not int or max_files < 0 or type(max_file_bytes) is not int or max_file_bytes <= 0:
        raise ValueError("max_files must be nonnegative and max_file_bytes must be positive integers")
    root = Path(repo_path).expanduser().resolve()
    output: dict[str, Any] = {"repo_path": str(root), "commit": None, "files_scanned": 0,
                              "conditions": [], "errors": [], "backend": "deterministic_heuristic",
                              "scan_limits": {"max_files": max_files, "max_file_bytes": max_file_bytes},
                              "files_skipped": 0, "truncated": False}
    if not root.is_dir():
        output["errors"].append({"path": str(root), "code": "not_directory", "message": "Repository path is not a directory."})
        return output
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=5, check=False)
        if commit.returncode == 0:
            output["commit"] = commit.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    selected: list[Path] | None = None
    if include_paths is not None:
        selected = []
        for path in include_paths:
            requested = Path(path)
            requested = requested if requested.is_absolute() else root / requested
            resolved = requested.resolve()
            if not resolved.is_relative_to(root):
                output["errors"].append({"path": str(path), "code": "outside_repository", "message": "Included path must stay within the repository."})
            else:
                selected.append(resolved)
    def source_paths():
        for directory, directories, filenames in os.walk(root, followlinks=False):
            directories[:] = sorted(name for name in directories
                                    if name not in _EXCLUDED and not name.startswith(".git")
                                    and not (Path(directory) / name).is_symlink())
            for filename in sorted(filenames):
                yield Path(directory) / filename

    for path in source_paths():
        relative = path.relative_to(root)
        if any(part in _EXCLUDED or part.startswith(".git") for part in relative.parts):
            continue
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in _EXTENSIONS:
            continue
        if not path.resolve().is_relative_to(root):
            continue
        if selected is not None and not any(path == item or path.is_relative_to(item) for item in selected):
            continue
        if output["files_scanned"] >= max_files:
            output["truncated"] = True
            break
        name = relative.as_posix()
        try:
            if path.stat().st_size > max_file_bytes:
                output["files_skipped"] += 1
                output["errors"].append({"path": name, "code": "file_too_large", "message": "File exceeds the configured byte limit."})
                continue
            with path.open("rb") as handle:
                content = handle.read(max_file_bytes + 1)
            if len(content) > max_file_bytes:
                output["files_skipped"] += 1
                output["errors"].append({"path": name, "code": "file_too_large", "message": "File grew beyond the configured byte limit."})
                continue
            if b"\0" in content:
                raise UnicodeError("NUL-containing file is not treated as source text")
            source = content.decode("utf-8")
            output["files_scanned"] += 1
            language = _EXTENSIONS[path.suffix.lower()]
            if language == "python":
                tree = ast.parse(source, filename=name)
                scanner = _PythonScanner(source, name, tree)
                scanner.visit(tree)
                conditions = scanner.conditions
                if re.search(r"\b(?:import triton|from triton\b|@triton\.jit)", source):
                    for condition in conditions:
                        condition["language"] = "triton_python"
            else:
                conditions = _scan_cpp(source, name, language)
            output["conditions"].extend(conditions)
        except (OSError, UnicodeError, SyntaxError, RecursionError) as error:
            output["errors"].append({"path": name, "code": type(error).__name__, "message": str(error)[:500]})
    return output
