#!/usr/bin/env python3
"""
能量租赁机器人启动脚本

使用方法:
    python run_bot.py              # 启动机器人
    python run_bot.py --test       # 测试模式
    python run_bot.py --help       # 显示帮助

环境变量:
    TELEGRAM_BOT_TOKEN     - Telegram Bot Token (必需)
    DB_HOST               - 数据库主机
    DB_NAME               - 数据库名
    DB_USER               - 数据库用户
    DB_PASSWORD           - 数据库密码
    TELEGRAM_ADMIN_UID    - 管理员用户ID (可选)
"""
"""
能量租赁机器人启动脚本
"""

import sys
import os
import asyncio
import signal
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
PROJECT_DIR = Path(__file__).parent
BOT_DIR = PROJECT_DIR / "energy_rental_bot"
sys.path.insert(0, str(PROJECT_DIR))

from energy_rental_bot.bot.energy_bot import EnergyRentalBot
from energy_rental_bot.utils.energy_utils import EnergyUtils


def main(test_mode=False):
    """主函数"""
    # 设置日志
    EnergyUtils.setup_logging()

    # 强制设置日志级别，确保能看到错误
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)

    if test_mode:
        logger.info("启动能量租赁机器人 (测试模式)...")
    else:
        logger.info("启动能量租赁机器人...")

    # 创建机器人实例
    bot = EnergyRentalBot()

    try:
        if test_mode:
            # 初始化机器人进行测试
            asyncio.run(bot.initialize())
            logger.info("测试模式：机器人初始化成功")
            return

        # 修复：移除手动信号处理
        # application.run_polling() 会自动处理 SIGINT 和 SIGTERM

        # 直接启动机器人
        logger.info("机器人正在运行，按 Ctrl+C 停止...")
        bot.start()

    except KeyboardInterrupt:
        # 这里通常不会触发，因为 run_polling 捕获了它，但保留作为安全措施
        logger.info("收到键盘中断，正在停止...")
    except Exception as e:
        logger.error(f"机器人运行出错: {str(e)}")
        raise
    finally:
        logger.info("机器人已停止")


def check_environment():
    """检查环境配置"""
    # 加载.env文件
    load_dotenv()
    # 检查必要的环境变量
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ 缺少必要的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请检查 .env 文件或环境变量设置")
        print("参考 .env.example 文件")
        sys.exit(1)

    print("✅ 环境配置检查通过")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='能量租赁机器人')
    parser.add_argument('--test', action='store_true', help='测试模式，只检查配置不启动机器人')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    print("🔋 能量租赁机器人")
    print("=" * 30)

    if args.verbose:
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")

    # 检查环境
    check_environment()

    if args.test:
        print("🧪 运行测试模式...")
        try:
            main(test_mode=True)
            print("✅ 测试通过！机器人配置正确")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            sys.exit(1)
        sys.exit(0)

    # 运行机器人
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 机器人已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        sys.exit(1)
