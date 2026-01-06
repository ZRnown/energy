#!/usr/bin/env python3
"""
能量租赁机器人快速开始演示脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    print("🚀 能量租赁机器人 - 快速开始")
    print("=" * 40)

    # 检查Python版本
    print(f"📍 Python版本: {sys.version.split()[0]}")
    print(f"📍 当前目录: {os.getcwd()}")

    # 检查项目结构
    project_root = Path(__file__).parent
    bot_dir = project_root / "energy_rental_bot"

    if not bot_dir.exists():
        print("❌ 错误: 未找到 energy_rental_bot 目录")
        return

    print("✅ 项目结构检查通过")

    # 检查依赖
    try:
        import telegram
        print("✅ python-telegram-bot 已安装")
    except ImportError:
        print("⚠️  python-telegram-bot 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot"], check=True)
        print("✅ python-telegram-bot 安装完成")

    # 设置演示环境变量
    os.environ['TELEGRAM_BOT_TOKEN'] = 'demo_token_123'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['DB_NAME'] = 'energy_bot_demo'
    os.environ['DB_USER'] = 'demo_user'
    os.environ['DB_PASSWORD'] = 'demo_pass'

    print("\n🔧 已设置演示环境变量")

    # 运行测试
    print("\n🧪 运行配置测试...")
    result = subprocess.run([sys.executable, str(project_root / "run_bot.py"), "--test"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ 机器人配置测试通过！")
        print("\n🎉 恭喜！能量租赁机器人已准备就绪")
        print("\n📝 下一步:")
        print("1. 编辑 .env 文件，设置真实的配置")
        print("2. 运行: python run_bot.py")
        print("3. 在 Telegram 中与机器人交互")
    else:
        print("❌ 配置测试失败:")
        print(result.stderr)

if __name__ == "__main__":
    main()
