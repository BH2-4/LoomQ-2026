#!/usr/bin/env python3
"""L3 穷举属性测试：随机 Hybrid-QASM 用例 × 全部测量值注入组合，
官方 TinyRISCVEmulator 跑我们的汇编 vs 参考解释器，要求 100% 一致。

用法：
  python3 starter_kit/l3_selftest.py            # 穷举属性测试（--bonus 见 M4）
  python3 starter_kit/l3_selftest.py --bonus    # Bonus 扩展指令端到端闭环
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))

try:
    from riscv_emulator import TinyRISCVEmulator
except ImportError:  # pragma: no cover
    from starter_kit.riscv_emulator import TinyRISCVEmulator  # type: ignore

from loomq_l3 import compile_hybrid  # noqa: E402
from loomq_l3 import classic, interp  # noqa: E402

N_CASES = 200


# ---------------- 随机用例生成 ----------------

def rand_expr(rng: random.Random, regs, cbits, depth: int):
    roll = rng.random()
    if roll < 0.35 or depth <= 0:
        choices = [lambda: classic.Num(rng.randint(-20, 20))]
        if regs:
            choices.append(lambda: classic.RReg(rng.choice(regs)))
        if cbits:
            choices.append(lambda: classic.CBit(rng.choice(cbits)))
        return rng.choice(choices)()
    lhs = rand_expr(rng, regs, cbits, depth - 1)
    rhs = rand_expr(rng, regs, cbits, depth - 1)
    return classic.Bin(rng.choice("+-"), lhs, rhs)


def rand_stmts(rng: random.Random, regs, cbits, count: int, depth: int):
    stmts = []
    for _ in range(count):
        if depth > 0 and rng.random() < 0.4:
            lhs = rand_expr(rng, regs, cbits, depth - 1)
            rhs = rand_expr(rng, regs, cbits, depth - 1)
            cond = classic.Cond(rng.choice(["==", "!="]), lhs, rhs)
            then_body = rand_stmts(rng, regs, cbits, rng.randint(1, 3), depth - 1)
            else_body = rand_stmts(rng, regs, cbits, rng.randint(0, 2), depth - 1)
            stmts.append(classic.If(cond, then_body, else_body))
        else:
            target = rng.choice(regs)
            expr = rand_expr(rng, regs, cbits, 2)
            stmts.append(classic.Assign(target, expr))
    return stmts


def render_expr(node) -> str:
    if isinstance(node, classic.Num):
        return str(node.value)
    if isinstance(node, classic.RReg):
        return "r%d" % node.n
    if isinstance(node, classic.CBit):
        return "c[%d]" % node.k
    return "(%s %s %s)" % (render_expr(node.lhs), node.op, render_expr(node.rhs))


def render_stmts(stmts) -> str:
    lines = []
    for stmt in stmts:
        if isinstance(stmt, classic.Assign):
            lines.append("r%d = %s;" % (stmt.target, render_expr(stmt.expr)))
        else:
            cond = stmt.cond
            lines.append("if (%s %s %s) {" % (render_expr(cond.lhs), cond.op,
                                              render_expr(cond.rhs)))
            lines.append(render_stmts(stmt.then_body))
            if stmt.else_body:
                lines.append("} else {")
                lines.append(render_stmts(stmt.else_body))
            lines.append("}")
    return "\n".join(lines)


def build_hybrid(rng: random.Random, stmts, m_bits: int) -> str:
    n_qubits = max(2, m_bits + 1)
    gates = ["h q[0];", "cx q[0], q[1];"]
    if m_bits >= 2:
        gates.append("cx q[1], q[2];")
    measures = ["measure q[%d] -> c[%d];" % (k, k) for k in range(m_bits)]
    return ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[%d];\ncreg c[%d];\n'
            % (n_qubits, m_bits)
            + "\n".join(gates) + "\n" + "\n".join(measures)
            + "\nclassical {\n" + render_stmts(stmts) + "\n}\n")


# ---------------- 穷举比对 ----------------

def expected_state(r_values, cvals):
    state = {}
    for i, value in enumerate(r_values, start=1):
        if value != 0:
            state["x%d" % i] = value
    for k, value in cvals.items():
        if value != 0:
            state["x%d" % (10 + k)] = value
    return state


def run_property(seed: int = 20260816, cases: int = N_CASES) -> int:
    rng = random.Random(seed)
    mismatches = []
    total_combos = 0
    max_instr = 0
    for case_no in range(cases):
        m_bits = rng.randint(1, 4)
        regs = sorted(rng.sample(range(1, 10), rng.randint(1, 3)))
        cbits = list(range(m_bits))
        stmts = rand_stmts(rng, regs, cbits, rng.randint(2, 6),
                           rng.randint(1, 4))
        source = build_hybrid(rng, stmts, m_bits)
        quantum_ops, assembly = compile_hybrid(source)
        parsed = classic.parse_classical(
            source.split("classical {", 1)[1].rsplit("}", 1)[0])
        max_instr = max(max_instr, len([line for line in assembly.splitlines()
                                        if not line.startswith("#")]))
        for mask in range(1 << m_bits):
            cvals = {k: (mask >> k) & 1 for k in range(m_bits)}
            reference = expected_state(interp.run_program(parsed, cvals), cvals)
            emulator = TinyRISCVEmulator()
            emulator.load_program(assembly)
            for k, value in cvals.items():
                emulator.set_register("x%d" % (10 + k), value)
            got = emulator.execute()
            total_combos += 1
            if got != reference:
                mismatches.append((case_no, mask, got, reference, source))
                break
    print("随机用例 %d 个，注入组合 %d 组，指令数峰值 %d（上限 1000 步）"
          % (cases, total_combos, max_instr))
    if mismatches:
        case_no, mask, got, reference, source = mismatches[0]
        print("首个失配：case %d mask %d\n汇编终态 %s\n参考终态 %s\n用例：\n%s"
              % (case_no, mask, got, reference, source))
        print("L3 属性测试：失败（%d 个用例失配）" % len(mismatches))
        return 1
    print("L3 属性测试：0 失配，全部一致")
    return 0


# ---------------- Bonus 端到端（M4） ----------------

def run_bonus(seed: int = 20260816, cases: int = 40) -> int:
    try:
        from riscv_emulator_qext import TinyRISCVQuantumEmulator
        from qext_codegen import compile_hybrid_qext
    except ImportError:
        print("Bonus 组件未实现")
        return 1
    rng = random.Random(seed)
    checked = 0
    for case_no in range(cases):
        m_bits = rng.randint(1, 3)
        regs = sorted(rng.sample(range(1, 10), rng.randint(1, 3)))
        stmts = rand_stmts(rng, regs, list(range(m_bits)), rng.randint(2, 5), 2)
        source = build_hybrid(rng, stmts, m_bits)
        quantum_ops, assembly = compile_hybrid_qext(source)
        emulator = TinyRISCVQuantumEmulator()
        emulator.load_program(assembly)
        got = emulator.execute()
        # 期望：先模拟量子部分得确定性测量（p1>0.5 → 1），再跑参考解释器
        from loomq import parse_qasm, simulate, probabilities
        from loomq_l3.parser import split_hybrid
        quantum_text, _ = split_hybrid(source)
        probs = probabilities(simulate(parse_qasm(quantum_text)))
        cvals = {}
        for k in range(m_bits):
            p1 = sum(p for idx, p in enumerate(probs) if (idx >> k) & 1)
            cvals[k] = 1 if p1 > 0.5 else 0
        reference = expected_state(interp.run_program(
            classic.parse_classical(
                source.split("classical {", 1)[1].rsplit("}", 1)[0]), cvals), cvals)
        # QMS 写入的测量寄存器 x10+ 也应出现在终态
        for k, value in cvals.items():
            if value:
                reference["x%d" % (10 + k)] = value
        if got != reference:
            print("Bonus 失配：case %d\n终态 %s\n期望 %s\n%s" % (case_no, got, reference, source))
            return 1
        checked += 1
    print("Bonus 端到端：%d 用例全部一致（量子指令真实执行于扩展模拟器）" % checked)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bonus", action="store_true")
    parser.add_argument("--cases", type=int, default=N_CASES)
    args = parser.parse_args()
    return run_bonus(cases=args.cases) if args.bonus else run_property(cases=args.cases)


if __name__ == "__main__":
    sys.exit(main())
