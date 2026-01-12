"""
能量租赁机器人模型类
"""

from .base_model import BaseModel
from energy_rental_bot.utils.energy_utils import EnergyUtils


class EnergyAiBishuModel(BaseModel):
    """能量AI笔数模型"""

    def __init__(self):
        super().__init__('energy_ai_bishu')

    def get_by_wallet_addr(self, wallet_addr):
        """根据钱包地址获取笔数套餐信息"""
        sql = "SELECT * FROM energy_ai_bishu WHERE wallet_addr = %s"
        result = self.db.query(sql, [wallet_addr])
        if result:
            return result[0]

        # 模拟数据 - 实际应该从数据库查询
        return {
            'rid': 1,
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'wallet_addr': wallet_addr,
            'bot_token': 'bot_token_here',
            'is_notice_admin': 'N',
            'is_notice': 'Y',
            'tg_admin_uid': 'admin123',
            'tg_notice_obj_send': 'group1,group2',
            'bot_username': 'energybot',
            'bot_admin_username': '@admin',
            'per_bishu_energy_quantity': 50000
        }

    def get_list_for_resource_check(self):
        """获取需要检查资源的笔数套餐列表"""
        sql = """
        SELECT * FROM energy_ai_bishu
        WHERE status = 0 AND is_open_bishu = 'Y' AND is_buy = 'N'
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'per_bishu_energy_quantity': 50000,
            'is_buy': 'N',
            'bot_rid': 1,
            'is_open_bishu': 'Y',
            'status': 0,
            'max_buy_quantity': 100,
            'total_buy_quantity': 0,
            'bot_token': 'bot_token_here'
        }]

    def get_pending_orders(self, order_type):
        """获取待处理的笔数套餐订单"""
        sql = """
        SELECT * FROM energy_ai_bishu
        WHERE status = 0 AND is_buy = 'Y' AND current_energy_quantity < per_bishu_energy_quantity
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'per_bishu_energy_quantity': 50000,
            'current_energy_quantity': 10000,
            'is_buy': 'Y',
            'bot_rid': 1,
            'status': 0,
            'max_buy_quantity': 100,
            'total_buy_quantity': 0,
            'poll_group': 'group1',
            'energy_platform_bot_rid': 1,
            'per_energy_day_bishu': 1,
            'bishu_recovery_type': 'auto',
            'bishu_daili_type': 'energy'
        }]

    def get_for_notification(self):
        """获取需要通知的笔数套餐记录"""
        sql = """
        SELECT * FROM energy_ai_bishu
        WHERE is_notice = 'Y'
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'per_bishu_energy_quantity': 50000,
            'bot_token': 'bot_token_here',
            'is_notice': 'Y',
            'is_notice_admin': 'N',
            'tg_admin_uid': 'admin123',
            'comments': '',
            'tg_notice_obj_send': 'group1,group2',
            'bot_username': 'energybot',
            'bot_admin_username': '@admin',
            'max_buy_quantity': 100,
            'total_buy_quantity': 10
        }]


class EnergyAiTrusteeshipModel(BaseModel):
    """能量AI托管模型"""

    def __init__(self):
        super().__init__('energy_ai_trusteeship')

    def get_by_wallet_addr(self, wallet_addr):
        """根据钱包地址获取托管信息"""
        sql = "SELECT * FROM energy_ai_trusteeship WHERE wallet_addr = %s"
        result = self.db.query(sql, [wallet_addr])
        if result:
            return result[0]

        # 模拟数据 - 实际应该从数据库查询
        return {
            'rid': 1,
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'wallet_addr': wallet_addr,
            'bot_token': 'bot_token_here',
            'is_notice_admin': 'N',
            'is_notice': 'Y',
            'tg_admin_uid': 'admin123',
            'tg_notice_obj_send': 'group1,group2',
            'bot_username': 'energybot',
            'bot_admin_username': '@admin',
            'per_buy_energy_quantity': 50000,
            'current_energy_quantity': 0,
            'total_buy_quantity': 0
        }

    def get_list_for_resource_check(self):
        """获取需要检查资源的托管列表"""
        sql = """
        SELECT * FROM energy_ai_trusteeship
        WHERE status = 0 AND is_open_ai_trusteeship = 'Y' AND is_buy = 'N'
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'min_energy_quantity': 50000,
            'is_buy': 'N',
            'bot_rid': 1,
            'is_open_ai_trusteeship': 'Y',
            'status': 0,
            'per_buy_energy_quantity': 50000,
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'bot_token': 'bot_token_here'
        }]

    def get_pending_orders(self, order_type):
        """获取待处理的AI订单"""
        sql = """
        SELECT * FROM energy_ai_trusteeship
        WHERE status = 0 AND is_buy = 'Y'
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'per_buy_energy_quantity': 50000,
            'trx_price_energy_32000': 50,
            'trx_price_energy_65000': 100,
            'per_energy_day': 1,
            'status': 0,
            'is_buy': 'Y',
            'bot_rid': 1,
            'total_buy_energy_quantity': 0,
            'total_used_trx': 0,
            'total_buy_quantity': 0,
            'is_notice_admin': 'N',
            'poll_group': 'group1',
            'energy_platform_bot_rid': 1,
            'max_buy_quantity': 100,
            'is_open_ai_trusteeship': 'Y'
        }]

    def update_resource(self, rid, data):
        """更新资源状态"""
        return self.update(rid, data)

    def get_for_notification(self):
        """获取需要通知的数据"""
        sql = """
        SELECT * FROM energy_ai_trusteeship
        WHERE is_notice = 'Y'
        """
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'tg_uid': 1234567890,  # 使用有效的Telegram chat_id (数字)，测试用
            'wallet_addr': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'per_buy_energy_quantity': 50000,
            'bot_token': 'bot_token_here',
            'is_notice': 'Y',
            'is_notice_admin': 'N',
            'tg_admin_uid': 'admin123',
            'comments': '',
            'tg_notice_obj_send': 'group1,group2',
            'bot_username': 'energybot',
            'bot_admin_username': '@admin'
        }]


class EnergyPlatformModel(BaseModel):
    """能量平台模型"""

    def __init__(self):
        super().__init__('energy_platform')

    def get_available_platforms(self, energy_amount, poll_group):
        """获取可用平台列表"""
        sql = """
        SELECT * FROM energy_platform
        WHERE status = 0 AND platform_balance >= %s
        ORDER BY seq_sn ASC
        """
        result = self.db.query(sql, [energy_amount])
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'platform_name': 1,  # nee.cc
            'platform_uid': 123456789,  # 使用有效的Telegram chat_id (数字)
            'platform_apikey': 'encrypted_key',
            'platform_balance': 1000000,
            'permission_id': 0,
            'seq_sn': 1
        }]


class EnergyPlatformBotModel(BaseModel):
    """能量平台机器人模型"""

    def __init__(self):
        super().__init__('energy_platform_bot')

    def get_list(self, status=0):
        """获取机器人列表"""
        sql = f"SELECT * FROM energy_platform_bot WHERE status = %s"
        result = self.db.query(sql, [status])
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'receive_wallet': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'status': 0,
            'get_tx_time': '2024-01-01 00:00:00'
        }]


class EnergyPlatformOrderModel(BaseModel):
    """能量平台订单模型"""

    def __init__(self):
        super().__init__('energy_platform_order')


class EnergyPlatformPackageModel(BaseModel):
    """能量平台套餐模型"""

    def __init__(self):
        super().__init__('energy_platform_package')

    def get_by_trx_price(self, bot_rid, trx_price):
        """根据TRX价格获取套餐"""
        sql = """
        SELECT * FROM energy_platform_package
        WHERE bot_rid = %s AND trx_price = %s AND status = 0
        """
        result = self.db.query(sql, [bot_rid, trx_price])
        if result:
            return result[0]

        # 模拟数据
        return {
            'rid': 1,
            'energy_amount': 50000,
            'energy_day': 1,
            'package_name': '50000能量1天'
        }


class EnergyWalletTradeListModel(BaseModel):
    """能量钱包交易列表模型"""

    def __init__(self):
        super().__init__('energy_wallet_trade_list')

    def get_pending_transactions(self, coin_name=None, wallet_addr=None):
        """获取待处理的交易"""
        conditions = ["process_status = 1"]
        params = []

        if coin_name:
            conditions.append("coin_name = %s")
            params.append(coin_name)

        if wallet_addr:
            conditions.append("transferto_address = %s")
            params.append(wallet_addr)

        sql = f"SELECT * FROM energy_wallet_trade_list WHERE {' AND '.join(conditions)}"
        result = self.db.query(sql, params)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'transferfrom_address': wallet_addr or 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'transferto_address': wallet_addr or 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'amount': 10.5,
            'coin_name': coin_name or 'trx',
            'tx_hash': 'hash123',
            'timestamp': EnergyUtils.thirteen_time(),
            'process_status': 1,
            'bot_rid': 1,
            'poll_group': 'group1',
            'platform_bot_rid': 1
        }]

    def get_tg_notifications(self, notify_type):
        """获取需要发送TG通知的记录"""
        status_map = {
            'self_order': "process_status = 9 AND tg_notice_status_receive = 'N'",
            'trusteeship': "process_status = 9 AND tg_notice_status_send = 'N'"
        }

        condition = status_map.get(notify_type, "process_status = 9")
        sql = f"SELECT * FROM energy_wallet_trade_list WHERE {condition}"
        result = self.db.query(sql)
        if result:
            return result

        # 模拟数据
        return [{
            'rid': 1,
            'tx_hash': 'hash123',
            'transferfrom_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'coin_name': 'trx',
            'amount': 10.5,
            'process_status': 9,
            'tg_notice_status_receive': 'N',
            'tg_notice_status_send': 'N',
            'tg_notice_obj_receive': 'group1,group2',
            'tg_notice_obj_send': 'group1,group2',
            'bot_token': 'bot_token_here',
            'receive_wallet': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
            'energy_amount': 50000,
            'package_name': '50000能量1天',
            'bot_username': 'energybot',
            'bot_admin_username': '@admin',
            'energy_platform_bot_rid': 1,
            'tg_uid': 123456789  # 添加缺失的tg_uid字段，使用有效的Telegram chat_id (数字)
        }]

    def get_by_tx_hash(self, hash_list):
        """检查hash是否存在"""
        if not hash_list:
            return []

        placeholders = ", ".join(["%s"] * len(hash_list))
        sql = f"SELECT tx_hash FROM energy_wallet_trade_list WHERE tx_hash IN ({placeholders})"
        result = self.db.query(sql, hash_list)
        return [row['tx_hash'] for row in result] if result else []
