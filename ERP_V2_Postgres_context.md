# 项目/模块: ERP_V2_Postgres

## 🗂️ 目录树

```text
ERP_V2_Postgres/
├── backend/                        # 后端核心代码 (FastAPI/Python)
│   ├── ai/                         # AI 模型对接与调度
│   │   └── llm_dispatcher.py       # 大模型接入与分发器 (适配 OpenRouter/DeepSeek 等)
│   ├── api/                        # API 路由接口层
│   │   ├── __init__.py
│   │   └── ai_router.py            # AI 相关接口路由 (如合同解析请求)
│   ├── config/                     # 配置管理
│   │   └── config_manager.py       # 统一配置加载与管理器 (读取 app_config.json)
│   ├── core/                       # 核心业务逻辑层 (领域驱动设计)
│   │   ├── __init__.py
│   │   ├── business_ops.py         # 基础业务操作 (如计提标记、年度归档)
│   │   ├── core_logic.py           # 通用跨模块业务逻辑
│   │   └── finance_engine.py       # 财务计算核心引擎
│   ├── database/                   # 数据库持久层 (PostgreSQL)
│   │   ├── __init__.py
│   │   ├── crud.py                 # 通用增删改查操作
│   │   ├── crud_base.py            # CRUD 基础抽象类
│   │   ├── crud_finance.py         # 财务数据专项 CRUD 逻辑
│   │   ├── crud_sys.py             # 系统/元数据表专项 CRUD 逻辑
│   │   ├── custom_schema.py        # 自定义静态表结构定义
│   │   ├── db_engine.py            # 数据库连接引擎与连接池配置
│   │   └── schema.py               # 动态表结构探测、生成与迁移工具
│   ├── models/                     # 数据模型定义 (SQLAlchemy/Pydantic)
│   │   └── README.md
│   ├── services/                   # 服务层 (封装具体业务流程)
│   │   ├── __init__.py
│   │   ├── ai_service.py           # AI 合同解析、文本提取与结构化服务
│   │   ├── analysis_service.py     # 数据透视与深度分析服务
│   │   ├── auth_service.py         # 用户认证与权限控制服务
│   │   ├── dashboard_service.py    # 首页看板统计数据服务
│   │   ├── excel_service.py        # Excel 文件解析与处理工具
│   │   ├── export_service.py       # 数据导出 (Excel/PDF) 服务
│   │   ├── file_service.py         # 文件上传、下载与存储管理服务
│   │   ├── flow_service.py         # 审批流与业务流程状态管理服务
│   │   ├── import_service.py       # 数据批量导入服务
│   │   └── project_service.py      # 项目生命周期管理服务
│   ├── utils/                      # 工具函数库
│   │   ├── __init__.py
│   │   ├── formatters.py           # 数据格式化 (货币、日期、百分比)
│   │   └── logger.py               # 统一日志记录工具
│   └── __init__.py
├── backups/                        # 数据库逻辑备份目录
├── data/                           # 持久化数据与资源存储
│   ├── backups/                    # 自动/手动备份文件
│   ├── logs/                       # 系统运行日志文件
│   ├── sqlite_db/                  # (旧版) 迁移前的 SQLite 数据库
│   └── uploads/                    # 用户上传的业务文档 (按项目编号分类)
│       └── MAIN20260325002
├── react_enterprise/               # 企业级 React 前端 (Ant Design 构建)
│   └── src/
│       ├── components/             # 复用组件库
│       └── pages/                  # 业务功能页面
├── streamlit_lab/                  # 基于 Streamlit 的实验性 UI / 快速原型
│   ├── .streamlit/                 # Streamlit 界面配置
│   ├── experiments/                # 实验室：新算法与 UI 特性测试
│   │   ├── __init__.py
│   │   ├── ex01_risk_engine.py     # 风险评估引擎实验
│   │   └── ex02_主合同管理页面自定义.py
│   ├── pages/                      # 业务页面导航
│   │   ├── 01_📂_项目看板.py       # 项目总览与数据可视化
│   │   ├── 02_🛠️_主合同管理.py     # 主合同录入、查询与编辑
│   │   ├── 03_🛠️_分包合同管理.py   # 分包合同与劳务管理
│   │   ├── 04_📊_数据分析.py       # 多维度报表统计
│   │   ├── 05_🏢_往来单位.py       # 供应商与客户管理
│   │   ├── 06_📥_导入Excel.py      # 历史数据批量导入工具
│   │   ├── 07_⚙️_系统管理.py       # 用户权限与系统配置
│   │   └── 99_🧪_实验室.py         # 实验性功能入口
│   ├── app.py                      # Streamlit 应用主入口
│   ├── components.py               # Streamlit 自定义 UI 组件封装
│   ├── debug_kit.py                # 开发者调试工具包
│   ├── sidebar_manager.py          # 侧边栏动态导航管理器
│   └── 🏠_Dashboard.py             # 首页统计看板
├── tests/                          # 自动化测试与辅助脚本
│   ├── fix_db.py                   # 数据库结构一键修复脚本
│   ├── generate_mock_data.py       # 生产模拟测试数据生成器
│   ├── run_server.py               # 后端测试服务器快速启动
│   ├── test_ai_parsing.py          # AI 合同解析准确性测试
│   ├── test_finance_scenario.py    # 财务结算场景链路测试
│   └── type_checker.py             # 数据类型一致性检查工具
├── README.md                       # 项目部署与开发说明文档
├── app_config.json                 # 应用全局业务配置 (字段定义、公式、模型)
└── docker-compose.yml              # Docker 容器化编排配置 (PG + Redis + Backend)
```
