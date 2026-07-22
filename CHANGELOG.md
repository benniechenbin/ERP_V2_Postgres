# 📝 更新日志 / Changelog

本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/) 与 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范。

---

## [0.1.0] - 2026-07-22

### Added
- **基础轻量架构**: 引入基于 Streamlit + PostgreSQL (备用 SQLite) 的轻量化前后端同构轻量 ERP 架构。
- **配置驱动引擎**: 引入 `app_config.json` 规则加载器，动态控制物理建表、视图字段扩展与输入表单渲染。
- **核心模块**:
  - 主合同与分包合同流程管理与防超付限制校验。
  - AI 合同识别调度器 (`backend/ai/llm_dispatcher.py`)。
  - 财务双向现金流与数据报表分析。
- **前端预留**: 创建 `frontend/` 占位目录及其基础 npm 配置。
- **工程与 CI 规范**:
  - 增加 `scripts/ci.py` 自动化检查工具（支持 `docs-check` 与 `version-check`）。
  - 补充 `ROADMAP.md`、`CHANGELOG.md` 及 `docs/` 项目治理文档标准。
