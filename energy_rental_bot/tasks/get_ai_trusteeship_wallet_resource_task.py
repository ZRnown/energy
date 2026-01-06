"""
获取AI托管钱包资源任务
"""

import json
import time
from energy_rental_bot.models.energy_models import EnergyAiTrusteeshipModel, EnergyAiBishuModel
from energy_rental_bot.utils.energy_utils import EnergyUtils, Concurrent


class GetAiTrusteeshipWalletResourceTask:
    """获取AI托管钱包资源任务"""

    def execute(self):
        """执行任务"""
        # 智能托管
        self.check_trusteeship_wallets()
        # 笔数套餐
        self.check_bishu_wallets()

    def check_trusteeship_wallets(self):
        """检查智能托管钱包"""
        model = EnergyAiTrusteeshipModel()
        wallet_list = model.get_list_for_resource_check()

        concurrent = Concurrent(5)
        for wallet in wallet_list:
            concurrent.create(lambda w=wallet: self.check_wallet_resource(w, 'trusteeship'))

    def check_bishu_wallets(self):
        """检查笔数套餐钱包"""
        model = EnergyAiBishuModel()
        wallet_list = model.get_list_for_resource_check()

        concurrent = Concurrent(5)
        for wallet in wallet_list:
            concurrent.create(lambda w=wallet: self.check_wallet_resource(w, 'bishu'))

    def check_wallet_resource(self, wallet, wallet_type):
        """检查钱包资源"""
        # 避免API限制
        time.sleep(1)

        # 调用tronscan API检查钱包资源
        url = f'https://apilist.tronscanapi.com/api/accountv2?address={wallet["wallet_addr"]}'
        api_key = EnergyUtils.get_random_api_key('tronapikey')
        headers = {"TRON-PRO-API-KEY": api_key}

        response = EnergyUtils.send_http_request(url, headers=headers)

        if response:
            try:
                data = json.loads(response)
                if 'bandwidth' in data:
                    # 只处理激活的地址
                    is_active = data.get('activated', False)
                    if is_active:
                        bandwidth = data['bandwidth'].get('freeNetRemaining', 0) + data['bandwidth'].get('netRemaining', 0)
                        energy = data['bandwidth'].get('energyRemaining', 0)

                        update_data = {
                            'current_bandwidth_quantity': bandwidth,
                            'current_energy_quantity': energy
                        }

                        # 检查是否需要自动购买
                        threshold = (
                            wallet['min_energy_quantity']
                            if wallet_type == 'trusteeship'
                            else wallet['per_bishu_energy_quantity']
                        )

                        if energy < threshold and wallet.get('is_buy') == 'N':
                            update_data['is_buy'] = 'Y'

                        # 更新数据库
                        if wallet_type == 'trusteeship':
                            model = EnergyAiTrusteeshipModel()
                        else:
                            model = EnergyAiBishuModel()

                        model.update(wallet['rid'], update_data)
            except json.JSONDecodeError:
                EnergyUtils.log('WALLET_RESOURCE_CHECK', f'解析钱包资源数据失败: {wallet["wallet_addr"]}')
