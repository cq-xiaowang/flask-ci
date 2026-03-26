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
        # 切换到main分支再pull
        run_command("git checkout main", cwd=deploy_path)
        code, output = run_command("git pull origin main", cwd=deploy_path)

    return code == 0, output

# 构建环境（Docker/虚拟环境）
def build_environment(project_config):
    print("→ 构建运行环境...")
    deploy_path = project_config["deploy_path"]
    build_script = project_config.get("build_script", "")

    output = ""

    if project_config["use_docker"]:
        # 检查目录下是否有 docker-compose.yml
        docker_compose_file = os.path.join(deploy_path, "docker-compose.yml")
        if os.path.exists(docker_compose_file):
            print("→ 检测到 docker-compose.yml，执行Docker构建...")
            cmd = "docker-compose down && docker-compose up -d --build"
            code, build_output = run_command(cmd, cwd=deploy_path)
            output += f"Docker构建: {build_output}\n"
        else:
            print("→ 未检测到 docker-compose.yml，跳过Docker构建")

    # 执行构建脚本（如果存在）
    if build_script:
        script_path = os.path.join(deploy_path, build_script)
        if os.path.exists(script_path):
            print(f"→ 执行构建脚本: {build_script}")
            # 如果是 shell 脚本，给执行权限
            if script_path.endswith(".sh"):
                run_command(f"chmod +x {script_path}", cwd=deploy_path)
                code, build_output = run_command(f"bash {script_path}", cwd=deploy_path)
            else:
                code, build_output = run_command(f"python {script_path}", cwd=deploy_path)
            output += f"构建脚本: {build_output}\n"
        else:
            print(f"→ 构建脚本 {build_script} 不存在，跳过")

    return True, output

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