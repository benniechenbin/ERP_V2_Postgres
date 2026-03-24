# 🤖 本地大模型存放目录

为了防止 Git 仓库爆满，大型模型文件已被 `.gitignore` 忽略。
系统如果需要纯离线运行，请手动下载模型并放入此文件夹。

## 📥 下载指引

1. **模型名称**: DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf
2. **下载地址** (国内满速直链): 
   `https://hf-mirror.com/unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf`
3. **摆放位置**: 下载完成后，将 `.gguf` 文件直接放在当前目录下。

配置完成后，在项目根目录的 `.env` 中设置 `AI_PROVIDER=local_gguf` 即可唤醒本地离线引擎。