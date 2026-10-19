"""attest-witness/1: the constrained witness language of the contract audit (review findings R5-03 and R6-1, 19 Oct 2026).

A contract-audit witness can establish INFEASIBLE only when it is written in this language. The language is a POSITIVE grammar:
every statement, expression, import, call and attribute a witness may use is named below, and anything not named is outside the
language. A witness outside the language is still executed and recorded, but it can only hold the run for a person (NEEDS
HUMAN); it never ends a run INFEASIBLE. The revision-6 rule was a list of forbidden spellings and was bypassed by an import
alias (`from builtins import type as make_type`); this module replaces it.

What the language enforces MECHANICALLY, in the pipeline before the verdict and again in `attest check` afterwards:

- statements: imports, assignments to names or to items, expression statements, if/elif/else, for, while, try/except/else/
  finally, assert, raise, pass, break, continue. No function, class or lambda definitions, no with, del, global, match or walrus.
- imports: `sys` (exit, stdout, stderr, maxsize), `itertools`, `math`, `string` and `json` (each with a fixed list of names),
  and the frozen repository's own modules. A name imported from the repository must RESOLVE, statically and through the
  repository's own source, to a function or class the repository defines (re-exports followed through explicit and star
  imports); a re-export of anything else, a conditional or repeated binding, or a missing file is unresolved. An allowed
  standard-library module that the repository shadows is refused.
- calls: an allowed built-in by its own name, an allowed standard-library function or a resolved repository function or class
  by its imported name or module attribute, or a method of a built-in value (str, bytes, numbers, list, tuple, dict, set, range).
  A call through a value held in a variable, through a subscript, through the result of another call or through any other
  computed expression is outside the language, and so is every name that is neither bound by the witness nor an allowed
  built-in (`type`, `object`, `getattr`, `vars`, `globals`, `exec`, `eval`, `compile`, `__import__`, `__builtins__`, ...).
- attributes: no name that starts with an underscore; on a module only the allowed names; on a value only the public method and
  attribute names of the built-in value types (and `args` of an exception).

So a witness's inputs are literals, containers and comprehensions of literals, and values computed from them by allowed
built-ins, allowed standard-library functions and the repository's own code; it cannot build a subclass of a built-in type, a
dynamic type, or an object with overridden special methods except by calling code the repository itself defines.

What the language does NOT establish: that the witness's inputs and comparisons demonstrate that the named criteria cannot all
hold. That link is the auditor model's reasoning; Attest records the program, its execution and its output, and a grounded
INFEASIBLE verdict says "demonstrated by an executed witness", never "proven impossible". The analysis is static: it assumes that
the repository binds names only through statements it can read (no `globals()` or `setattr` tricks in the repository's own code)
and that no installed dependency on the guest path shadows a resolved repository module.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Mapping

WITNESS_LANGUAGE = "attest-witness/1"
REPOSITORY_COPY_DIR = "contract_audit/repository"  # copies of the frozen repository files an origin resolution read
MAX_RESOLUTION_DEPTH = 8
MAX_PROBLEMS = 20

ALLOWED_MODULES: dict[str, frozenset[str]] = {
    "sys": frozenset({"exit", "stdout", "stderr", "maxsize"}),
    "itertools": frozenset({"accumulate", "batched", "chain", "combinations", "combinations_with_replacement", "compress", "count", "cycle",
                            "dropwhile", "filterfalse", "groupby", "islice", "pairwise", "permutations", "product", "repeat", "starmap",
                            "takewhile", "zip_longest"}),
    "math": frozenset({"ceil", "comb", "e", "exp", "fabs", "factorial", "floor", "fsum", "gcd", "inf", "isclose", "isfinite", "isinf", "isnan",
                       "isqrt", "lcm", "log", "log10", "log2", "nan", "perm", "pi", "pow", "prod", "sqrt", "tau", "trunc"}),
    "string": frozenset({"ascii_letters", "ascii_lowercase", "ascii_uppercase", "digits", "hexdigits", "octdigits", "printable", "punctuation",
                         "whitespace"}),
    "json": frozenset({"dumps", "loads"}),
}
# `sys` is a built-in module of the interpreter and cannot be shadowed by a file; the others can, so a repository file of the same
# name makes the import refer to repository code and the import is refused
UNSHADOWABLE_MODULES = frozenset({"sys"})

BUILTIN_CALLABLES = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "chr", "complex", "dict", "divmod", "enumerate", "filter", "float",
    "format", "frozenset", "hex", "int", "isinstance", "iter", "len", "list", "map", "max", "min", "next", "oct", "ord", "pow", "print",
    "range", "repr", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip"})
BUILTIN_EXCEPTIONS = frozenset({
    "ArithmeticError", "AssertionError", "AttributeError", "EOFError", "Exception", "IndexError", "KeyError", "LookupError",
    "NotImplementedError", "OSError", "OverflowError", "RecursionError", "RuntimeError", "StopIteration", "TypeError", "UnicodeDecodeError",
    "UnicodeEncodeError", "UnicodeError", "ValueError", "ZeroDivisionError"})
MODULE_GLOBALS = frozenset({"__name__"})
# the public method and attribute names of str, bytes, bytearray, int, float, complex, bool, list, tuple, dict, set, frozenset and
# range in Python 3.12 (frozen here so that the pipeline and every checker agree), plus `args` of an exception
VALUE_ATTRIBUTES = frozenset({
    "add", "append", "args", "as_integer_ratio", "bit_count", "bit_length", "capitalize", "casefold", "center", "clear", "conjugate", "copy",
    "count", "decode", "denominator", "difference", "difference_update", "discard", "encode", "endswith", "expandtabs", "extend", "find",
    "format", "format_map", "from_bytes", "fromhex", "fromkeys", "get", "hex", "imag", "index", "insert", "intersection",
    "intersection_update", "is_integer", "isalnum", "isalpha", "isascii", "isdecimal", "isdigit", "isdisjoint", "isidentifier", "islower",
    "isnumeric", "isprintable", "isspace", "issubset", "issuperset", "istitle", "isupper", "items", "join", "keys", "ljust", "lower",
    "lstrip", "maketrans", "numerator", "partition", "pop", "popitem", "real", "remove", "removeprefix", "removesuffix", "replace",
    "reverse", "rfind", "rindex", "rjust", "rpartition", "rsplit", "rstrip", "setdefault", "sort", "split", "splitlines", "start",
    "startswith", "step", "stop", "strip", "swapcase", "symmetric_difference", "symmetric_difference_update", "title", "to_bytes",
    "translate", "union", "update", "upper", "values", "zfill"})

# Arguments that a callee of the language calls back: (positional indexes, keyword names). A callable passed there must itself have
# a resolved origin, exactly like a called name, so that no call happens through a computed value (review R6-1, "indirect calls").
CALLBACK_ARGUMENTS: dict[str, tuple[tuple[int, ...], tuple[str, ...]]] = {
    "builtins.map": ((0,), ()), "builtins.filter": ((0,), ()), "builtins.sorted": ((), ("key",)), "builtins.min": ((), ("key",)),
    "builtins.max": ((), ("key",)), "itertools.starmap": ((0,), ()), "itertools.filterfalse": ((0,), ()), "itertools.dropwhile": ((0,), ()),
    "itertools.takewhile": ((0,), ()), "itertools.accumulate": ((1,), ("func",)), "itertools.groupby": ((1,), ("key",)),
    "json.loads": ((), ("cls", "object_hook", "object_pairs_hook", "parse_float", "parse_int", "parse_constant")),
    "json.dumps": ((), ("cls", "default")), "method.sort": ((), ("key",)),
}

_ALLOWED_MODULE_LIST = ", ".join(sorted(ALLOWED_MODULES))


def language_summary() -> str:
    """The language as the contract-audit prompt states it (kept next to the rules so the two cannot drift apart)."""
    return (f"WITNESS LANGUAGE ({WITNESS_LANGUAGE}), enforced mechanically before a witness can establish anything. The witness is a flat "
            "module of statements: imports, assignments to names (or to items of a list or dict), expression statements, if/elif/else, for, "
            "while, try/except/else/finally, assert, raise, pass, break and continue. It may import only sys (for sys.exit, sys.stdout, "
            "sys.stderr), itertools, math, string and json, and the repository's own modules; every name it imports from the repository "
            "must be a function or class the repository itself defines. It may call only: the built-ins "
            f"{', '.join(sorted(BUILTIN_CALLABLES))} and the built-in exception classes; the allowed standard-library functions; the "
            "repository's functions and classes by their imported names (or as attributes of an imported repository module); and the "
            "ordinary methods of str, bytes, number, list, tuple, dict and set values (for example ''.join(...), s.strip(), "
            "str.partition(s, '=')). It may not define any function, class or lambda, call a value held in a variable, subscript or "
            "call result, use type, object, getattr, vars, globals, exec, eval, compile or __import__, or access any attribute whose name "
            "starts with an underscore (to report an exception, print repr(exc)). Its inputs are literals and values computed from them by "
            "these calls. A witness outside this language is executed and recorded, but it can only hold the run for a human; it never "
            "establishes that the task is infeasible")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and not PurePosixPath(path).is_absolute() and ".." not in parts and "" not in parts


class Repository:
    """The frozen repository as origin resolution sees it: every file path, the module roots of the guest's PYTHONPATH and a reader
    for the content of the files the resolution needs. `read_files` records (path -> sha256) every file a resolution read, so the
    same resolution can be repeated offline from copies of exactly those files."""

    def __init__(self, paths: Iterable[str], roots: Iterable[str], read: Callable[[str], bytes | None]):
        self.paths = {p for p in paths if _safe_relative(p)}
        ordered = [str(r).strip("/") for r in roots if str(r).strip("/")]
        self.roots = list(dict.fromkeys(ordered + [""]))  # python_paths first, the repository root last, as on the guest
        self._read = read
        self.read_files: dict[str, str] = {}
        self.unavailable: set[str] = set()
        self._trees: dict[str, ast.Module | None] = {}
        self._modules: dict[str, tuple[str, bool]] = {}  # file -> (dotted module, is package)

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, bytes], python_paths: Iterable[str] = ()) -> "Repository":
        return cls(snapshot.keys(), python_paths, lambda path: snapshot.get(path))

    @classmethod
    def from_bundle(cls, run_dir: Path, task_record: dict) -> "Repository":
        """Resolution over the copies kept in the bundle: a copy is used only when its digest equals the frozen task's digest of that
        path, so a resolution can never read a file the frozen repository did not contain."""
        frozen = dict((task_record or {}).get("repo_files_sha256") or {})
        base = Path(run_dir) / REPOSITORY_COPY_DIR

        def read(path: str) -> bytes | None:
            if path not in frozen or not _safe_relative(path):
                return None
            copy = base / path
            if not copy.is_file() or copy.is_symlink():
                return None
            data = copy.read_bytes()
            return data if _sha256(data) == frozen[path] else None

        return cls(frozen.keys(), (task_record or {}).get("python_paths") or [], read)

    # ---------------------------------------------------------------------------------------------------------- modules
    def module_file(self, dotted: str) -> str | None:
        if not dotted or any(not part.isidentifier() for part in dotted.split(".")):
            return None
        rel = dotted.replace(".", "/")
        for root in self.roots:
            base = f"{root}/{rel}" if root else rel
            for candidate, package in ((f"{base}/__init__.py", True), (f"{base}.py", False)):
                if candidate in self.paths:
                    self._modules[candidate] = (dotted, package)
                    return candidate
        return None

    def has_module(self, dotted: str) -> bool:
        return self.module_file(dotted) is not None

    def tree(self, path: str) -> ast.Module | None:
        if path in self._trees:
            return self._trees[path]
        data = self._read(path)
        if data is None:
            self.unavailable.add(path)
            self._trees[path] = None
            return None
        self.read_files[path] = _sha256(data)
        try:
            tree = ast.parse(data.decode("utf-8-sig"))
        except (SyntaxError, UnicodeDecodeError, ValueError):
            tree = None
        self._trees[path] = tree
        return tree

    def _package_of(self, path: str) -> str:
        dotted, package = self._modules.get(path, ("", False))
        return dotted if package else dotted.rpartition(".")[0]

    def _absolute(self, path: str, level: int, module: str | None) -> str | None:
        """The absolute module a (possibly relative) `from ... import` in `path` names."""
        if level == 0:
            return module
        base = self._package_of(path)
        for _ in range(level - 1):
            if not base:
                return None
            base = base.rpartition(".")[0]
        if not base:
            return None
        return f"{base}.{module}" if module else base

    # ---------------------------------------------------------------------------------------------------------- resolution
    def resolve(self, module: str, name: str, depth: int = 0, seen: frozenset = frozenset()) -> tuple[dict | None, str]:
        """(resolution, reason). A resolution names what `module.name` is at run time, statically: a function or class the repository
        defines (`kind` function or class, with file and line), or a repository module (`kind` module). None, with the reason, when
        the name is anything else or cannot be determined from the repository's own source."""
        key = (module, name)
        if depth > MAX_RESOLUTION_DEPTH or key in seen:
            return None, f"the resolution of {module}.{name} is cyclic or deeper than {MAX_RESOLUTION_DEPTH} steps"
        seen = seen | {key}
        if name.startswith("_"):
            return None, f"{name} is a private name"
        path = self.module_file(module)
        if path is None:
            return None, f"{module} is not a module of the frozen repository"
        tree = self.tree(path)
        if tree is None:
            why = "is not available" if path in self.unavailable else "does not parse"
            return None, f"{path} {why}"
        bindings, nested, stars = _bindings(tree, name)
        submodule = self.module_file(f"{module}.{name}")
        exporting = []
        for star in stars:
            source = self._absolute(path, star.level, star.module)
            if source is None or not self.has_module(source):
                return None, f"{path} line {star.lineno} star-imports {star.module or '.'}, which is not a repository module"
            exported = self._exports(source, name, depth + 1, seen)
            if exported is None:
                return None, f"whether {source} exports {name} cannot be determined"
            if exported:
                exporting.append(source)
        if nested:
            return None, f"{name} is bound conditionally in {path} (line {nested[0].lineno})"
        if len(bindings) + len(exporting) > 1:
            return None, f"{name} is bound more than once in {path}"
        if not bindings and not exporting:
            if submodule is not None:
                return {"kind": "module", "module": f"{module}.{name}", "file": submodule}, ""
            return None, f"{path} does not define {name}"
        if exporting:
            found, reason = self.resolve(exporting[0], name, depth + 1, seen)
            return (dict(found, via=[path] + found.get("via", [])) if found else None), reason
        node = bindings[0]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {"kind": "function", "module": module, "name": name, "file": path, "line": node.lineno}, ""
        if isinstance(node, ast.ClassDef):
            return {"kind": "class", "module": module, "name": name, "file": path, "line": node.lineno}, ""
        if isinstance(node, ast.ImportFrom):
            alias = next(a for a in node.names if (a.asname or a.name) == name)
            source = self._absolute(path, node.level, node.module)
            if source is None or not self.has_module(source):
                return None, (f"{name} is re-exported in {path} (line {node.lineno}) from {node.module or '.'}, which is not part of the "
                              "frozen repository")
            found, reason = self.resolve(source, alias.name, depth + 1, seen)
            return (dict(found, via=[path] + found.get("via", [])) if found else None), reason
        if isinstance(node, ast.Import):
            alias = next(a for a in node.names if (a.asname or a.name.split(".")[0]) == name)
            target = alias.name if alias.asname else alias.name.split(".")[0]
            if self.has_module(target):
                return {"kind": "module", "module": target, "file": self.module_file(target)}, ""
            return None, f"{name} is bound in {path} (line {node.lineno}) to the module {alias.name}, which is not part of the frozen repository"
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Name):
            found, reason = self.resolve(module, node.value.id, depth + 1, seen)
            return (dict(found, via=[path] + found.get("via", [])) if found else None), reason
        return None, f"{name} is bound in {path} (line {getattr(node, 'lineno', '?')}) by a statement other than a definition or a repository import"

    def _exports(self, module: str, name: str, depth: int, seen: frozenset) -> bool | None:
        """Whether `from module import *` binds `name` (None when it cannot be decided statically)."""
        if depth > MAX_RESOLUTION_DEPTH:
            return None
        path = self.module_file(module)
        tree = self.tree(path) if path else None
        if tree is None:
            return None
        all_bindings, all_nested, _ = _bindings(tree, "__all__")
        if all_bindings or all_nested:
            if all_nested or len(all_bindings) != 1 or not isinstance(all_bindings[0], ast.Assign):
                return None
            value = all_bindings[0].value
            if not isinstance(value, (ast.List, ast.Tuple)) or not all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in value.elts):
                return None
            return name in {e.value for e in value.elts}
        if name.startswith("_"):
            return False
        bindings, nested, stars = _bindings(tree, name)
        if bindings or nested:
            return True
        for star in stars:
            source = self._absolute(path, star.level, star.module)
            if source is None or not self.has_module(source):
                return None
            exported = self._exports(source, name, depth + 1, seen)
            if exported is None or exported:
                return exported
        return False


