"""Breaker pass, mutation part: small semantic mutants of the candidate's changed lines.

Mutants are generated from the AST (comparison swaps, boolean swaps, `not` removal, +/-, constant shifts,
boolean flips, `raise` to `pass`) only at lines the candidate changed, then each mutant runs the sealed suite
in its own disposable branch. A mutant is killed when the sealed suite fails on it.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
from dataclasses import dataclass

COMPARE_SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq,
                ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}
BINOP_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
              ast.FloorDiv: ast.Mult, ast.Mod: ast.Sub}


@dataclass
class Mutant:
    id: str
    path: str
    lineno: int
    operator: str
    description: str
    source: str


def changed_line_numbers(base_text: str | None, new_text: str) -> set[int]:
    """Line numbers (1-based, in the new text) that were inserted or replaced relative to the base."""
    old = (base_text or "").splitlines()
    new = new_text.splitlines()
    changed: set[int] = set()
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag in ("insert", "replace"):
            changed.update(range(j1 + 1, j2 + 1))
    return changed


class _Sites(ast.NodeTransformer):
    """Enumerate mutation sites in DFS order; apply exactly one when `target` is set."""

    def __init__(self, lines: set[int], target: int | None = None):
        self.lines = lines
        self.target = target
        self.sites: list[tuple[int, str, str]] = []
        self.applied: tuple[int, str, str] | None = None

    def _consider(self, node: ast.AST, operator: str, description: str, mutate):
        if getattr(node, "lineno", None) not in self.lines:
            return node
        index = len(self.sites)
        self.sites.append((node.lineno, operator, description))
        if self.target == index:
            new = mutate()
            ast.copy_location(new, node)
            self.applied = (node.lineno, operator, description)
            return new
        return node

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        for position, op in enumerate(node.ops):
            swap = COMPARE_SWAP.get(type(op))
            if swap is None:
                continue
            def mutate(position=position, swap=swap):
                ops = list(node.ops)
                ops[position] = swap()
                return ast.Compare(left=node.left, ops=ops, comparators=node.comparators)
            node = self._consider(node, "compare", f"{type(op).__name__} -> {swap.__name__}", mutate)
            if self.applied and self.applied[1] == "compare":
                break
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        swap = ast.Or if isinstance(node.op, ast.And) else ast.And
        return self._consider(node, "boolop", f"{type(node.op).__name__} -> {swap.__name__}",
                              lambda: ast.BoolOp(op=swap(), values=node.values))

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not):
            return self._consider(node, "not", "remove `not`", lambda: node.operand)
        return node

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        swap = BINOP_SWAP.get(type(node.op))
        if swap is None:
            return node
        return self._consider(node, "binop", f"{type(node.op).__name__} -> {swap.__name__}",
                              lambda: ast.BinOp(left=node.left, op=swap(), right=node.right))

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool):
            return self._consider(node, "bool", f"{node.value} -> {not node.value}",
                                  lambda: ast.Constant(value=not node.value))
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return self._consider(node, "int", f"{node.value} -> {node.value + 1}",
                                  lambda: ast.Constant(value=node.value + 1))
        return node

    def visit_Raise(self, node: ast.Raise):
        self.generic_visit(node)
        return self._consider(node, "raise", "raise -> pass", lambda: ast.Pass())


def enumerate_sites(source: str, lines: set[int]) -> list[tuple[int, str, str]]:
    visitor = _Sites(lines)
    visitor.visit(ast.parse(source))
    return visitor.sites


def apply_site(source: str, lines: set[int], index: int) -> tuple[str, tuple[int, str, str]]:
    visitor = _Sites(lines, target=index)
    tree = visitor.visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    if visitor.applied is None:
        raise IndexError(f"mutation site {index} not found")
    return ast.unparse(tree) + "\n", visitor.applied


def generate_mutants(base: dict[str, bytes], candidate: dict[str, bytes], max_mutants: int = 12) -> list[Mutant]:
    mutants: list[Mutant] = []
    candidates: list[tuple[str, str, set[int], int]] = []
    for path in sorted(candidate):
        if not path.endswith(".py"):
            continue
        new_text = candidate[path].decode("utf-8", "replace")
        base_text = base[path].decode("utf-8", "replace") if path in base else None
        lines = changed_line_numbers(base_text, new_text)
        if not lines:
            continue
        try:
            sites = enumerate_sites(new_text, lines)
        except SyntaxError:
            continue
        for index in range(len(sites)):
            candidates.append((path, new_text, lines, index))
    if not candidates:
        return []
    if len(candidates) > max_mutants:
        step = len(candidates) / max_mutants
        chosen = [candidates[int(i * step)] for i in range(max_mutants)]
    else:
        chosen = candidates
    for path, text, lines, index in chosen:
        try:
            source, (lineno, operator, description) = apply_site(text, lines, index)
        except (IndexError, SyntaxError, ValueError):
            continue
        if source.strip() == ast.unparse(ast.parse(text)).strip():
            continue
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:10]
        mutants.append(Mutant(id=f"m{len(mutants) + 1:02d}-{digest}", path=path, lineno=lineno,
                              operator=operator, description=description, source=source))
    return mutants
