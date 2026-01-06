"""
能量租赁机器人服务类
"""

import json
import time
from energy_rental_bot.models.energy_models import (
    EnergyPlatformBotModel,
    EnergyWalletTradeListModel
)
from energy_rental_bot.utils.energy_utils import EnergyUtils


class EnergyWalletServices:
    """能量钱包服务"""

    def get_list(self, status=0):
        """获取能量钱包列表"""
        model = EnergyPlatformBotModel()
        result = model.get_list(status)
        data = {}

        for item in result:
            if item['status'] == 0 and len(item.get('receive_wallet', '')) == 34:
                data[item['rid']] = item

        return data

    def get_id_list(self, return_type=0):
        """获取收款钱包ID和名称列表"""
        data = self.get_list()

        if return_type == 1:
            # 返回钱包地址列表
            return {k: v['receive_wallet'] for k, v in data.items()}
        elif return_type == 2:
            # 返回钱包信息字典
            return {v['receive_wallet']: v for k, v in data.items()}
        elif return_type == 3:
            # 返回活跃钱包列表
            return [v for k, v in data.items() if v['status'] in [0, 2]]
        else:
            # 返回基本信息列表
            return [{'rid': v['rid'], 'receive_wallet': v['receive_wallet']} for k, v in data.items()]


class EnergyWalletTradeTrxServices:
    """能量钱包TRX交易服务"""

    def __init__(self):
        self.limit = 50

    def get_list(self, wallet_info, start_timestamp, end_timestamp, page=0):
        """获取能量钱包数据 - 通过tronscan获取"""
        limit = self.limit
        start = page * limit

        url = (
            "https://apilist.tronscanapi.com/api/new/transfer"
            "?sort=-timestamp&count=true&limit={}&start={}&address={}&toAddress={}&tokens=_&start_timestamp={}&end_timestamp={}"
        ).format(limit, start, wallet_info['receive_wallet'], wallet_info['receive_wallet'], start_timestamp, end_timestamp)

        api_key = EnergyUtils.get_random_api_key('tronapikey')
        headers = {"TRON-PRO-API-KEY": api_key}

        response = EnergyUtils.send_http_request(url, headers=headers)
        if response:
            try:
                data = json.loads(response)
                if 'total' in data and data.get('data'):
                    self.handle_wallet_data(data, wallet_info, start_timestamp, end_timestamp, page, limit)
            except json.JSONDecodeError:
                EnergyUtils.log('TRX_TRADE_ERROR', f'解析TRX交易数据失败: {response}')

    def handle_wallet_data(self, data, wallet_info, start_timestamp, end_timestamp, page, limit):
        """处理收款数据"""
        if 'data' in data:
            transactions = data['data']
            total = data.get('total', 0)

            if transactions:
                hash_list = [tx.get('transactionHash') for tx in transactions]
                existing_hashes = self.check_existing_hashes(hash_list)

                current_time = EnergyUtils.now_date()

                for tx in transactions:
                    if (tx.get('transactionHash') not in existing_hashes
                        and tx.get('contractRet') == 'SUCCESS'
                        and EnergyUtils.calculate_amount(tx.get('amount', 0), 6) >= 1
                        and tx.get('tokenInfo', {}).get('tokenId') == '_'
                        and tx.get('tokenInfo', {}).get('tokenAbbr') == 'trx'):

                        self.add_wallet_data(tx, current_time, wallet_info)

                # 分页处理
                get_total = (page + 1) * limit
                if total > get_total and len(transactions) == limit:
                    self.get_list(wallet_info, start_timestamp, end_timestamp, page + 1)

    def add_wallet_data(self, tx_data, current_time, wallet_info):
        """添加钱包交易数据"""
        tx_record = {
            'tx_hash': tx_data.get('transactionHash'),
            'transferfrom_address': tx_data.get('transferFromAddress'),
            'timestamp': tx_data.get('timestamp'),
            'transferto_address': wallet_info['receive_wallet'],
            'coin_name': 'trx',
            'amount': EnergyUtils.calculate_amount(tx_data.get('amount', 0), 6),
            'get_time': current_time,
            'process_status': 1,
            'process_comments': '待处理',
            'process_time': current_time
        }

        model = EnergyWalletTradeListModel()
        model.insert(tx_record)

    def check_existing_hashes(self, hash_list):
        """检查已存在的交易哈希"""
        model = EnergyWalletTradeListModel()
        return model.get_by_tx_hash(hash_list)


class EnergyWalletTradeUsdtServices:
    """能量钱包USDT交易服务"""

    def get_list(self, wallet_info, start_timestamp, next_url='0'):
        """获取闪兑钱包数据"""
        if next_url != '0':
            url = next_url
        else:
            url = (
                "https://api.trongrid.io/v1/accounts/{}/transactions/trc20"
                "?limit=50&only_to=true&min_timestamp={}&contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
            ).format(wallet_info['receive_wallet'], start_timestamp)

        api_key = EnergyUtils.get_random_api_key('gridapikey')
        headers = {"TRON-PRO-API-KEY": api_key}

        response = EnergyUtils.send_http_request(url, headers=headers)
        if response:
            try:
                data = json.loads(response)
                self.handle_wallet_data(data, wallet_info)
            except json.JSONDecodeError:
                EnergyUtils.log('USDT_TRADE_ERROR', f'解析USDT交易数据失败: {response}')

    def handle_wallet_data(self, data, wallet_info):
        """处理收款数据"""
        if 'data' in data:
            transactions = data['data']

            if transactions:
                hash_list = [tx.get('transaction_id') for tx in transactions]
                existing_hashes = self.check_existing_hashes(hash_list)

                current_time = EnergyUtils.now_date()

                for tx in transactions:
                    if tx.get('transaction_id') not in existing_hashes and tx.get('type') == 'Transfer':
                        self.add_wallet_data(tx, current_time, wallet_info)

                # 处理下一页
                if 'meta' in data and 'links' in data['meta'] and 'next' in data['meta']['links']:
                    self.get_list(wallet_info, 0, data['meta']['links']['next'])

    def add_wallet_data(self, tx_data, current_time, wallet_info):
        """添加钱包交易数据"""
        tx_record = {
            'tx_hash': tx_data.get('transaction_id'),
            'transferfrom_address': tx_data.get('from'),
            'timestamp': tx_data.get('block_timestamp'),
            'transferto_address': wallet_info['receive_wallet'],
            'coin_name': 'usdt',
            'amount': EnergyUtils.calculate_amount(tx_data.get('value', 0), 6),
            'get_time': current_time,
            'process_status': 1,
            'process_comments': '待处理',
            'process_time': current_time
        }

        model = EnergyWalletTradeListModel()
        model.insert(tx_record)

    def check_existing_hashes(self, hash_list):
        """检查已存在的交易哈希"""
        model = EnergyWalletTradeListModel()
        return model.get_by_tx_hash(hash_list)
