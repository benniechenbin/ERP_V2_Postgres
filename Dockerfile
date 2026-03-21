# Dockerfile
FROM python:3.10-slim
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有代码
COPY . .

# 🟢 关键改动：将工作目录切换到 app.py 所在的实际文件夹
WORKDIR /app/streamlit_lab

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]