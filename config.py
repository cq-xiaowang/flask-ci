# CI服务配置
CI_HOST = "0.0.0.0"
CI_PORT = 5000
CI_DEBUG = False

# 项目配置（可添加多个项目）
PROJECTS = {
    "journey-blog-vue": {
        "git_url": "https://gitee.com/yourname/your-project.git",  # 你的代码仓库
        "branch": "main",  # 监听分支
        "deploy_path": "/usr/local/share/ci/journey-blog-vue",  # 代码存放路径
        "build_script": "./build.sh",  # 构建脚本
        "use_docker": True  # 是否使用Docker构建环境
    }
}

# WebHook密钥（安全校验）
WEBHOOK_SECRET = "ours-flask-ci-secret-Lab123!@#"