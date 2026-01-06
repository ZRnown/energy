"""
处理AI能量订单任务
"""

import json
import hashlib
import time
from energy_rental_bot.models.energy_models import (
    EnergyAiTrusteeshipModel,
    EnergyAiBishuModel,
    EnergyPlatformModel,
    EnergyPlatformOrderModel
)
from energy_rental_bot.utils.energy_utils import EnergyUtils, RsaServices, Concurrent


class HandleAiEnergyOrderTask:
    """处理AI能量订单任务"""

    def execute(self):
        """执行任务"""
        # 智能托管
        self.handle_trusteeship_orders()
        # 笔数套餐
        self.handle_bishu_orders()

    def handle_trusteeship_orders(self):
        """处理智能托管订单"""
        model = EnergyAiTrusteeshipModel()
        orders = model.get_pending_orders('trusteeship')

        for order in orders:
            # 检查购买限制
            if order['max_buy_quantity'] > 0 and order['max_buy_quantity'] <= order['total_buy_quantity']:
                continue

            # 检查用户余额
            if not self.check_user_balance(order):
                continue

            # 获取可用平台
            platforms = self.get_available_platforms(order['poll_group'], order['per_buy_energy_quantity'])

            # 尝试下单
            self.process_order(order, platforms, 'trusteeship')

    def handle_bishu_orders(self):
        """处理笔数套餐订单"""
        model = EnergyAiBishuModel()
        orders = model.get_pending_orders('bishu')

        for order in orders:
            # 检查购买限制
            if order['max_buy_quantity'] > 0 and order['max_buy_quantity'] <= order['total_buy_quantity']:
                continue

            # 检查能量余额
            if not self.check_energy_balance(order):
                continue

            # 获取可用平台
            platforms = self.get_available_platforms(order['poll_group'], order['per_bishu_energy_quantity'])

            # 尝试下单
            self.process_order(order, platforms, 'bishu')

    def check_user_balance(self, order):
        """检查用户余额"""
        # 检查用户TRX余额是否足够
        price = order['trx_price_energy_32000'] if order['per_buy_energy_quantity'] == 32000 else order['trx_price_energy_65000']

        # 模拟检查用户余额
        # 这里应该调用具体的余额检查API
        return True  # 假设余额足够

    def check_energy_balance(self, order):
        """检查能量余额"""
        # 检查钱包当前能量是否低于阈值
        return order['current_energy_quantity'] < order['per_bishu_energy_quantity']

    def get_available_platforms(self, poll_group, energy_amount):
        """获取可用平台"""
        model = EnergyPlatformModel()
        return model.get_available_platforms(energy_amount, poll_group)

    def process_order(self, order, platforms, order_type):
        """处理订单"""
        rsa = RsaServices()

        for platform in platforms:
            private_key = rsa.private_decrypt(platform['platform_apikey'])

            if not private_key:
                self.update_order_comments(order['rid'], order_type, "平台私钥为空")
                continue

            # 标记为下单中
            self.update_order_status(order['rid'], order_type, 'B')

            # 调用相应平台的API
            address = order['wallet_addr']
            energy_amount = order['per_buy_energy_quantity'] if order_type == 'trusteeship' else order['per_bishu_energy_quantity']
            energy_day = order.get('per_energy_day', 1)

            result = self.call_platform_api(platform, address, energy_amount, energy_day, private_key)

            if result['success']:
                # 创建平台订单
                self.create_platform_order(platform, order, result, order_type)

                # 更新统计
                self.update_order_statistics(order, order_type)

                # 发送通知
                self.send_order_notification(order, order_type, 'success')

                break
            else:
                self.update_order_comments(order['rid'], order_type, result['message'])

    def call_platform_api(self, platform, address, energy_amount, energy_day, private_key):
        """调用平台API"""
        # 这里应该根据平台类型调用不同的API
        # 暂时使用相同的下单逻辑
        return self.place_energy_order(platform, address, energy_amount, energy_day)

    def create_platform_order(self, platform, order, result, order_type):
        """创建平台订单"""
        order_data = {
            'energy_platform_rid': platform['rid'],
            'energy_platform_bot_rid': order['energy_platform_bot_rid'],
            'platform_name': platform['platform_name'],
            'platform_uid': platform['platform_uid'],
            'receive_address': order['wallet_addr'],
            'platform_order_id': result.get('order_no', ''),
            'energy_amount': order['per_buy_energy_quantity'] if order_type == 'trusteeship' else order['per_bishu_energy_quantity'],
            'energy_day': order.get('per_energy_day', 1),
            'energy_time': EnergyUtils.now_date(),
            'source_type': 3,  # AI自动下单
            'recovery_status': 2 if platform['platform_name'] == 3 else 1,
            'use_trx': result.get('use_trx', 0)
        }

        order_model = EnergyPlatformOrderModel()
        return order_model.insert(order_data)

    def update_order_statistics(self, order, order_type):
        """更新订单统计"""
        update_data = {
            'is_buy': 'N',  # 重置购买状态
            'total_buy_energy_quantity': order['total_buy_energy_quantity'] + (
                order['per_buy_energy_quantity'] if order_type == 'trusteeship' else order['per_bishu_energy_quantity']
            ),
            'total_buy_quantity': order['total_buy_quantity'] + 1,
            'is_notice': 'Y',
            'last_buy_time': EnergyUtils.now_date()
        }

        if order_type == 'trusteeship':
            model = EnergyAiTrusteeshipModel()
        else:
            model = EnergyAiBishuModel()

        model.update(order['rid'], update_data)

    def update_order_status(self, rid, order_type, status):
        """更新订单状态"""
        update_data = {'is_buy': status}

        if order_type == 'trusteeship':
            model = EnergyAiTrusteeshipModel()
        else:
            model = EnergyAiBishuModel()

        model.update(rid, update_data)

    def update_order_comments(self, rid, order_type, comments):
        """更新订单备注"""
        update_data = {'comments': f"{EnergyUtils.now_date()} {comments}"}

        if order_type == 'trusteeship':
            model = EnergyAiTrusteeshipModel()
        else:
            model = EnergyAiBishuModel()

        model.update(rid, update_data)

    def send_order_notification(self, order, order_type, status):
        """发送订单通知"""
        # 发送Telegram通知
        notify_task = SendEnergyTgMessageTask()
        notify_task.send_order_notification(order, order_type, status)

    def place_energy_order(self, platform, address, energy_amount, energy_day):
        """调用相应平台的API下单"""
        # 这里使用与HandleEnergyOrderTask相同的下单逻辑
        # 实际应该根据平台类型调用不同的API

        platform_name = platform['platform_name']

        if platform_name == 1:  # nee.cc
            return self.place_nee_order(platform, address, energy_amount, energy_day)
        elif platform_name == 2:  # RentEnergysBot
            return self.place_rent_energy_order(platform, address, energy_amount, energy_day)
        elif platform_name == 3:  # 自己质押
            return self.place_self_stake_order(platform, address, energy_amount)
        elif platform_name == 4:  # trongas.io
            return self.place_trongas_order(platform, address, energy_amount, energy_day)
        else:
            return {'success': False, 'message': '不支持的平台类型'}

    # 各个平台的下单实现与HandleEnergyOrderTask中的相同
    def place_nee_order(self, platform, address, energy_amount, energy_day):
        """nee.cc平台下单"""
        param = {
            "uid": platform['platform_uid'],
            "resource_type": "0",
            "receive_address": address,
            "amount": str(energy_amount),
            "freeze_day": str(energy_day),
            "time": str(int(time.time()))
        }

        # 添加签名
        sorted_param = sorted(param.items())
        sign_str = ''.join([f"{k}{v}" for k, v in sorted_param if k not in ["sign", "sign_type"] and v != ''])
        param['sign'] = hashlib.md5(sign_str.encode()).hexdigest()

        url = 'https://api.tronqq.com/openapi/v2/order/submit'
        response = EnergyUtils.send_http_request(url, json.dumps(param), {'Content-Type': 'application/json'})

        if response:
            try:
                result = json.loads(response)
                if result.get('status') == 200:
                    return {'success': True, 'order_no': result['data']['order_no']}
                else:
                    return {'success': False, 'message': result.get('msg', '下单失败')}
            except json.JSONDecodeError:
                return {'success': False, 'message': 'API响应解析失败'}
        else:
            return {'success': False, 'message': 'API请求失败'}

    def place_rent_energy_order(self, platform, address, energy_amount, energy_day):
        """RentEnergysBot平台下单"""
        energy_type = 'day' if energy_day == 1 else ('3day' if energy_day == 3 else 'hour')
        energy_amount = max(energy_amount, 33000)

        url = (
            f"https://api.wallet.buzz?api=getEnergy&apikey={platform['platform_apikey']}"
            f"&address={address}&amount={energy_amount}&type={energy_type}"
        )

        response = EnergyUtils.send_http_request(url)

        if response:
            try:
                result = json.loads(response)
                if result.get('status') == 'success':
                    return {'success': True, 'txid': result['txid']}
                else:
                    return {'success': False, 'message': '下单失败'}
            except json.JSONDecodeError:
                return {'success': False, 'message': 'API响应解析失败'}
        else:
            return {'success': False, 'message': 'API请求失败'}

    def place_self_stake_order(self, platform, address, energy_amount):
        """自己质押平台下单"""
        params = {
            'pri': platform['platform_apikey'],
            'fromaddress': platform['platform_uid'],
            'receiveaddress': address,
            'resourcename': 'ENERGY',
            'resourceamount': energy_amount,
            'resourcetype': 1,
            'permissionid': platform['permission_id']
        }

        response = EnergyUtils.send_http_request('energy_stake_api_url', params)

        if response:
            try:
                result = json.loads(response)
                if result.get('code') == 200:
                    return {
                        'success': True,
                        'txid': result['data']['txid'],
                        'use_trx': result['data']['use_trx']
                    }
                else:
                    return {'success': False, 'message': '质押失败'}
            except json.JSONDecodeError:
                return {'success': False, 'message': 'API响应解析失败'}
        else:
            return {'success': False, 'message': 'API请求失败'}

    def place_trongas_order(self, platform, address, energy_amount, energy_day):
        """trongas.io平台下单"""
        rent_time = energy_day if energy_day == 1 else (72 if energy_day == 3 else 1)

        param = {
            "username": platform['platform_uid'],
            "password": platform['platform_apikey'],
            "resType": "ENERGY",
            "payNums": energy_amount,
            "rentTime": rent_time,
            "resLock": 0,
            "receiveAddress": address
        }

        url = 'https://trongas.io/api/pay'
        response = EnergyUtils.send_http_request(url, param)

        if response:
            try:
                result = json.loads(response)
                if result.get('code') == 10000:
                    return {
                        'success': True,
                        'order_id': result['data']['orderId'],
                        'order_money': result['data']['orderMoney']
                    }
                else:
                    return {'success': False, 'message': '下单失败'}
            except json.JSONDecodeError:
                return {'success': False, 'message': 'API响应解析失败'}
        else:
            return {'success': False, 'message': 'API请求失败'}


# 导入这里是为了避免循环导入
from energy_rental_bot.tasks.send_energy_tg_message_task import SendEnergyTgMessageTask
