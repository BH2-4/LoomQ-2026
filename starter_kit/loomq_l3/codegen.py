"""AST → 官方 7 指令 RISC-V 汇编（li add sub addi beq bne j）。

约定：r1..r9 → x1..x9；c[k] → x(10+k)（评测注入）；临时寄存器 x28/x29，
程序结尾清零以保证"全部寄存器终态"与参考解释器一致。只生成前向跳转，
总步数 ≤ 指令条数。
"""

from __future__ import annotations

from typing import List

from .classic import Assign, Bin, CBit, Cond, If, Num, RReg

_T1 = "x28"
_T2 = "x29"


class _Emitter:
    def __init__(self):
        self.lines: List[str] = []
        self.label_seq = 0

    def emit(self, text: str) -> None:
        self.lines.append(text)

    def label(self, prefix: str) -> str:
        self.label_seq += 1
        return "%s_%d" % (prefix, self.label_seq)


def _gen_expr(node, dst: str, em: _Emitter) -> None:
    if isinstance(node, Num):
        em.emit("li %s, %d" % (dst, node.value))
        return
    if isinstance(node, RReg):
        em.emit("add %s, x%d, x0" % (dst, node.n))
        return
    if isinstance(node, CBit):
        em.emit("add %s, x%d, x0" % (dst, 10 + node.k))
        return
    if isinstance(node, Bin):
        lhs, rhs = node.lhs, node.rhs
        if node.op == "+":
            if isinstance(rhs, Num):
                _gen_expr(lhs, dst, em)
                em.emit("addi %s, %s, %d" % (dst, dst, rhs.value))
                return
            if isinstance(lhs, Num):
                _gen_expr(rhs, dst, em)
                em.emit("addi %s, %s, %d" % (dst, dst, lhs.value))
                return
            _gen_expr(lhs, dst, em)
            _gen_expr(rhs, _T2, em)
            em.emit("add %s, %s, %s" % (dst, dst, _T2))
            return
        # op == '-'
        if isinstance(rhs, Num):
            _gen_expr(lhs, dst, em)
            em.emit("addi %s, %s, %d" % (dst, dst, -rhs.value))
            return
        if isinstance(lhs, Num):
            _gen_expr(rhs, _T2, em)
            em.emit("li %s, %d" % (dst, lhs.value))
            em.emit("sub %s, %s, %s" % (dst, dst, _T2))
            return
        _gen_expr(lhs, dst, em)
        _gen_expr(rhs, _T2, em)
        em.emit("sub %s, %s, %s" % (dst, dst, _T2))
        return
    raise TypeError("不支持的表达式节点 %r" % (node,))


def _gen_stmts(stmts: List[object], em: _Emitter) -> None:
    for stmt in stmts:
        if isinstance(stmt, Assign):
            _gen_expr(stmt.expr, "x%d" % stmt.target, em)
        elif isinstance(stmt, If):
            cond = stmt.cond
            _gen_expr(cond.lhs, _T1, em)
            _gen_expr(cond.rhs, _T2, em)
            then_label = em.label("THEN")
            else_label = em.label("ELSE")
            end_label = em.label("ENDIF")
            branch = "beq" if cond.op == "==" else "bne"
            em.emit("%s %s, %s, %s" % (branch, _T1, _T2, then_label))
            em.emit("j %s" % else_label)
            em.emit("%s:" % then_label)
            _gen_stmts(stmt.then_body, em)
            em.emit("j %s" % end_label)
            em.emit("%s:" % else_label)
            _gen_stmts(stmt.else_body, em)
            em.emit("%s:" % end_label)
        else:
            raise TypeError("不支持的语句节点 %r" % (stmt,))


def compile_classical(stmts: List[object]) -> str:
    """语句列表 → 汇编文本（末尾清零临时寄存器）。"""
    em = _Emitter()
    em.emit("# loomq l3 classical code")
    _gen_stmts(stmts, em)
    em.emit("li %s, 0" % _T1)
    em.emit("li %s, 0" % _T2)
    return "\n".join(em.lines) + "\n"
