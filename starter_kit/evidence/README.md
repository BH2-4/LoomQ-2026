# LoomQ 人工评分证据

这份文件是人工评分材料的统一入口。请直接编辑它，只填写要申报的项目。截图、原始结果或图表统一放在 `starter_kit/evidence/files/`，也可以引用 `starter_kit/` 中已有的代码和文档。

证据包是可选的。没有申报某项人工分时，留空即可，不影响自动评分。

## 提交前填写

把要申报项目的方框改成 `[x]`，并填写对应内容：

- [x] L1 真机
- [ ] L2 交互体验
- [ ] 工程与产品化
- [x] 自定义量子 RISC-V Bonus
- [ ] 新手引导与视觉叙事 Bonus

## L1 真机

每个有效真机平台计 5 分，最多两个平台。模拟器不计真机分。每个平台复制并填写一次下面的信息：

### 平台 1：SpinQ 量旋云（核磁量子真机，属官方能力表 `spinq_cloud_qpu` 的 2–8 比特真机范围）

```text
平台名称：SpinQ 量旋云 · 核磁量子计算机（Bell 用 2 比特 Gemini，GHZ-3 用 3 比特 Triangulum）
平台 job ID：Bell = G-260815-0001；GHZ-3 = S-260815-0002
运行时间：2026-08-15 02:58 UTC（Bell）；2026-08-15 03:00 UTC（GHZ-3）
shots：各 1000
实际执行的 QASM：starter_kit/circuits/bell.qasm 与 starter_kit/circuits/ghz3.qasm（实际提交的是其中间层规范化输出，已原样保存在证据 JSON 的 qasm_contract_output 字段）
平台返回的原始结果：evidence/files/spinq/bell_G-260815-0001.json；evidence/files/spinq/ghz3_S-260815-0002.json
任务页截图：无（job ID 可在量旋云控制台任务记录中溯源复核）
```

主峰校验：Bell Top-2 = {11, 00}；GHZ-3 Top-2 = {111, 000}，与理想分布一致。

### 平台 2：本源量子云（超导真机 悟空 180 / WK_C180_2，官方 Q&A 认可的非强制真机后端）

```text
平台名称：本源量子云 · 悟空 180 真机（后端 WK_C180_2，经 pyqpanda3 动态后端发现接口提交）
平台 job ID：Bell = 2E213684ED8EB081361832057F1D12B3；GHZ-3 = B054B2797AD542992605601384F9DB4B
运行时间：2026-08-15 15:23 UTC（两个任务）
shots：各 1000
实际执行的 QASM：starter_kit/circuits/bell.qasm 与 starter_kit/circuits/ghz3.qasm（实际提交的规范化 QASM2 保存在证据 JSON 的 qasm_submitted 字段）
平台返回的原始结果：evidence/files/originq/bell_WK_C180_2_2E213684ED8EB081361832057F1D12B3.json；evidence/files/originq/ghz3_WK_C180_2_B054B2797AD542992605601384F9DB4B.json
任务页截图：无（task_id 可在本源量子云控制台任务查询中溯源复核）
```

主峰校验：Bell Top-2 = {11, 00}（52.5% / 46.8%）；GHZ-3 Top-2 = {111, 000}（37.6% / 34.1%），与理想分布一致。

建议把文件放进 `evidence/files/`，比如：

```text
evidence/files/spinq-circuit.qasm
evidence/files/spinq-result.json
evidence/files/spinq-screenshot.png
```

工作人员会核对 job ID、运行时间、电路、shots 和原始结果。截图只能辅助说明，不能代替 job ID 和原始结果。

## L2 交互体验

请填写：

```text
启动界面或 CLI 的命令：[填写]
测试入口或页面地址：[填写，没有则写“无”]
用于交互体验评测的 3 个用户任务：
1. [填写]
2. [填写]
3. [填写]
截图或演示视频：[选填，填写仓库内路径或稳定只读链接]
```

工作人员会在组委会统一模型环境中运行最终代码，测试新手是否看得懂、出错后能否得到有效帮助、结果是否清楚，以及多轮回答是否一致。选手自己的对话截图只用于说明产品流程，不直接证明得分。

## 工程与产品化

已有内容可以直接引用主 README 或其他项目文档，不必复制到本目录。

```text
干净环境中的构建和启动命令：[填写命令或文档路径]
架构说明：[填写文档路径，或用几句话说明主要模块]
目标用户和使用场景：[填写]
完整使用流程：[填写文档、截图或演示路径]
```

工作人员会按最终 commit 实际构建和启动，并检查文档与代码是否一致、产品是否真的降低了量子计算的使用门槛。

## 自定义量子 RISC-V Bonus

以下三项必须齐全且测试通过，才获得 8 分：

```text
指令编码规格：starter_kit/l3_bonus_spec.md
模拟器扩展实现：starter_kit/riscv_emulator_qext.py（官方 riscv_emulator.py 的扩展 fork，原文件未改动）
端到端测试命令：python3 starter_kit/l3_selftest.py --bonus（另有模拟器自测：python3 starter_kit/riscv_emulator_qext.py）
```

扩展指令集为 QH/QX/QCX/QMS（Hadamard、X、受控非、测量入寄存器），编码占用
RISC-V CUSTOM-0（opcode 0x0B）扩展空间；量子部分编译为量子指令、经典部分仍为
官方 7 指令，混合程序在扩展模拟器上一次执行完成"量子演化→测量读数→经典控制"
闭环。端到端测试对 200 个随机 Hybrid 用例与独立状态向量参考全对拍，0 失配。

## 新手引导与视觉叙事 Bonus

请填写已有材料的路径，不要求为评分另写一套文档：

```text
零基础首次运行指南：[填写]
量子概念解释：[填写]
结果可视化：[填写]
错误恢复或无障碍引导：[填写]
```

以上四项各 1 分。普通项目 README 完整不代表自动获得 Bonus。

## 提交规则

- 所有材料都要在截止前进入最终提交的 commit，工作人员不接受截止后补交。
- 外部视频可以用稳定只读链接，源码、原始结果和复现命令应保存在仓库中。
- 整个 fork commit 的归档包不得超过 100 MiB。
- 不要提交 API Key、Token、Cookie、个人身份信息或平台账户隐私。
- 如申报 L1 真机分，在最终提交 Issue 的 `Hardware evidence` 中填写 `starter_kit/evidence/README.md`。
