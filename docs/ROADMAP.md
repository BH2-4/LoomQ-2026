# LoomQ-2026 核心路径作战文档

> Team: BH2-4 · 截止 2026-08-25 12:00 UTC+8 · 以 Issue created_at 为准
> 事实源 = 仓库原文（`problem_statement.md` 等），每天 `git fetch upstream` 检查规则更新。

## 0. 北极星

**把不确定性压到单一模块，其余全拿确定性分数。**

| 分数块 | 分值 | 性质 | 策略 |
|---|---:|---|---|
| L1 语义等价（自动） | 35 | 确定性 | 自研解析器+模拟器+三 IR codegen，满分冲刺 |
| L3 混合编译（自动） | 15 | 确定性 | 确定性编译器 + 穷举注入自测，满分冲刺 |
| L2 客观（自动） | 20 | **唯一方差源** | 选后端查表必拿；生成/纠错走验证修复回路 |
| L1 真机（人工） | 10 | 摩擦分 | 双平台早注册早跑（SpinQ + 本源） |
| L2 体验（人工） | 10 | 打磨分 | 门槛：L2 客观 ≥12，先保客观再打磨 |
| 工程与产品化（人工） | 10 | 打磨分 | 本文档即架构文档雏形；一键复现 |
| Bonus | +12 | 纵深 | L3 扩展指令三项材料 +8；新手引导可视化 +4 |

保底盘 ≈ 77 分（L1 35 + L3 15 + 选后端 ~7 + 真机 10 + 工程 10），冲高空间在 L2 生成/纠错与体验/引导。

## 1. 架构决策（ADR 摘要）

- **ADR-1 纯标准库状态向量模拟器**：正式评测默认禁网，`run()` 必须离线出结果；评测电路 ≤ 数比特、12 门白名单，自研零依赖模拟器最快且无版本风险。`requirements.txt` 保持基线。
- **ADR-2 单源三目标 codegen**：QASM2 解析 → 统一中间 IR → 分别生成 spinq(QASM2)/braket(QASM3)/originq(OriginIR)。禁止三套独立硬编码（评委四问第一条）。
- **ADR-3 L2 = 模板路由 + LLM 参数抽取 + 验证回路**：意图分类（生成/纠错/选后端）→ 模板库+LLM 只输出 JSON 参数（`json_object`，仅用 `json`/`re` 解析）→ 本地模拟器验证 Fidelity≥0.97 → 失败带错误回喂修复 1-2 次 → 降级最近模板。选后端纯查 `backend_capabilities.json`，回复必含规范标识原文（如 `braket_local_simulator`）。QUASAR（arXiv:2510.00967）已验证此路线。
- **ADR-4 L3 = 确定性编译**：Hybrid-QASM 文法（整数、r1-r9、`+ - == !=`、if/else、c[k]→x10..）递归下降解析 → 代码生成到 7 指令汇编（`li add sub addi beq bne j`）。自测 = 自建用例生成器穷举所有测量值组合比对参考解释器。
- **ADR-5 评测对齐双保险**：公开 evaluator + 自建"隐藏集模拟器"（8 电路全集 / L2 变体 ≥20 个 / L3 随机文法用例），每次 push CI 全跑。

## 2. 工作包与依赖

```text
WP0 调研冻结 ─┬─> WP1 L1 内核 ─┬─> WP2 隐藏集对齐 ─┬─> WP3b 真机跑+证据
              │                └─> WP4 L2 客观 ────┴─> WP5 体验/工程/Bonus4
              ├─> WP3a 账户申请（今天启动，纯等待，不阻塞） 
              └─> WP6 L3 编译器+Bonus8（独立，随时插入，建议 WP2 后）
WP7 冻结提交（预演 8-24，最终 8-25 上午留缓冲）
```

## 3. 里程碑时间轴（今天 = 8-14）

| 日期 | 里程碑 | 验收（可复制命令） |
|---|---|---|
| 8-14 | WP0+WP3a：本文档入库；SpinQ/本源注册+Token 申请发出 | 账户申请提交记录截图 |
| 8-14→8-16 | WP1 L1 内核 | `python3 starter_kit/evaluator.py --level l1 --target spinq,originq,braket` 退出码 0 |
| 8-16→8-17 | WP2 隐藏集对齐 | 自建 8 电路 + 100 组随机电路回归，保真度全 ≥0.97 |
| 8-17→8-19 | WP4 L2 客观 | 自建 ≥20 变体 case 通过率 ≥90%，单 case <120s（含 1 次修复） |
| 8-18→8-19 | WP3b 真机证据 | 两平台 result.json + job_id 控制台可溯源，evidence 填毕 |
| 8-19→8-21 | WP5 体验+工程 | 零基础用户 5 分钟跑通首实验；干净环境一键 setup+run |
| 8-21→8-23 | WP6 L3+Bonus8 | `evaluator --level l3` 通过 + 穷举注入自测全对 + 指令规格/扩展/测试三项齐 |
| 8-23→8-24 | 冻结打磨 + 预演提交 | `prepare_submission --team-id BH2-4` 通过 + 预演 Issue 获 accepted 回执 |
| 8-25 上午 | 最终提交 | 最终 Issue `submission:accepted`（截止 12:00） |

## 4. 红线（勿做清单）

- 不硬编码任何 URL/Key/模型名；错误信息不回显密钥（官方测试在盯）
- 不动 `tests/`、`.github/`、`competition/`、`l2_policy.json`；`starter_kit/` 结构与四必需文件保留
- 不做关键词匹配/打表——变体复测+代码审查会直接清零对应 Level
- 依赖必须 `==` 精确锁定；目标是 `requirements.txt` 维持零依赖基线
- 密钥只进本地环境变量；evidence 不放 Key；归档 ≤100 MiB
- Issue 只能新建不能编辑；证据必须进最终 commit，赛后不补

## 5. 每日例程

1. `git fetch upstream && git log upstream/main --oneline -5`——检查规则/契约更新
2. `python3 starter_kit/evaluator.py --json-out report.json`——全量契约自测
3. 更新本文档进度标记（⬜/✅），阻塞项当天升级

## 6. 进度

- [x] WP0 调研冻结（本文档）
- [ ] WP3a 账户申请（✅ SpinQ 公钥认证已通；本源 Token 已验证，机器维护中自动探测）
- [x] WP1 L1 内核（2026-08-14：解析器/模拟器/codegen 完成，公开评测 6/6、官方契约测试 26/26、30 组随机电路回环一致）
- [x] WP1b 基本流程验证（evaluator / 官方 tests / git push / prepare_submission 预检全通过）
- [ ] WP2 隐藏集对齐（✅ 2026-08-15：selfcheck.py 119 项全过，抓出并修复 originq TDAG 契约违规；每日常跑）
- [ ] WP4 L2 客观
- [x] WP3b 真机证据（✅ 2026-08-15 双平台闭合：SpinQ 核磁 G-260815-0001/S-260815-0002 + 本源 WK_C180_2 两 job，Top-K 全中；超导双保险探测已按用户指示关闭——官方统一开放测试在赛末）
- [ ] WP5 体验/工程
- [ ] WP6 L3+Bonus
- [ ] WP7 冻结提交