def _bindings(tree: ast.Module, name: str) -> tuple[list, list, list]:
    """Statements of a module (outside function, class and lambda bodies) that bind `name`: (top-level bindings, bindings nested in
    a compound statement, star imports)."""
    top: list = []
    nested: list = []
    stars: list = []

    def binds(node) -> bool:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return node.name == name
        if isinstance(node, ast.Import):
            return any((a.asname or a.name.split(".")[0]) == name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            return any(a.name != "*" and (a.asname or a.name) == name for a in node.names)
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [item.optional_vars for item in node.items if item.optional_vars is not None]
        elif isinstance(node, ast.Delete):
            targets = node.targets
        elif isinstance(node, ast.Global):
            return name in node.names
        for target in targets:
            for sub in ast.walk(target):
                if isinstance(sub, ast.Name) and sub.id == name:
                    return True
        if isinstance(node, ast.Try) or (hasattr(ast, "TryStar") and isinstance(node, getattr(ast, "TryStar"))):
            return any(h.name == name for h in node.handlers)
        return False

    def visit(statements, depth: int) -> None:
        for node in statements:
            if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
                (stars if depth == 0 else nested).append(node)
            elif binds(node):
                (top if depth == 0 else nested).append(node)
            # walrus targets anywhere in the statement's expressions (outside nested scopes)
            for sub in _expressions_outside_scopes(node):
                if isinstance(sub, ast.NamedExpr) and isinstance(sub.target, ast.Name) and sub.target.id == name:
                    nested.append(node)
                    break
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for field_name in ("body", "orelse", "finalbody", "handlers"):
                children = getattr(node, field_name, None)
                if not children:
                    continue
                if field_name == "handlers":
                    for handler in children:
                        visit(handler.body, depth + 1)
                else:
                    visit(children, depth + 1)
            if hasattr(ast, "Match") and isinstance(node, ast.Match):
                for case in node.cases:
                    for sub in ast.walk(case.pattern):
                        if getattr(sub, "name", None) == name:
                            nested.append(node)
                    visit(case.body, depth + 1)

    visit(tree.body, 0)
    return top, nested, stars


def _expressions_outside_scopes(node):
    """Expression nodes of one statement, not descending into nested statements, functions, classes, lambdas or comprehensions."""
    stack = [child for child in ast.iter_child_nodes(node) if isinstance(child, ast.expr)]
    while stack:
        current = stack.pop()
        yield current
        if isinstance(current, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            continue
        stack.extend(child for child in ast.iter_child_nodes(current) if isinstance(child, ast.expr))


# ------------------------------------------------------------------------------------------------------------------ analysis
class _Origin:
    __slots__ = ("kind", "module", "name", "line", "resolution")

    def __init__(self, kind: str, module: str | None = None, name: str | None = None, line: int | None = None, resolution: dict | None = None):
        self.kind = kind  # stdlib-module, stdlib, repo-module, repo, value, invalid
        self.module = module
        self.name = name
        self.line = line
        self.resolution = resolution

    def key(self) -> tuple:
        return (self.kind, self.module, self.name)


class _Analyzer:
    def __init__(self, repository: Repository | None):
        self.repository = repository
        self.problems: list[str] = []
        self.origins: list[dict] = []
        self.bindings: dict[str, list[_Origin]] = {}

    # ----------------------------------------------------------------------------------------------------------- helpers
    def problem(self, text: str) -> None:
        if text not in self.problems:
            self.problems.append(text)

    def bind(self, name: str, origin: _Origin) -> None:
        self.bindings.setdefault(name, []).append(origin)

    def _repo_module(self, dotted: str) -> bool:
        return self.repository is not None and self.repository.has_module(dotted)

    def _shadowed(self, module: str) -> bool:
        return module not in UNSHADOWABLE_MODULES and self._repo_module(module)

    def _resolve(self, module: str, name: str) -> tuple[dict | None, str]:
        if self.repository is None:
            return None, "no repository is available to resolve it"
        return self.repository.resolve(module, name)

    # ----------------------------------------------------------------------------------------------------------- pass 1
    def collect(self, tree: ast.Module) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._import(alias, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                self._import_from(node)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                self.bind(node.id, _Origin("value", line=node.lineno))
            elif isinstance(node, ast.ExceptHandler) and node.name:
                self.bind(node.name, _Origin("value", line=node.lineno))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.bind(node.name, _Origin("value", line=node.lineno))

    def _import(self, alias: ast.alias, line: int) -> None:
        full = alias.name
        top = full.split(".")[0]
        bound = alias.asname or top
        target = full if alias.asname else top
        if full in ALLOWED_MODULES:
            if self._shadowed(full):
                self.problem(f"imports {full} at line {line}, but the repository's own module {full} shadows the standard-library module")
                self.bind(bound, _Origin("invalid", line=line))
                return
            self.bind(bound, _Origin("stdlib-module", module=full, line=line))
            self.origins.append({"line": line, "import": full, "as": bound, "origin": "standard library"})
            return
        if top in ALLOWED_MODULES or not self._repo_module(full) or not self._repo_module(target):
            self.problem(f"imports the module {full} at line {line}, which is neither an allowed standard-library module "
                         f"({_ALLOWED_MODULE_LIST}) nor a module of the frozen repository")
            self.bind(bound, _Origin("invalid", line=line))
            return
        self.bind(bound, _Origin("repo-module", module=target, line=line))
        self.origins.append({"line": line, "import": full, "as": bound, "origin": "repository module", "file": self.repository.module_file(target)})

    def _import_from(self, node: ast.ImportFrom) -> None:
        line = node.lineno
        if node.level:
            self.problem(f"uses a relative import at line {line}; a witness imports modules by their absolute names")
            for alias in node.names:
                self.bind(alias.asname or alias.name, _Origin("invalid", line=line))
            return
        module = node.module or ""
        for alias in node.names:
            bound = alias.asname or alias.name
            if alias.name == "*":
                self.problem(f"star-imports {module} at line {line}; a witness names every imported name")
                continue
            if module in ALLOWED_MODULES:
                if self._shadowed(module):
                    self.problem(f"imports from {module} at line {line}, but the repository's own module {module} shadows the standard-library module")
                    self.bind(bound, _Origin("invalid", line=line))
                elif alias.name not in ALLOWED_MODULES[module]:
                    self.problem(f"imports {alias.name} from {module} at line {line}, which {WITNESS_LANGUAGE} does not allow "
                                 f"(allowed: {', '.join(sorted(ALLOWED_MODULES[module]))})")
                    self.bind(bound, _Origin("invalid", line=line))
                else:
                    self.bind(bound, _Origin("stdlib", module=module, name=alias.name, line=line))
                    self.origins.append({"line": line, "import": f"{module}.{alias.name}", "as": bound, "origin": "standard library"})
                continue
            if not self._repo_module(module):
                self.problem(f"imports {alias.name} from the module {module} at line {line}, which is neither an allowed standard-library "
                             f"module ({_ALLOWED_MODULE_LIST}) nor a module of the frozen repository")
                self.bind(bound, _Origin("invalid", line=line))
                continue
            found, reason = self._resolve(module, alias.name)
            if found is None:
                self.problem(f"imports {alias.name} from the repository module {module} at line {line}, which does not resolve to a "
                             f"function or class the repository defines ({reason})")
                self.bind(bound, _Origin("invalid", line=line))
            elif found["kind"] == "module":
                self.bind(bound, _Origin("repo-module", module=found["module"], line=line, resolution=found))
                self.origins.append({"line": line, "import": f"{module}.{alias.name}", "as": bound, "origin": "repository module", "file": found["file"]})
            else:
                self.bind(bound, _Origin("repo", module=module, name=alias.name, line=line, resolution=found))
                self.origins.append({"line": line, "import": f"{module}.{alias.name}", "as": bound, "origin": f"repository {found['kind']}",
                                     "file": found["file"], "defined_at_line": found["line"], "via": found.get("via", [])})

    # ----------------------------------------------------------------------------------------------------------- pass 2
    def statements(self, body) -> None:
        for node in body:
            self.statement(node)

    def statement(self, node) -> None:
        kind = type(node)
        line = getattr(node, "lineno", "?")
        if kind in (ast.Import, ast.ImportFrom, ast.Pass, ast.Break, ast.Continue):
            return
        if kind is ast.Expr:
            self.expr(node.value)
        elif kind is ast.Assign:
            for target in node.targets:
                self.target(target)
            self.expr(node.value)
        elif kind is ast.AugAssign:
            self.target(node.target, augmented=True)
            self.expr(node.value)
        elif kind is ast.AnnAssign:
            if not isinstance(node.target, ast.Name):
                self.problem(f"annotates a target other than a name at line {line}")
            self.expr(node.annotation)
            if node.value is not None:
                self.expr(node.value)
        elif kind in (ast.If, ast.While):
            self.expr(node.test)
            self.statements(node.body)
            self.statements(node.orelse)
        elif kind is ast.For:
            self.target(node.target)
            self.expr(node.iter)
            self.statements(node.body)
            self.statements(node.orelse)
        elif kind is ast.Try:
            self.statements(node.body)
            for handler in node.handlers:
                if handler.type is not None:
                    self.expr(handler.type)
                self.statements(handler.body)
            self.statements(node.orelse)
            self.statements(node.finalbody)
        elif kind is ast.Assert:
            self.expr(node.test)
            if node.msg is not None:
                self.expr(node.msg)
        elif kind is ast.Raise:
            if node.exc is not None:
                self.expr(node.exc)
            if node.cause is not None:
                self.expr(node.cause)
        elif kind in (ast.FunctionDef, ast.AsyncFunctionDef):
            self.problem(f"defines a function ({node.name}) at line {line}")
        elif kind is ast.ClassDef:
            self.problem(f"defines a class ({node.name}) at line {line}")
        else:
            self.problem(f"uses a {kind.__name__} statement at line {line}, which {WITNESS_LANGUAGE} does not allow")

    def target(self, node, augmented: bool = False) -> None:
        if isinstance(node, ast.Name):
            return
        if isinstance(node, (ast.Tuple, ast.List)) and not augmented:
            for element in node.elts:
                self.target(element.value if isinstance(element, ast.Starred) else element)
            return
        if isinstance(node, ast.Subscript):
            self.expr(node.value)
            self.expr(node.slice)
            return
        self.problem(f"assigns to a {type(node).__name__} at line {getattr(node, 'lineno', '?')}; a witness assigns only to names and items")

    def expr(self, node) -> None:
        kind = type(node)
        line = getattr(node, "lineno", "?")
        if kind is ast.Constant:
            return
        if kind is ast.Name:
            self.name_load(node)
        elif kind is ast.Attribute:
            self.attribute(node)
        elif kind is ast.Call:
            self.call(node)
        elif kind is ast.BinOp:
            self.expr(node.left)
            self.expr(node.right)
        elif kind is ast.UnaryOp:
            self.expr(node.operand)
        elif kind is ast.BoolOp:
            for value in node.values:
                self.expr(value)
        elif kind is ast.Compare:
            self.expr(node.left)
            for value in node.comparators:
                self.expr(value)
        elif kind is ast.IfExp:
            self.expr(node.test)
            self.expr(node.body)
            self.expr(node.orelse)
        elif kind in (ast.List, ast.Tuple, ast.Set):
            for element in node.elts:
                self.expr(element)
        elif kind is ast.Starred:
            self.expr(node.value)
        elif kind is ast.Dict:
            for key, value in zip(node.keys, node.values):
                if key is not None:
                    self.expr(key)
                self.expr(value)
        elif kind is ast.Subscript:
            self.expr(node.value)
            self.expr(node.slice)
        elif kind is ast.Slice:
            for part in (node.lower, node.upper, node.step):
                if part is not None:
                    self.expr(part)
        elif kind is ast.JoinedStr:
            for value in node.values:
                self.expr(value)
        elif kind is ast.FormattedValue:
            self.expr(node.value)
            if node.format_spec is not None:
                self.expr(node.format_spec)
        elif kind in (ast.ListComp, ast.SetComp, ast.GeneratorExp):
            self.comprehension(node.generators)
            self.expr(node.elt)
        elif kind is ast.DictComp:
            self.comprehension(node.generators)
            self.expr(node.key)
            self.expr(node.value)
        elif kind is ast.Lambda:
            self.problem(f"defines a lambda at line {line}")
        else:
            self.problem(f"uses a {kind.__name__} expression at line {line}, which {WITNESS_LANGUAGE} does not allow")

    def comprehension(self, generators) -> None:
        for generator in generators:
            if generator.is_async:
                self.problem(f"uses an asynchronous comprehension at line {getattr(generator.iter, 'lineno', '?')}")
            self.target(generator.target)
            self.expr(generator.iter)
            for condition in generator.ifs:
                self.expr(condition)

    def name_load(self, node: ast.Name) -> None:
        if node.id in self.bindings or node.id in BUILTIN_CALLABLES or node.id in BUILTIN_EXCEPTIONS or node.id in MODULE_GLOBALS:
            return
        self.problem(f"uses the name {node.id} at line {node.lineno}, which is neither bound by the witness nor an allowed built-in")

    def module_of(self, node) -> tuple[str, str] | None:
        """('stdlib-module', name) or ('repo-module', dotted) when the expression denotes an imported module, else None."""
        if isinstance(node, ast.Name):
            binds = self.bindings.get(node.id) or []
            kinds = {(b.kind, b.module) for b in binds}
            if len(kinds) == 1:
                kind, module = next(iter(kinds))
                if kind in ("stdlib-module", "repo-module"):
                    return kind, module
            return None
        if isinstance(node, ast.Attribute) and not node.attr.startswith("_"):
            inner = self.module_of(node.value)
            if inner and inner[0] == "repo-module":
                found, _ = self._resolve(inner[1], node.attr)
                if found and found["kind"] == "module":
                    return "repo-module", found["module"]
        return None

    def attribute(self, node: ast.Attribute) -> bool:
        """Validates an attribute access; True when it denotes something a witness may call."""
        line = node.lineno
        if node.attr.startswith("_"):
            self.problem(f"accesses the attribute {node.attr} at line {line}; attribute names that start with an underscore are outside "
                         f"{WITNESS_LANGUAGE}")
            if self.module_of(node.value) is None:
                self.expr(node.value)
            return False
        module = self.module_of(node.value)
        if module and module[0] == "stdlib-module":
            if node.attr not in ALLOWED_MODULES[module[1]]:
                self.problem(f"uses {module[1]}.{node.attr} at line {line}, which {WITNESS_LANGUAGE} does not allow "
                             f"(allowed: {', '.join(sorted(ALLOWED_MODULES[module[1]]))})")
                return False
            return True
        if module and module[0] == "repo-module":
            found, reason = self._resolve(module[1], node.attr)
            if found is None:
                self.problem(f"uses {module[1]}.{node.attr} at line {line}, which does not resolve to a function or class the repository "
                             f"defines ({reason})")
                return False
            self.origins.append({"line": line, "attribute": f"{module[1]}.{node.attr}", "origin": f"repository {found['kind']}",
                                 "file": found["file"], "defined_at_line": found.get("line")})
            return True
        self.expr(node.value)
        if node.attr not in VALUE_ATTRIBUTES:
            self.problem(f"accesses the attribute {node.attr} of a value at line {line}; only the public methods and attributes of built-in "
                         "str, bytes, number, list, tuple, dict, set and range values (and args of an exception) are allowed")
            return False
        return True

    def callable_name(self, node: ast.Name, line: int, what: str) -> str | None:
        """Validates a name used as a callable; returns the callee's identity ('builtins.map', 'itertools.groupby', 'repo') or None."""
        binds = self.bindings.get(node.id) or []
        if not binds:
            if node.id in BUILTIN_CALLABLES or node.id in BUILTIN_EXCEPTIONS:
                return f"builtins.{node.id}"
            self.problem(f"{what} {node.id} at line {line}, which is not an allowed built-in")
            return None
        if any(b.kind == "invalid" for b in binds):
            return None  # the import was reported already
        if len({b.key() for b in binds}) != 1 or binds[0].kind not in ("stdlib", "repo"):
            where = ", ".join(sorted({f"{'an assignment or loop' if b.kind == 'value' else 'an import of a module'} at line {b.line}" for b in binds}))
            self.problem(f"{what} {node.id} at line {line}, which is bound by {where}; a witness may call only allowed built-ins, allowed "
                         "standard-library functions and the repository's own functions and classes, by their imported names")
            return None
        return f"{binds[0].module}.{binds[0].name}" if binds[0].kind == "stdlib" else "repo"

    def callback(self, node, line: int, callee: str) -> None:
        """An argument that `callee` calls back must be a callable with a resolved origin (or None, as in filter(None, ...))."""
        if isinstance(node, ast.Constant) and node.value is None:
            return
        if isinstance(node, ast.Name):
            self.callable_name(node, line, f"passes to {callee} the callable")
            return
        if isinstance(node, ast.Attribute):
            self.attribute(node)
            return
        self.problem(f"passes a computed callable ({type(node).__name__}) to {callee} at line {line}; a callable argument must be a name or "
                     "attribute whose origin is resolved")

    def call(self, node: ast.Call) -> None:
        func = node.func
        line = node.lineno
        callee = None
        if isinstance(func, ast.Name):
            callee = self.callable_name(func, line, "calls")
        elif isinstance(func, ast.Attribute):
            if self.attribute(func):
                module = self.module_of(func.value) if not func.attr.startswith("_") else None
                if module and module[0] == "stdlib-module":
                    callee = f"{module[1]}.{func.attr}"
                elif module is None and func.attr == "sort":
                    callee = "method.sort"
        else:
            self.problem(f"calls a computed value ({type(func).__name__}) at line {line}; only names and attributes whose origin is "
                         "resolved can be called")
        positions, keywords = CALLBACK_ARGUMENTS.get(callee or "", ((), ()))
        if callee == "builtins.iter" and len(node.args) == 2:
            positions = (0,)  # iter(callable, sentinel) calls its first argument
        for index in positions:
            if index < len(node.args) and not isinstance(node.args[index], ast.Starred):
                self.callback(node.args[index], line, callee)
        for keyword in node.keywords:
            if keyword.arg in keywords:
                self.callback(keyword.value, line, callee)
        if positions and any(isinstance(a, ast.Starred) for a in node.args[:max(positions) + 1]):
            self.problem(f"passes starred arguments to {callee} at line {line}, so its callable argument cannot be checked")
        if keywords and any(k.arg is None for k in node.keywords):
            self.problem(f"passes **keyword arguments to {callee} at line {line}, so its callable arguments cannot be checked")
        for argument in node.args:
            self.expr(argument)
        for keyword in node.keywords:
            self.expr(keyword.value)


def analyze_witness(source: str, repository: Repository | None) -> dict:
    """The language analysis of one witness program: whether it conforms to WITNESS_LANGUAGE, every problem found (empty when it
    conforms), the resolved origin of every import and repository attribute, and the repository files the resolution read with
    their digests. `repository` None means that no repository can be consulted: every repository import is then unresolved."""
    analyzer = _Analyzer(repository)
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        analyzer.problem(f"does not parse: {error.msg} at line {error.lineno}")
        tree = None
    if tree is not None:
        analyzer.collect(tree)
        analyzer.statements(tree.body)
    files = dict(sorted(repository.read_files.items())) if repository is not None else {}
    return {"version": WITNESS_LANGUAGE, "conforms": not analyzer.problems, "problems": analyzer.problems[:MAX_PROBLEMS],
            "origins": analyzer.origins, "repository_files": files}
