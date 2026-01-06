"""
获取能量钱包TRX交易任务
"""

import time
from energy_rental_bot.services.energy_services import EnergyWalletServices, EnergyWalletTradeTrxServices
from energy_rental_bot.utils.energy_utils import EnergyUtils, Concurrent


class GetEnergyWalletTrxTradeTask:
    """获取能量钱包TRX交易任务"""

    def execute(self):
        """执行任务"""
        wallet_service = EnergyWalletServices()
        wallet_list = wallet_service.get_id_list(3)  # 获取定时任务过滤状态的钱包

        if wallet_list:
            # 协程并发处理
            concurrent = Concurrent(5)
            for wallet in wallet_list:
                concurrent.create(lambda w=wallet: self.process_wallet(w))

    def process_wallet(self, wallet):
        """处理单个钱包"""
        trade_service = EnergyWalletTradeTrxServices()

        # 获取最后处理时间
        start_time = self.get_last_processed_time(wallet['receive_wallet'], 'trx')
        end_time = EnergyUtils.thirteen_time()

        # 获取tronscan数据
        trade_service.get_list(wallet, start_time, end_time)

        # 获取trongrid数据 (这里暂时使用相同的方法，实际应该有不同的实现)
        trade_service.get_list(wallet, start_time, end_time)

    def get_last_processed_time(self, wallet_addr, coin_name):
        """获取最后处理时间"""
        # 这里应该从数据库查询最后处理时间
        # 暂时返回1小时前的时间戳
        return (int(time.time()) - 3600) * 1000
