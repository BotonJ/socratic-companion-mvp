# 学习伴侣系统 (Learning Companion System)

> 苏格拉底教学法的最小可运行系统

一个基于Prompt驱动的轻量级AI学习伴侣系统，融合苏格拉底教学法和虚拟角色扮演，让学习变得高效有趣。

## 项目简介

本系统基于三个实战方案设计：
- **吴乐旻的"苏格拉底·七"系统**：理论框架创始人
- **洛星尘的《与行星相会》系统**：DeepSeek 1M上下文实战
- **胡魏的经济学课堂实录**：命令化启动+自动更新

## 核心特性

- 🎯 **苏格拉底教学法**：问题驱动，学生自己推理
- 👥 **多角色互动**：3人团队，分工明确
- 📚 **文档化管理**：进度、人设、日记全部文档化
- 🚀 **轻量级架构**：纯Prompt驱动，无需复杂编码

## 快速开始

### 使用Claude Code

1. 克隆本项目：
```bash
git clone https://github.com/BotonJ/socratic-companion-mvp.git
cd socratic-companion-mvp
```

2. 将学习材料（PDF/MD）放入 `materials/` 目录

3. 让 Claude 读取 `START.md`，然后说"开始上课"

### 使用其他工具

本系统兼容任何支持长上下文和Prompt驱动的AI工具：
- Cursor + Claude Code
- DeepSeek官网（1M上下文）
- 其他Agentic Engineering工具

## 项目结构

```
socratic-companion-mvp/
├── templates/           # Prompt模板库
│   └── system.md      # 系统核心（最高指令）
│
├── personas/           # 角色人设库
│   └── sanqyue-seven.md # 三月七人设（示例）
│
├── session/            # 会话状态
│   ├── progress.md    # 学习进度
│   ├── diary.md       # 学习日记
│   └── notes.md       # 学习笔记
│
├── materials/          # 教材目录
├── agents/             # Agent定义（预留）
├── skills/             # 技能定义（预留）
└── commands/           # 斜杠命令（预留）
```

## 设计理念

> "苏格拉底·七完全抛弃数值化，它的游戏性不再依赖张牙舞爪的征服欲，而基于温情脉脉的朋友之谊，这反而对学习动力形成了隽永的呵护。"
>
> —— 吴乐旻

## 路线图

### Phase 1（当前）- 核心框架 ✅
- [x] 系统核心Prompt
- [x] 示例角色人设（三月七）
- [x] 学习进度管理
- [x] 学习日记

### Phase 2（规划中）- 增强功能
- [ ] 命令化启动（`/teach-me`、`/read-with`）
- [ ] 多角色人设库
- [ ] 课后自动更新机制
- [ ] 知识树可视化

### Phase 3（规划中）- 高级功能
- [ ] Agent编排
- [ ] 多模态支持（图像/图表）
- [ ] 协作学习模式
- [ ] 学习分析报表

## 许可证

MIT License

## 致谢

- 吴乐旻 - "苏格拉底·七"系统设计
- 洛星尘 - 《与行星相会》实战方案
- 胡巍 - 经济学课堂实录

---

**祝你学习愉快！** 🎓✨