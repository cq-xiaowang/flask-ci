import os
import subprocess
import threading
from datetime import datetime

# 执行系统命令（带日志输出）
def run_command(cmd, cwd=None, timeout=300):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, str(e)

# 拉取最新代码
def git_pull(project_config):
    print("→ 拉取最新代码...")
    deploy_path = project_config["deploy_path"]

    # 目录不存在则克隆
    if not os.path.exists(deploy_path):
        os.makedirs(deploy_path, exist_ok=True)
        code, output = run_command(f"git clone {project_config['git_url']} .", cwd=deploy_path)
    else:
        code, output = run_command("git pull origin main", cwd=deploy_path)

    return code == 0, output

# 构建环境（Docker/虚拟环境）
def build_environment(project_config):
    print("→ 构建运行环境...")
    deploy_path = project_config["deploy_path"]

    if project_config["use_docker"]:
        # Docker构建（推荐：环境完全隔离）
        cmd = "docker-compose down && docker-compose up -d --build"
    else:
        # Python虚拟环境（无Docker时使用）
        cmd = """
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        """

    code, output = run_command(cmd, cwd=deploy_path)
    return code == 0, output

# 写入构建日志
def write_log(project, status, output):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/{project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"项目：{project}\n状态：{status}\n时间：{datetime.now()}\n\n输出：\n{output}")

# 主构建流程（异步执行）
def start_build(project_name):
    from config import PROJECTS
    if project_name not in PROJECTS:
        return False, "项目不存在"

    project = PROJECTS[project_name]
    log_output = ""

    # 1. 拉取代码
    pull_ok, pull_log = git_pull(project)
    log_output += pull_log + "\n"
    if not pull_ok:
        write_log(project_name, "拉取代码失败", log_output)
        return False, log_output

    # 2. 构建环境
    build_ok, build_log = build_environment(project)
    log_output += build_log + "\n"

    # 3. 记录结果
    status = "构建成功" if build_ok else "构建失败"
    write_log(project_name, status, log_output)
    return build_ok, log_output

# 异步构建（不阻塞WebHook）
def async_build(project_name):
    thread = threading.Thread(target=start_build, args=(project_name,))
    thread.start()