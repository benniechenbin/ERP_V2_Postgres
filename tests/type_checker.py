import os
import re

# 需要检查的关键字
KEYWORDS = ["list", "str", "dict", "float", "int", "tuple", "set", "type"]

# 定义正则表达式模式
PATTERNS = {
    "直接赋值": r"\b({})\s*=\s*",
    "循环变量": r"for\s+({})\s+in",
    "函数参数": r"def\s+\w+\s*\(.*?\b({})\b.*?\):",
    "通配符导入": r"from\s+\S+\s+import\s+\*",
    "isinstance误用": r"isinstance\s*\(\s*[^,]+,\s*['\"]", # 检查是否写成了 isinstance(x, "str")
}

def scan_project(root_dir):
    print(f"🚀 开始全项目扫描: {root_dir}")
    print("-" * 60)
    found_count = 0

    for root, dirs, files in os.walk(root_dir):
        # 跳过虚拟环境和缓存
        if any(x in root for x in [".venv", "venv", "anaconda3", "__pycache__", ".git"]):
            continue

        for file in files:
            if file.endswith(".py") and file != "type_checker.py":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            # 过滤掉注释行
                            if line.strip().startswith("#"): continue
                            
                            for label, pattern in PATTERNS.items():
                                # 填充关键字到正则中
                                final_pattern = pattern.format("|".join(KEYWORDS))
                                matches = re.findall(final_pattern, line)
                                
                                if matches:
                                    # 处理 findall 结果
                                    target = matches[0] if isinstance(matches[0], str) else ""
                                    print(f"🚩 [发现风险] {label}: {target}")
                                    print(f"   文件: {file_path}")
                                    print(f"   行号: {i + 1} | 内容: {line.strip()}")
                                    print("-" * 40)
                                    found_count += 1
                except Exception as e:
                    print(f"⚠️ 无法读取文件 {file_path}: {e}")

    if found_count == 0:
        print("✅ 扫描完毕！未发现明显的关键字污染风险。")
    else:
        print(f"💡 扫描完毕，共发现 {found_count} 处潜在风险。请重点检查上述位置。")

if __name__ == "__main__":
    # 获取当前目录作为扫描起点
    scan_project(os.getcwd())