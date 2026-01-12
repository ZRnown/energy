"""
发送能量TG消息任务
"""

import json
import logging
from urllib.parse import quote
from energy_rental_bot.models.energy_models import (
    EnergyWalletTradeListModel,
    EnergyAiTrusteeshipModel,
    EnergyAiBishuModel
)
from energy_rental_bot.utils.energy_utils import EnergyUtils
from energy_rental_bot.config.config import TELEGRAM_CONFIG


class SendEnergyTgMessageTask:
    """发送能量TG消息任务"""

    def __init__(self):
        # 修复：初始化 logger
        self.logger = logging.getLogger(__name__)

    def execute(self):
        """执行任务"""
        try:
            # 自助下单成功通知
            self.send_self_order_notifications()
            # 智能托管通知 - 已移除
            # self.send_trusteeship_notifications()
            # 笔数套餐通知
            self.send_bishu_notifications()
        except Exception as e:
            self.logger.error(f"发送消息任务执行异常: {str(e)}")

    def send_order_notification(self, order, order_type, status):
        """发送订单状态通知"""
        try:
            message = self.build_order_message(order, order_type, status)
            keyboard = self.build_keyboard(order)
            self.send_to_telegram(order['bot_token'], order['tg_uid'], message, keyboard)
        except Exception as e:
            self.logger.error(f"发送订单通知异常: {str(e)}")

    def send_self_order_notifications(self):
        """发送自助下单通知"""
        model = EnergyWalletTradeListModel()
        notifications = model.get_tg_notifications('self_order')

        for item in notifications:
            self.send_tg_message(item, 'self_order')
            self.update_notification_status(item['rid'], 'receive')
            self.update_notification_status(item['rid'], 'send')

    def send_trusteeship_notifications(self):
        """发送智能托管通知 - 已禁用"""
        # 智能托管功能已移除，不再发送通知
        pass

    def send_bishu_notifications(self):
        """发送笔数套餐通知"""
        model = EnergyAiBishuModel()
        notifications = model.get_for_notification()

        for item in notifications:
            self.send_tg_message(item, 'bishu')
            self.update_bishu_notification_status(item['rid'])

    def send_tg_message(self, item, message_type):
        """发送TG消息"""
        if not item:
            self.logger.error("发送TG消息失败：item为空")
            return

        message = self.build_message(item, message_type)
        keyboard = self.build_keyboard(item)

        # 发送到Telegram
        chat_id = item.get('chat_id') or item.get('tg_uid')

        # 使用配置文件中的真实bot_token，而不是数据库中的模拟数据
        bot_token = TELEGRAM_CONFIG['bots'][0]['token'] if TELEGRAM_CONFIG['bots'] else None

        if not chat_id or not bot_token:
            self.logger.error(f"发送TG消息失败：缺少必要字段 chat_id={chat_id}, bot_token={'***' if bot_token else None}")
            return

        self.send_to_telegram(bot_token, chat_id, message, keyboard)

    def build_message(self, item, message_type):
        """构建消息内容"""
        if not item:
            return "⚠️ 消息数据异常"

        if message_type == 'self_order':
            return (
                "🔋<b>新的能量订单成功</b> \n"
                "➖➖➖➖➖➖➖➖\n"
                "<b>下单模式</b>：自助下单\n"
                f"<b>能量数量</b>：{item.get('energy_amount', '未知')}\n"
                f"<b>能量地址</b>：{EnergyUtils.format_address(item.get('wallet_addr', '未知'))}\n\n"
                "<b>能量已经到账！请在时间范围内使用！</b>\n"
                "发送 /buyenergy 继续购买能量！\n"
                "➖➖➖➖➖➖➖➖"
            )
        elif message_type == 'trusteeship':
            return (
                "🔋<b>新的能量订单成功</b> \n"
                "<b>下单模式</b>：智能托管\n"
                f"<b>能量数量</b>：{item.get('per_buy_energy_quantity', '未知')}\n"
                f"<b>能量地址</b>：{EnergyUtils.format_address(item.get('wallet_addr', '未知'))}\n\n"
                "<b>能量已经到账！请在时间范围内使用！</b>\n"
                "⚠️<u>预计剩余：</u>计算剩余次数\n"
                "➖➖➖➖➖➖➖➖"
            )
        elif message_type == 'bishu':
            return (
                "🖌<b>新的笔数能量订单成功</b> \n"
                "<b>下单模式</b>：笔数套餐\n"
                f"<b>能量数量</b>：{item.get('per_bishu_energy_quantity', '未知')}\n"
                f"<b>能量地址</b>：{EnergyUtils.format_address(item.get('wallet_addr', '未知'))}\n\n"
                "<b>能量已经到账！请在时间范围内使用！</b>\n"
                "⚠️<u>预计剩余：</u>计算剩余次数\n"
                "➖➖➖➖➖➖➖➖"
            )
        else:
            return ''

    def build_order_message(self, order, order_type, status):
        """构建订单消息"""
        if status == 'success':
            return (
                "✅<b>AI能量订单成功</b> \n"
                f"<b>下单模式</b>：{'智能托管' if order_type == 'trusteeship' else '笔数套餐'}\n"
                f"<b>能量地址</b>：{EnergyUtils.format_address(order['wallet_addr'])}\n\n"
                "能量已自动补充！"
            )
        else:
            return (
                "❌<b>AI能量订单失败</b> \n"
                f"<b>下单模式</b>：{'智能托管' if order_type == 'trusteeship' else '笔数套餐'}\n"
                f"<b>失败原因</b>：{order.get('comments', '未知错误')}"
            )

    def build_keyboard(self, item):
        """构建键盘"""
        if not item:
            return None

        bot_username = item.get("bot_username", "energybot")
        admin_username = item.get("bot_admin_username", "@admin")

        # 修复 admin_username 可能为 None 的情况
        if not admin_username:
             admin_username = "@admin"

        admin_link = admin_username[1:] if admin_username.startswith("@") else admin_username

        return {
            'inline_keyboard': [
                [
                    {'text': '能量闪租', 'url': f'https://t.me/{bot_username}'},
                    {'text': '笔数套餐', 'url': f'https://t.me/{bot_username}'}
                ],
                [
                    {'text': '联系客服', 'url': f'https://t.me/{admin_link}'},
                    {'text': 'TRX预支', 'url': f'https://t.me/{admin_link}'}
                ]
            ]
        }

    def send_to_telegram(self, bot_token, chat_id, message, keyboard):
        """发送消息到Telegram"""
        try:
            # 检查是否为测试模式
            is_test_mode = (
                'demo' in str(bot_token).lower() or
                'test' in str(bot_token).lower() or
                str(bot_token) == 'your_bot_token' or
                str(chat_id) in ['123456789', '1234567890'] or  # 检测模拟数据
                'TR7NHqje' in str(message)  # 检测模拟钱包地址
            )

            if is_test_mode:
                self.logger.info(f"[测试模式] 模拟发送Telegram消息到 chat_id={chat_id}")
                self.logger.info(f"[测试模式] 消息内容: {message[:100]}...")
                return

            url = (
                f"https://api.telegram.org/bot{bot_token}/sendMessage"
                f"?chat_id={chat_id}&text={quote(message)}&parse_mode=HTML&reply_markup={quote(json.dumps(keyboard))}"
            )
            # 使用 GET 请求通常更稳定用于简单发送，或者确保 POST 数据正确
            EnergyUtils.send_http_request(url)
        except Exception as e:
            self.logger.error(f"HTTP请求发送失败: {str(e)}")

    def update_notification_status(self, rid, status_type):
        """更新通知状态"""
        model = EnergyWalletTradeListModel()
        model.update(rid, {f'tg_notice_status_{status_type}': 'Y'})

    def update_trusteeship_notification_status(self, rid):
        """更新智能托管通知状态"""
        model = EnergyAiTrusteeshipModel()
        model.update(rid, {'is_notice': 'N', 'is_notice_admin': 'N'})

    def update_bishu_notification_status(self, rid):
        """更新笔数套餐通知状态"""
        model = EnergyAiBishuModel()
        model.update(rid, {'is_notice': 'N', 'is_notice_admin': 'N'})
