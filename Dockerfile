# Dockerfile
FROM python:3.10-slim

# 🟢 1. 设置系统级环境变量
# 避免 Python 生成 .pyc 垃圾文件，并强制无缓冲输出日志
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 🟢 关键防御：告诉 Python 解释器，把 /app 作为根目录去寻找包
# 这样无论你的 WORKDIR 切到哪里，import backend 都会永远生效
ENV PYTHONPATH=/app

# 2. 设置初始工作目录
WORKDIR /app

# 3. 依赖安装 (利用 Docker 层缓存机制)
COPY requirements.txt .
# 加上一些基础的编译工具，防止部分包（如 psycopg2 或 llama-cpp）在 linux 下缺少 C 编译器报错
RUN apt-get update && apt-get install -y gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制代码全家桶
COPY . .

# 🟢 5. 切换到前端运行目录
WORKDIR /app/streamlit_lab

# 6. 暴露端口与启动指令
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]