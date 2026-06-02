# 🏗️ ERP V2 (PostgreSQL 版) - 生产环境完全离线部署指南

本文档专为实施与运维人员编写，提供基于 Docker 容器化架构的标准部署流程。本系统采用前后端同构的 Streamlit 架构，底层搭载 PostgreSQL 数据库，并深度集成私有化部署的大型语言模型（LLM）实现智能解析功能。

**⚠️ 本指南专为“无互联网连接（内网/政企专网）”的物理机或虚拟机环境编写。**

---

## 📑 1. 架构概览与环境依赖

系统在生产环境中共分为两个核心容器运行：

* **Web 容器 (`erp_web_v2`)**：承载 Python/Streamlit 应用，负责 UI 渲染、业务逻辑及 AI 调度。
* **数据库容器 (`erp_postgres_v2`)**：承载 PostgreSQL 15，负责结构化数据持久化与事务处理。

**宿主机基础要求：**

* **操作系统**：Linux (Ubuntu/CentOS) 或 macOS。
* **硬件配置**：
* **最低配置**：4核 CPU / 8GB 内存 / 50GB 硬盘（无 AI 或极轻量级模型）。
* **推荐配置**：8核+ CPU / 16GB+ 内存 / 100GB 硬盘（可流畅运行 7B 级别的量化大模型进行合同解析）。


* **前置软件**：离线服务器必须已提前安装好 `Docker` 及 `Docker Compose`。

---

## 🚀 2. 离线标准部署步骤

### 步骤一：准备离线安装包与物料

在前往内网机房前，请确保您的 U 盘或移动硬盘中包含以下物料：

1. **基础代码与配置包**：`erp_v2_release.tar`
2. **Web 应用镜像包**：`erp_web_v2.tar`
3. **数据库镜像包**：`postgres_15_alpine.tar`
4. **AI 大模型文件**：如 `DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf`

将上述物料拷贝至服务器目标目录（如 `/opt/erp_v2`）并解压基础代码包：

```bash
mkdir -p /opt/erp_v2
cd /opt/erp_v2
# 解压系统配置与挂载目录包
tar -xvf erp_v2_release.tar 

```

### 步骤二：加载离线 Docker 镜像 (核心)

在无外网环境下，我们需要将打包好的 `.tar` 镜像手动导入到 Docker 引擎中。

```bash
# 导入 PostgreSQL 底座镜像
docker load -i postgres_15_alpine.tar

# 导入 ERP Web 核心业务镜像
docker load -i erp_web_v2.tar

# 验证镜像是否导入成功
docker images
# 您应该能看到 postgres:15-alpine 和 erp_web_v2:latest 的镜像记录

```

### 步骤三：修改 Compose 文件取消在线构建

打开解压后的 `docker-compose.yml`，**必须**将 `web` 服务的在线构建指令删除，改为使用刚才导入的本地镜像。

```yaml
  # 修改前：
  web:
    build: .
    container_name: erp_web_v2
    ...

  # 修改后：
  web:
    image: erp_web_v2:latest  # 🟢 明确指定使用本地已加载的镜像
    container_name: erp_web_v2
    ...

```

### 步骤四：配置环境变量 (.env)

系统通过 `.env` 文件进行敏感配置的凌空注入。项目中提供了一个模板文件。

1. 复制模板文件：
```bash
cp .env.example .env

```


2. 编辑 `.env` 文件，修改数据库密码及其他系统级配置：
```env
# .env 示例内容
DB_USER=erp_admin
DB_PASS=您的超强密码
DB_NAME=erp_core_db
# 其他 AI 或应用配置参数...

```



### 步骤五：部署本地大语言模型

为了实现合同与单据的本地智能解析且保证数据隐私，系统依赖离线 GGUF 模型。

1. 确保目录存在：`mkdir -p backend/models`
2. 将携带的大模型文件移动至该目录下：
```bash
mv /您拷贝的路径/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf ./backend/models/

```



> **⚠️ 注意**：请确保模型名称与系统（或 `.env`）中配置的 `GGUF_MODEL_NAME` 路径完全一致。

### 步骤六：一键离线启动

在 `docker-compose.yml` 所在的根目录下执行以下命令（注意：**不能**加 `--build` 参数）：

```bash
docker-compose up -d

```

**启动验证**：

* 检查容器状态：`docker-compose ps`，确保两个容器均为 `Up` 状态。
* 检查应用日志：`docker-compose logs -f web`，等待出现 `Network URL: http://xxx:8501` 字样即代表启动成功。

---

## 🌐 3. 访问与网络配置

容器成功运行后，默认对外暴露以下端口：

* **🖥️ 前端访问端口：`8501**`
* 请在浏览器中访问：`http://<内网服务器IP>:8501`
* *建议在宿主机配置 Nginx 反向代理，将 8501 映射至 80/443 端口提供内部域名访问。*


* **🗄️ 数据库直连端口：`5435**`
* 系统为防止与宿主机自带的 PG 冲突，将外部的 `5435` 映射到了容器内的 `5432`。
* 实施人员可使用 Navicat 或 DBeaver 通过 `5435` 端口进行直连调试。



---

## 💾 4. 数据持久化与备份策略

Docker 容器是无状态的，但系统已通过 `Volumes` 机制实现了核心数据的绝对安全隔离。**在进行服务器迁移或完整备份时，请务必备份以下三个位置**：

1. **数据库核心数据 (`pgdata` 卷)**：
* 这是由 Docker 托管的命名卷，包含了所有的表、合同记录、系统日志。
* 备份方法 (导出 SQL 脚本)：
```bash
docker exec -t erp_postgres_v2 pg_dump -U erp_admin erp_core_db -c > erp_backup_$(date +%Y%m%d).sql

```




2. **用户上传附件 (`./host_data/uploads`)**：
* 业务员上传的 PDF 合同、Excel 清单物理存储于宿主机此挂载目录。


3. **核心业务配置 (`app_config.json`)**：
* 位于项目根目录。它控制了系统内所有动态表单的渲染逻辑、计算公式以及只读/必填属性。任何针对配置的修改都保存在此文件中。



---

## 🛠️ 5. 日常运维指南

### 常用管理命令

```bash
# 查看所有服务的实时日志
docker-compose logs -f

# 仅查看 Web 服务的报错日志 (有助于排查 AI 解析故障)
docker-compose logs -f web

# 重启整个系统 (当修改了 app_config.json 或 Python 代码后使用)
docker-compose restart web

# 彻底停止并销毁容器 (保留数据卷)
docker-compose down

# 进入 Web 容器内部 (如需手动执行特定脚本)
docker exec -it erp_web_v2 /bin/bash

```

### 数据库初始化与热修复

如果系统底层物理表因为配置升级需要新增字段，系统管理员可以通过前端的 **`实验室 (Sandbox) -> 开发者控制台 -> 系统全量配置`** 面板，执行修改配置并触发底层 schema 热同步，无需手动进入数据库执行 `ALTER TABLE` DDL 语句。