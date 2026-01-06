"""
能量租赁机器人控制器类
"""

import json
from urllib.parse import quote
from energy_rental_bot.models.energy_models import EnergyAiBishuModel
from energy_rental_bot.utils.energy_utils import EnergyUtils


class TrongasIoController:
    """TrongasIo控制器 - 处理笔数能量回调通知"""

    def notice(self, request):
        """trongas笔数回调通知"""
        receive_address = request.get('receiveAddress', '')
        residue = request.get('residue', '')

        if receive_address:
            # 查地址通知
            bishu = self.get_energy_ai_bishu_by_wallet(receive_address)
            if bishu and bishu.get('tg_uid') and bishu['tg_uid']:
                # 通知用户
                self.notify_user_energy_success(bishu, receive_address, residue)

            # 通知到群
            if bishu.get('tg_notice_obj_send') and bishu['tg_notice_obj_send']:
                self.notify_group_energy_success(bishu, receive_address)

        return {'code': 200, 'msg': 'success'}

    def get_energy_ai_bishu_by_wallet(self, wallet_addr):
        """根据钱包地址获取笔数套餐信息"""
        model = EnergyAiBishuModel()
        return model.get_by_wallet_addr(wallet_addr)

    def notify_user_energy_success(self, bishu, receive_address, residue):
        """通知用户能量购买成功"""
        keyboard = {
            'inline_keyboard': [
                [
                    {'text': '能量闪租', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': '笔数套餐', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': '智能托管', 'url': f'https://t.me/{bishu["bot_username"]}'}
                ],
                [
                    {'text': '联系客服', 'url': f'https://t.me/{bishu["bot_admin_username"][1:]}'},
                    {'text': 'TRX闪兑', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': 'TRX预支', 'url': f'https://t.me/{bishu["bot_admin_username"][1:]}'}
                ]
            ]
        }

        encoded_keyboard = json.dumps(keyboard)

        reply_text_uid = (
            "🖌<b>新的笔数能量订单成功</b> \n"
            "➖➖➖➖➖➖➖➖\n"
            "<b>下单模式</b>：笔数套餐\n"
            f"<b>能量数量</b>：{bishu['per_bishu_energy_quantity']} \n"
            f"<b>能量地址</b>：{EnergyUtils.format_address(receive_address)}\n\n"
            "<b>能量已经到账！请在时间范围内使用！</b>\n"
            "发送 /buyenergy 继续购买能量！\n\n"
            f"⚠️<u>预计剩余：</u>{residue}\n"
            "➖➖➖➖➖➖➖➖"
        )

        send_message_url = (
            f"https://api.telegram.org/bot{bishu['bot_token']}/sendMessage"
            f"?chat_id={bishu['tg_uid']}&text={quote(reply_text_uid)}&parse_mode=HTML&reply_markup={quote(encoded_keyboard)}"
        )

        # 发送HTTP请求
        EnergyUtils.send_http_request(send_message_url)

    def notify_group_energy_success(self, bishu, receive_address):
        """通知群组能量购买成功"""
        keyboard = {
            'inline_keyboard': [
                [
                    {'text': '能量闪租', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': '笔数套餐', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': '智能托管', 'url': f'https://t.me/{bishu["bot_username"]}'}
                ],
                [
                    {'text': '联系客服', 'url': f'https://t.me/{bishu["bot_admin_username"][1:]}'},
                    {'text': 'TRX闪兑', 'url': f'https://t.me/{bishu["bot_username"]}'},
                    {'text': 'TRX预支', 'url': f'https://t.me/{bishu["bot_admin_username"][1:]}'}
                ]
            ]
        }

        encoded_keyboard = json.dumps(keyboard)

        reply_text = (
            "🖌<b>新的笔数能量订单成功</b> \n"
            "➖➖➖➖➖➖➖➖\n"
            "<b>下单模式</b>：笔数套餐\n"
            f"<b>能量数量</b>：{bishu['per_bishu_energy_quantity']} \n"
            f"<b>能量地址</b>：{EnergyUtils.format_address(receive_address)}\n\n"
            "<b>能量已经到账！请在时间范围内使用！</b>\n"
            "发送 /buyenergy 继续购买能量！\n"
            "➖➖➖➖➖➖➖➖"
        )

        send_list = bishu['tg_notice_obj_send'].split(',')

        for group_id in send_list:
            send_message_url = (
                f"https://api.telegram.org/bot{bishu['bot_token']}/sendMessage"
                f"?chat_id={group_id.strip()}&text={quote(reply_text)}&parse_mode=HTML&reply_markup={quote(encoded_keyboard)}"
            )

            EnergyUtils.send_http_request(send_message_url)
