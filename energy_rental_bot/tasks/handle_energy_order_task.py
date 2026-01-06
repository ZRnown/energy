"""
处理能量订单任务
"""

import json
import hashlib
import time
from energy_rental_bot.models.energy_models import (
    EnergyWalletTradeListModel,
    EnergyPlatformModel,
    EnergyPlatformPackageModel,
    EnergyAiBishuModel,
    EnergyPlatformOrderModel
)
from energy_rental_bot.services.energy_services import EnergyWalletServices
from energy_rental_bot.utils.energy_utils import EnergyUtils


class HandleEnergyOrderTask:
    """处理能量订单任务"""

    def execute(self):
        """执行任务"""
        try:
            # TRX闪租能量
            self.handle_trx_energy_orders()
            # USDT笔数套餐
            self.handle_usdt_energy_orders()
        except Exception as e:
            EnergyUtils.log('HANDLE_ENERGY_ORDER', f'任务执行报错：{str(e)}')

    def handle_trx_energy_orders(self):
        """处理TRX能量订单"""
        wallet_service = EnergyWalletServices()
        wallet_list = wallet_service.get_id_list(2)

        if wallet_list:
            current_time = EnergyUtils.now_date()
            for wallet_addr, wallet_info in wallet_list.items():
                platform_bot_rid = wallet_info['rid']

                # 获取待处理的TRX交易
                pending_transactions = self.get_pending_trx_transactions(wallet_addr)

                for transaction in pending_transactions:
                    self.process_trx_transaction(transaction, platform_bot_rid, current_time)

    def handle_usdt_energy_orders(self):
        """处理USDT笔数套餐订单"""
        wallet_service = EnergyWalletServices()
        wallet_list = wallet_service.get_id_list(2)

        if wallet_list:
            current_time = EnergyUtils.now_date()
            for wallet_addr, wallet_info in wallet_list.items():
                bot_rid = wallet_info['rid']

                # 获取待处理的USDT交易
                pending_transactions = self.get_pending_usdt_transactions(wallet_addr)

                for transaction in pending_transactions:
                    self.process_usdt_transaction(transaction, bot_rid, current_time)

    def get_pending_trx_transactions(self, wallet_addr):
        """获取待处理的TRX交易"""
        model = EnergyWalletTradeListModel()
        return model.get_pending_transactions('trx', wallet_addr)

    def get_pending_usdt_transactions(self, wallet_addr):
        """获取待处理的USDT交易"""
        model = EnergyWalletTradeListModel()
        return model.get_pending_transactions('usdt', wallet_addr)

    def process_trx_transaction(self, transaction, platform_bot_rid, current_time):
        """处理TRX交易"""
        # 匹配金额对应的套餐
        package_model = EnergyPlatformPackageModel()
        package = package_model.get_by_trx_price(transaction['bot_rid'], transaction['amount'])

        if not package:
            self.update_transaction_status(transaction['rid'], 7, '金额无对应套餐', current_time)
            return

        energy_amount = package['energy_amount']

        # 轮询获取可用平台
        platform_model = EnergyPlatformModel()
        available_platforms = platform_model.get_available_platforms(energy_amount, transaction['poll_group'])

        if not available_platforms:
            self.update_transaction_status(transaction['rid'], 4, '机器人无可用能量平台', current_time)
            return

        # 尝试下单
        for platform in available_platforms:
            result = self.place_energy_order(platform, transaction['transferfrom_address'], energy_amount, package['energy_day'])

            if result['success']:
                self.create_platform_order(platform, transaction, energy_amount, package, current_time)
                self.update_transaction_status(transaction['rid'], 9, 'SUCCESS', current_time, platform['rid'], package['rid'])
                break

    def process_usdt_transaction(self, transaction, bot_rid, current_time):
        """处理USDT交易"""
        # 查询笔数套餐钱包是否存在
        bishu_model = EnergyAiBishuModel()
        bishu_wallet = bishu_model.get_by_wallet_addr(transaction['transferfrom_address'])

        if bishu_wallet and 'total_buy_usdt' in bishu_wallet:
            # 更新购买统计
            update_data = {
                'total_buy_usdt': bishu_wallet.get('total_buy_usdt', 0) + transaction['amount'],
                'max_buy_quantity': bishu_wallet.get('max_buy_quantity', 0) + int(transaction['amount'] / transaction.get('per_bishu_usdt_price', 1))
            }
            bishu_model.update(bishu_wallet['rid'], update_data)
        else:
            # 创建新的笔数套餐钱包
            insert_data = {
                'bot_rid': bot_rid,
                'wallet_addr': transaction['transferfrom_address'],
                'status': 0,
                'total_buy_usdt': transaction['amount'],
                'max_buy_quantity': int(transaction['amount'] / transaction.get('per_bishu_usdt_price', 1)),
                'create_time': current_time
            }
            bishu_model.insert(insert_data)

        self.update_transaction_status(transaction['rid'], 9, '笔数套餐购买成功', current_time)

    def place_energy_order(self, platform, address, energy_amount, energy_day):
        """调用相应平台的API下单"""
        # 根据平台类型调用不同的API
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

    def place_nee_order(self, platform, address, energy_amount, energy_day):
        """调用nee.cc API"""
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
        """调用RentEnergysBot API"""
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
        """自己质押代理"""
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
        """调用trongas.io API"""
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

    def create_platform_order(self, platform, transaction, energy_amount, package, current_time):
        """创建平台订单"""
        order_data = {
            'energy_platform_rid': platform['rid'],
            'energy_platform_bot_rid': transaction['platform_bot_rid'],
            'platform_name': platform['platform_name'],
            'platform_uid': platform['platform_uid'],
            'receive_address': transaction['transferfrom_address'],
            'platform_order_id': transaction.get('order_no', ''),
            'energy_amount': energy_amount,
            'energy_day': package['energy_day'],
            'energy_time': current_time,
            'source_type': 2,  # 自动下单
            'recovery_status': 2 if platform['platform_name'] == 3 else 1,
            'use_trx': transaction.get('use_trx', 0)
        }

        order_model = EnergyPlatformOrderModel()
        return order_model.insert(order_data)

    def update_transaction_status(self, rid, status, comments, current_time, platform_rid=None, package_rid=None):
        """更新交易状态"""
        update_data = {
            'process_status': status,
            'process_comments': comments,
            'process_time': current_time
        }

        if platform_rid:
            update_data['energy_platform_rid'] = platform_rid

        if package_rid:
            update_data['energy_package_rid'] = package_rid

        model = EnergyWalletTradeListModel()
        model.update(rid, update_data)
