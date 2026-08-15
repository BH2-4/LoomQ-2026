# 官方 Q&A 关键结论（飞书文档，2026-08-12 更新版）

来源：赛道 Q&A 合集 https://my.feishu.cn/docx/LiLpdc5XuoJkzexPXhSc8k0unvd
微信赛道介绍：https://mp.weixin.qq.com/s/HAkbtjtDwrdH6rzNxlqFpQ

## 对我们策略的影响

| 问题 | 官方答复 | 我们的行动 |
|---|---|---|
| 本源真机显示"维护中" | 真机运行成本高，**权限在特定时间段集中开放**；主要功能测试以打通 QASM 为主 | 分时段探测策略正确；已用 pyqpanda3 动态发现 WK_C180_2 在线并完成取证 |
| 是否必须 origin_72 | **不强制唯一物理后端**，有人用"悟空 180（WK_C180_2）"获官方认可 | 已采用 WK_C180_2 取证（job_id 可溯源） |
| L2 生成物限制 | 只能生成 **OpenQASM 2.0 + 12 门白名单** | 模板库架构正确命中，L2 输出按白名单生成 |
| L3 Bonus 口径 | 必须做"方向 1"：自定义指令编码**实际进入可运行、可验证的执行链路**（最小闭环即可，不要求完整汇编器/解码器）；**闭环到开源和明确 GPU 设备的指令集是加分项** | WP6 设计：指令编码 + 模拟器执行闭环 + 端到端测试；有条件再考虑 GPU 侧描述 |
| 决赛答辩 | 无需现场答辩，提交材料写清楚即可 | 按 README/evidence 完整叙事即可 |
| 报名表 | 公告给出报名表链接（8.1-8.25）；仓库 intake 逻辑不依赖报名表（Team ID=Issue 作者） | 建议 1 分钟填写保险：https://my.feishu.cn/share/base/form/shrcnJcMDs843ZKPUzsxhD25rxc |

## 真机取证记录（2026-08-15）

- SpinQ 量旋云（核磁真机，`spinq_cloud_qpu` 范围含超导/核磁 2-8 比特）：
  - Bell @ gemini_vp，job `G-260815-0001`，Top-2 {11,00} ✅
  - GHZ-3 @ triangulum_vp，job `S-260815-0002`，Top-2 {111,000} ✅
- 本源量子云（超导真机 WK_C180_2，官方认可的非强制后端）：
  - Bell，job `2E213684ED8EB081361832057F1D12B3`，Top-2 {11,00} ✅
  - GHZ-3，job `B054B2797AD542992605601384F9DB4B`，Top-2 {111,000} ✅

## 后端发现命令（pyqpanda3）

```python
from pyqpanda3 import qcloud
service = qcloud.QCloudService(api_key=TOKEN)   # token 走环境变量
service.backends()  # {'HanYuan_01': False, 'PQPUMESH8': True, 'WK_C180': True, 'WK_C180_2': True, ...}
```
旧 pyqpanda（QPanda2）固定芯片名 origin_72/wuyuan_d3 全部不可用属正常现象，勿再走该通道。
