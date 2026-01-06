#!/usr/bin/env python3
"""
能量租赁机器人主入口文件
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from utils.energy_utils import EnergyUtils
from controllers.energy_controller import TrongasIoController
from tasks.handle_energy_order_task import HandleEnergyOrderTask
from tasks.get_energy_wallet_trx_trade_task import GetEnergyWalletTrxTradeTask
from tasks.get_ai_trusteeship_wallet_resource_task import GetAiTrusteeshipWalletResourceTask
from tasks.handle_ai_energy_order_task import HandleAiEnergyOrderTask
from tasks.send_energy_tg_message_task import SendEnergyTgMessageTask


def main():
    """主函数"""
    # 设置日志
    EnergyUtils.setup_logging()

    parser = argparse.ArgumentParser(description='能量租赁机器人')
    parser.add_argument('task', choices=[
        'HandleEnergyOrder',
        'GetEnergyWalletTrxTrade',
        'GetAiTrusteeshipWalletResource',
        'HandleAiEnergyOrder',
        'SendEnergyTgMessage',
        'notice'  # API回调处理
    ], help='要执行的任务')
    parser.add_argument('--receive-address', help='接收地址 (用于notice任务)')
    parser.add_argument('--residue', help='剩余数量 (用于notice任务)')

    args = parser.parse_args()

    try:
        if args.task == 'HandleEnergyOrder':
            task = HandleEnergyOrderTask()
            task.execute()
            print("能量订单处理完成")

        elif args.task == 'GetEnergyWalletTrxTrade':
            task = GetEnergyWalletTrxTradeTask()
            task.execute()
            print("TRX交易数据获取完成")

        elif args.task == 'GetAiTrusteeshipWalletResource':
            task = GetAiTrusteeshipWalletResourceTask()
            task.execute()
            print("钱包资源检查完成")

        elif args.task == 'HandleAiEnergyOrder':
            task = HandleAiEnergyOrderTask()
            task.execute()
            print("AI能量订单处理完成")

        elif args.task == 'SendEnergyTgMessage':
            task = SendEnergyTgMessageTask()
            task.execute()
            print("消息通知发送完成")

        elif args.task == 'notice':
            if not args.receive_address:
                print("错误: notice任务需要 --receive-address 参数")
                sys.exit(1)

            controller = TrongasIoController()
            result = controller.notice({
                'receiveAddress': args.receive_address,
                'residue': args.residue or ''
            })
            print(f"API回调处理结果: {result}")

        else:
            print(f"未知任务: {args.task}")
            sys.exit(1)

    except Exception as e:
        EnergyUtils.log('MAIN_ERROR', f'任务执行失败: {str(e)}')
        print(f"任务执行失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
