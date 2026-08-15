"""L3 混合编译入口：compile_hybrid(hybrid_qasm_str) -> (quantum_ops, assembly)。"""

from __future__ import annotations

from typing import List, Tuple

try:
    from . import classic, parser
except ImportError:  # pragma: no cover
    from loomq_l3 import classic, parser  # type: ignore

try:
    from loomq import parse_qasm
except ImportError:  # pragma: no cover
    from starter_kit.loomq import parse_qasm  # type: ignore

from .codegen import compile_classical  # noqa: E402,F401  (相对导入，包内总是可用)


def compile_hybrid(hybrid_qasm_str: str) -> Tuple[List[dict], str]:
    quantum_text, classical_text = parser.split_hybrid(hybrid_qasm_str)
    circuit = parse_qasm(quantum_text)
    quantum_ops: List[dict] = []
    for op in circuit.ops:
        quantum_ops.append({
            "op": op.name,
            "params": list(op.params),
            "qubits": list(op.qubits),
            "measure": None,
        })
    for qubit, clbit in circuit.measures:
        quantum_ops.append({"op": "measure", "params": [], "qubits": [qubit],
                            "measure": [qubit, clbit]})
    stmts = classic.parse_classical(classical_text) if classical_text.strip() else []
    assembly = compile_classical(stmts)
    return quantum_ops, assembly


__all__ = ["compile_hybrid"]
