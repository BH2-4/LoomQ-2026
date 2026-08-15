#!/usr/bin/env python3
"""LoomQ L3 Bonus：量子扩展 RISC-V 模拟器（官方 TinyRISCVEmulator 的 fork）。

本文件是对官方 starter_kit/riscv_emulator.py 的**扩展 fork**（官方文件保持原样）。
在官方 7 指令（li add sub addi beq bne j）之上新增 4 条量子扩展指令：

    qh  qi          # 对量子比特 qi 施加 H 门
    qx  qi          # 对量子比特 qi 施加 X 门
    qcx qc, qt      # 对 qc(控制), qt(目标) 施加 CX 门
    qms qi, rd      # 测量 qi：读数（确定性最大幅度规则）写入寄存器 rd 并坍缩态

编码规格见 l3_bonus_spec.md。端到端测试：python3 starter_kit/l3_selftest.py --bonus
"""

import math
from typing import Dict, List, Tuple

try:
    from riscv_emulator import TinyRISCVEmulator
except ImportError:  # pragma: no cover
    from starter_kit.riscv_emulator import TinyRISCVEmulator  # type: ignore

_S2 = 1.0 / math.sqrt(2.0)


class TinyRISCVQuantumEmulator(TinyRISCVEmulator):
    """官方模拟器扩展：内部维护实数状态向量，量子指令真实参与执行链路。"""

    def load_program(self, asm_code: str):
        super().load_program(asm_code)
        self.max_qubit = -1
        self.qstate: List[float] = [1.0]  # |0…0>，按需增长

    def _ensure_qubits(self, n: int) -> None:
        if n <= self.max_qubit:
            return
        new_size = 1 << (n + 1)
        old = self.qstate + [0.0] * (new_size - len(self.qstate))
        self.qstate = old
        self.max_qubit = n

    def _qh(self, qi: int) -> None:
        self._ensure_qubits(qi)
        bit = 1 << qi
        for base in range(0, len(self.qstate), 1 << (qi + 1)):
            for i in range(bit):
                a = self.qstate[base + i]
                b = self.qstate[base + i + bit]
                self.qstate[base + i] = (a + b) * _S2
                self.qstate[base + i + bit] = (a - b) * _S2

    def _qx(self, qi: int) -> None:
        self._ensure_qubits(qi)
        bit = 1 << qi
        for base in range(0, len(self.qstate), 1 << (qi + 1)):
            for i in range(bit):
                j = base + i
                self.qstate[j], self.qstate[j + bit] = \
                    self.qstate[j + bit], self.qstate[j]

    def _qcx(self, qc: int, qt: int) -> None:
        self._ensure_qubits(max(qc, qt))
        cbit, tbit = 1 << qc, 1 << qt
        for idx in range(len(self.qstate)):
            if (idx & cbit) and not (idx & tbit):
                j = idx | tbit
                self.qstate[idx], self.qstate[j] = self.qstate[j], self.qstate[idx]

    def _qms(self, qi: int, rd: str) -> None:
        """确定性最大幅度测量：p1 > 0.5 → 1，否则 0。

        坍缩采用"全宽度清零 + 归一化"：状态向量维度不变，仅把与读数
        不一致的分量置零，保证后续量子指令的比特下标仍然有效。
        """
        self._ensure_qubits(qi)
        bit = 1 << qi
        p1 = sum(a * a for idx, a in enumerate(self.qstate) if idx & bit)
        outcome = 1 if p1 > 0.5 else 0
        for idx in range(len(self.qstate)):
            if ((idx >> qi) & 1) != outcome:
                self.qstate[idx] = 0.0
        norm = math.sqrt(sum(a * a for a in self.qstate)) or 1.0
        self.qstate = [a / norm for a in self.qstate]
        self.set_register(rd, outcome)

    def execute(self) -> Dict[str, int]:
        steps = 0
        num_instr = len(self.instructions)
        while 0 <= self.pc < num_instr:
            steps += 1
            if steps > self.max_steps:
                raise RuntimeError("程序执行超出最大步数限制，疑似发生死循环")
            op, args = self.instructions[self.pc]
            next_pc = self.pc + 1
            if op == "qh":
                self._qh(int(args[0]))
            elif op == "qx":
                self._qx(int(args[0]))
            elif op == "qcx":
                self._qcx(int(args[0]), int(args[1]))
            elif op == "qms":
                self._qms(int(args[0]), args[1])
            elif op == "li":
                self.set_register(args[0], int(args[1]))
            elif op == "add":
                self.set_register(args[0],
                                  self.get_register(args[1]) + self.get_register(args[2]))
            elif op == "sub":
                self.set_register(args[0],
                                  self.get_register(args[1]) - self.get_register(args[2]))
            elif op == "addi":
                self.set_register(args[0],
                                  self.get_register(args[1]) + int(args[2]))
            elif op == "beq":
                if self.get_register(args[0]) == self.get_register(args[1]):
                    if args[2] not in self.labels:
                        raise ValueError("未定义的跳转标签: %s" % args[2])
                    next_pc = self.labels[args[2]]
            elif op == "bne":
                if self.get_register(args[0]) != self.get_register(args[1]):
                    if args[2] not in self.labels:
                        raise ValueError("未定义的跳转标签: %s" % args[2])
                    next_pc = self.labels[args[2]]
            elif op == "j":
                if args[0] not in self.labels:
                    raise ValueError("未定义的跳转标签: %s" % args[0])
                next_pc = self.labels[args[0]]
            else:
                raise ValueError("不支持的指令操作: %s" % op)
            self.pc = next_pc
        result = {}
        for idx, val in enumerate(self.registers):
            if val != 0:
                result["x%d" % idx] = val
        return result


if __name__ == "__main__":
    code = """
    qh 0
    qcx 0, 1
    qms 0, x10
    qms 1, x11
    li x1, 0
    beq x10, x11, SAME
    li x1, 1
    j END
    SAME:
    li x1, 2
    END:
    """
    emu = TinyRISCVQuantumEmulator()
    emu.load_program(code)
    state = emu.execute()
    print("Bell 态测量相关：x10 与 x11 必然相同 → x1 =", state.get("x1", 0))
    assert state.get("x1", 0) == 2, "量子扩展语义错误"
    print("量子扩展模拟器自测通过")
