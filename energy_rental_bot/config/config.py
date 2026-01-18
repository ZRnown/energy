"""
能量租赁机器人配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据库配置
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'energy_bot'),
    'username': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# TRON网络配置
TRON_CONFIG = {
    'api_keys': {
        'tronapikey': [
            os.getenv('TRON_API_KEY_1', 'key1'),
            os.getenv('TRON_API_KEY_2', 'key2'),
            os.getenv('TRON_API_KEY_3', 'key3')
        ],
        'gridapikey': [
            os.getenv('GRID_API_KEY_1', 'key4'),
            os.getenv('GRID_API_KEY_2', 'key5'),
            os.getenv('GRID_API_KEY_3', 'key6')
        ]
    },
    'networks': {
        'mainnet': 'https://api.trongrid.io',
        'testnet': 'https://api.shasta.trongrid.io'
    }
}

# Telegram配置
TELEGRAM_CONFIG = {
    'bots': [
        {
            'token': os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token'),
            'username': os.getenv('TELEGRAM_BOT_USERNAME', 'energybot'),
            'admin_username': os.getenv('TELEGRAM_ADMIN_USERNAME', '@admin'),
            'admin_uid': os.getenv('TELEGRAM_ADMIN_UID', '')  # 管理员用户ID
        }
    ],
    'webhook': {
        'enabled': False,  # 是否启用webhook模式
        'url': os.getenv('WEBHOOK_URL', ''),
        'port': int(os.getenv('WEBHOOK_PORT', 8443))
    }
}

# 任务配置
TASK_CONFIG = {
    'concurrency': {
        'max_workers': 5,
        'timeout': 30
    },
    'intervals': {
        'get_trx_trades': 60,      # 每分钟获取TRX交易
        'get_usdt_trades': 60,     # 每分钟获取USDT交易
        'handle_orders': 60,       # 每分钟处理订单
        'check_resources': 600,    # 每10分钟检查资源
        'handle_ai_orders': 600,   # 每10分钟处理AI订单
        'send_notifications': 60   # 每分钟发送通知
    }
}

# 平台配置示例
PLATFORM_CONFIG = {
    'nee_cc': {
        'name': 'nee.cc',
        'platform_id': 1,
        'api_url': 'https://api.tronqq.com/openapi/v2/order/submit'
    },
    'rent_energy': {
        'name': 'RentEnergysBot',
        'platform_id': 2,
        'api_url': 'https://api.wallet.buzz'
    },
    'self_stake': {
        'name': '自己质押',
        'platform_id': 3,
        'api_url': 'energy_stake_api_url'
    },
    'trongas': {
        'name': 'trongas.io',
        'platform_id': 4,
        'api_url': 'https://trongas.io/api/pay'
    }
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'file': '/tmp/energy_rental_bot.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# 监控配置
MONITOR_CONFIG = {
    'alerts': {
        'low_balance_threshold': 1000,  # 余额不足告警阈值
        'high_error_rate_threshold': 0.1,  # 错误率告警阈值
        'max_retry_attempts': 3
    },
    'metrics': {
        'enable_prometheus': False,
        'prometheus_port': 8000
    }
}

# 能量闪租配置
ENERGY_RENT_CONFIG = {
    # 能量价格配置 (TRX -> 能量)
    'prices': {
        'with_u': {'trx': 3.0, 'energy': 65000},    # 对方有U的情况
        'without_u': {'trx': 6.0, 'energy': 131000}  # 对方无U的情况
    },

    # 限制配置
    'max_single_trx': 50.0,        # 最高单笔TRX
    'max_energy': 1300000,         # 对应最大能量
    'rent_duration_hours': 1,      # 租赁时长（小时）

    # 接收地址 - 从环境变量读取
    'receive_wallet': os.getenv('ENERGY_RENT_WALLET', 'TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh'),

    # 盈利配置
    'profit_margin': 0.1,          # 利润率 10%
    'platform_fee': 0.05           # 平台手续费 5%
}

# 笔数套餐配置
BISHA_CONFIG = {
    # 笔数套餐价格配置 (TRX/笔)
    'price_per_bishu': 6.0,

    # 可购买的笔数选项
    'available_packages': [15, 20, 30, 50, 100, 200, 300, 500],

    # 能量配置
    'energy_per_bishu': 131000,  # 每笔对应的能量数量
    'energy_recovery_time': 5,   # 能量恢复时间（秒）

    # 自动赠送配置
    'auto_gift_trx_threshold': 0.35,  # TRX余额阈值
    'auto_gift_bandwidth_threshold': 345,  # 带宽阈值
    'auto_gift_amount': 0.35,  # 自动赠送TRX数量

    # 扣费规则
    'deduct_after_hours': 24,   # 多长时间未使用扣减1笔
    'pause_after_hours': 72,    # 多长时间未使用自动暂停

    # 接收地址
    'receive_wallet': os.getenv('BISHA_WALLET', 'TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh'),

    # 客服配置
    'customer_service': {
        'admin_username': os.getenv('TELEGRAM_ADMIN_USERNAME', '@admin'),
        'work_hours': '每天 9:00-18:00',
        'response_time': '24小时内'
    }
}
