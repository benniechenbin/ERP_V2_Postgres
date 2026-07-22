# 📚 架构决策与设计文档 / Architecture & Design Documents

本目录存放项目的详细设计、架构决策及需求说明。

## 📂 目录结构与职责

- `docs/adr/`: **Architecture Decision Records (架构决策记录)**
  - 用于记录对项目架构产生长期重大影响的技术决定。
  - 允许的状态值：`Proposed` → `Accepted` → `Deprecated / Superseded`

- `docs/rfc/`: **Request for Comments (技术方案设计)**
  - 用于重大新功能或重构前的技术方案讨论与设计评估。
  - 允许的状态值：`Proposed` → `Accepted` → `Superseded / Rejected`

- `docs/prd/`: **Product Requirement Documents (产品需求文档)**
  - 用于明确具体业务需求、交互流程与验收标准。
  - 允许的状态值：`Draft` → `Review` → `Accepted` → `In Progress` → `Released`

---

## 📝 状态标注规范

所有 ADR / RFC / PRD 文档在创建时，必须在文档顶部包含元信息卡片，示例如下：

```markdown
# ADR-001: 采用配置驱动的多数据库热扩容架构

* **状态：** Accepted
* **日期：** 2026-07-22
* **作者：** 开发团队
```
