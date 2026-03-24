import os
from pathlib import Path

def generate_tree(dir_path, ignore_dirs, file_extensions, prefix=""):
    """
    递归生成纯文本的目录树字符串
    """
    tree_str = ""
    try:
        items = os.listdir(dir_path)
    except PermissionError:
        return tree_str

    # 过滤并排序文件夹和文件
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(dir_path, d)) and d not in ignore_dirs])
    files = sorted([f for f in items if os.path.isfile(os.path.join(dir_path, f)) and Path(f).suffix in file_extensions])

    entries = dirs + files
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{entry}\n"

        # 如果是文件夹，继续递归
        if entry in dirs:
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(os.path.join(dir_path, entry), ignore_dirs, file_extensions, prefix + extension)
            
    return tree_str

def export_project_to_markdown(project_dir, output_file, ignore_dirs=None, file_extensions=None):
    """
    将项目导出为包含目录树和代码块的 Markdown 文件。
    """
    if ignore_dirs is None:
        # 默认过滤掉常见的无关文件夹
        ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode', 'node_modules', '__MACOSX'}
    
    if file_extensions is None:
        file_extensions = {'.py'}

    project_path = Path(project_dir).resolve()

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# 项目: {project_path.name}\n\n")

        # --- 第一部分：生成并写入目录树概览 ---
        md_file.write("## 🗂️ 项目目录树\n\n```text\n")
        md_file.write(f"{project_path.name}/\n")
        tree_content = generate_tree(project_path, ignore_dirs, file_extensions)
        md_file.write(tree_content)
        md_file.write("```\n\n---\n\n")
        
        # --- 第二部分：遍历并写入代码内容 ---
        md_file.write("## 💻 代码详情\n\n")
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            dirs.sort()
            files.sort()

            current_path = Path(root)
            try:
                relative_path = current_path.relative_to(project_path)
            except ValueError:
                continue

            # 目录标题
            if relative_path.parts:
                depth = len(relative_path.parts)
                # 基础层级从 H3 开始，因为 H2 被用作大板块划分
                dir_heading = "#" * (depth + 2) 
                md_file.write(f"{dir_heading} 📁 {relative_path.name}\n\n")
            else:
                depth = 0

            # 文件标题与代码块
            for file in files:
                file_path = current_path / file
                if file_path.suffix in file_extensions:
                    file_heading = "#" * (depth + 3)
                    md_file.write(f"{file_heading} 📄 {file}\n\n")
                    
                    md_file.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            md_file.write(f.read())
                    except Exception as e:
                        md_file.write(f"# 读取文件失败: {e}\n")
                    
                    if not md_file.tell() == 0:
                        md_file.write("\n")
                    md_file.write("```\n\n")

if __name__ == "__main__":
    # 1. 获取当前脚本的绝对路径的父目录 (即 tests/ 目录)
    current_script_dir = Path(__file__).resolve().parent
    
    # 2. 定位到上一级目录 (即 项目根目录)
    PROJECT_DIRECTORY = current_script_dir.parent
    
    # 3. 设置输出文件路径 (这里将其保存在项目根目录下)
    OUTPUT_MARKDOWN_FILE = PROJECT_DIRECTORY / "project_code_context.md"
    
    print(f"开始整理目录: {PROJECT_DIRECTORY}")
    export_project_to_markdown(PROJECT_DIRECTORY, OUTPUT_MARKDOWN_FILE)
    print(f"✅ 整理完成！请查看文件: {OUTPUT_MARKDOWN_FILE}")