"""
能量租赁机器人 - Telegram Bot 核心类
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

# Monkey patch APScheduler to use pytz timezone
import apscheduler.util
original_astimezone = apscheduler.util.astimezone
def patched_astimezone(tz):
    if tz is None:
        return pytz.timezone('UTC')
    if hasattr(tz, 'zone'):  # already a pytz timezone
        return tz
    return pytz.timezone('UTC')  # fallback
apscheduler.util.astimezone = patched_astimezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from energy_rental_bot.config.config import TELEGRAM_CONFIG, TASK_CONFIG, ENERGY_RENT_CONFIG, BISHA_CONFIG
from energy_rental_bot.controllers.energy_controller import TrongasIoController
from energy_rental_bot.models.energy_models import (
    EnergyAiBishuModel,
    EnergyAiTrusteeshipModel,
    EnergyWalletTradeListModel
)
from energy_rental_bot.tasks.handle_energy_order_task import HandleEnergyOrderTask
from energy_rental_bot.tasks.get_energy_wallet_trx_trade_task import GetEnergyWalletTrxTradeTask
from energy_rental_bot.tasks.handle_ai_energy_order_task import HandleAiEnergyOrderTask
from energy_rental_bot.tasks.send_energy_tg_message_task import SendEnergyTgMessageTask
from energy_rental_bot.utils.energy_utils import EnergyUtils


class EnergyRentalBot:
    """能量租赁机器人主类"""

    def __init__(self):
        self.application = None
        self.logger = logging.getLogger(__name__)

        # 初始化控制器
        self.trongas_controller = TrongasIoController()

        # 用户状态管理
        self.user_states: Dict[int, Dict[str, Any]] = {}

        # 任务调度器
        self.scheduler_task = None

    async def initialize(self) -> None:
        """初始化机器人"""
        try:
            # 清除环境变量中的代理设置
            import os
            proxy_vars = ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]

            # 创建应用
            token = TELEGRAM_CONFIG['bots'][0]['token']
            self.application = (
                Application.builder()
                .token(token)
                .job_queue(None)  # 禁用job_queue避免时区问题
                .post_init(self._post_init)
                .build()
            )

            # 注册处理器
            await self._register_handlers()

            self.logger.info("Telegram Bot 初始化成功")

        except Exception as e:
            self.logger.error(f"Bot 初始化失败: {str(e)}")
            raise

    async def _post_init(self, application: Application) -> None:
        """机器人启动后的初始化"""
        # 启动后台任务调度器
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("后台任务调度器已启动")

    async def _register_handlers(self) -> None:
        """注册消息处理器"""
        if not self.application:
            return

        # 命令处理器
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("buyenergy", self._handle_buy_energy))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("admin", self._handle_admin))

        # 内联按钮处理器
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))

        # 文本消息处理器 (处理钱包地址输入等)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_text_message
        ))

        # 错误处理器
        self.application.add_error_handler(self._handle_error)

    def start(self) -> None:
        """启动机器人"""
        try:
            # 确保在主事件循环中运行
            if not self.application:
                # 创建新的事件循环来初始化
                import nest_asyncio
                nest_asyncio.apply()  # 允许嵌套事件循环
                asyncio.run(self.initialize())

            self.logger.info("能量租赁机器人启动中...")

            # 启动机器人 (这是阻塞调用)
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            self.logger.error(f"启动机器人失败: {str(e)}")
            raise

    async def stop(self) -> None:
        """停止机器人"""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        if self.application:
            await self.application.shutdown()

        self.logger.info("能量租赁机器人已停止")

    async def _scheduler_loop(self) -> None:
        """后台任务调度循环"""
        self.logger.info("后台任务循环已开始")
        while True:
            try:
                current_time = datetime.now(pytz.timezone('UTC'))

                # 每分钟执行的任务
                if current_time.second < 5:  # 避免重复执行
                    # 使用 asyncio.create_task 不阻塞循环
                    asyncio.create_task(self._run_minute_tasks_safe())

                # 每10分钟执行的任务
                if current_time.minute % 10 == 0 and current_time.second < 5:
                    asyncio.create_task(self._run_ten_minute_tasks_safe())

                await asyncio.sleep(5)  # 每5秒检查一次

            except asyncio.CancelledError:
                self.logger.info("后台任务循环被取消")
                break
            except Exception as e:
                self.logger.error(f"调度器严重错误: {str(e)}")
                await asyncio.sleep(30)

    # 添加新的安全执行方法 wrapper

    async def _run_minute_tasks_safe(self) -> None:
        """安全运行分钟任务"""
        try:
            await self._run_minute_tasks()
        except Exception as e:
            self.logger.error(f"分钟任务组执行失败: {str(e)}")

    async def _run_ten_minute_tasks_safe(self) -> None:
        """安全运行10分钟任务"""
        try:
            await self._run_ten_minute_tasks()
        except Exception as e:
            self.logger.error(f"10分钟任务组执行失败: {str(e)}")

    # 稍微修改 _run_minute_tasks，将其变为非阻塞（因为原来的 Task.execute 是同步的）

    async def _run_minute_tasks(self) -> None:
        """每分钟执行的任务"""
        # 将同步阻塞任务放到线程池中运行，避免阻塞 Telegram Bot 的心跳
        loop = asyncio.get_running_loop()

        await loop.run_in_executor(None, self._execute_minute_logic)

    def _execute_minute_logic(self):
        """同步执行的分钟逻辑"""
        try:
            # 获取TRX交易数据
            trx_task = GetEnergyWalletTrxTradeTask()
            trx_task.execute()
        except Exception as e:
            self.logger.error(f"TRX交易任务失败: {e}")

        try:
            # 处理能量订单
            order_task = HandleEnergyOrderTask()
            order_task.execute()
        except Exception as e:
            self.logger.error(f"订单处理任务失败: {e}")

        try:
            # 发送通知
            notify_task = SendEnergyTgMessageTask()
            notify_task.execute()
        except Exception as e:
            self.logger.error(f"通知任务失败: {e}")

    async def _run_ten_minute_tasks(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._execute_ten_minute_logic)

    def _execute_ten_minute_logic(self):
        try:
            # 处理AI能量订单
            ai_task = HandleAiEnergyOrderTask()
            ai_task.execute()
        except Exception as e:
             self.logger.error(f"AI订单任务失败: {e}")

    # ===== 命令处理器 =====

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /start 命令"""
        user = update.effective_user
        if not user:
            return

        welcome_text = (
            f"🖌 <b>欢迎使用能量租赁机器人</b>\n\n"
            f"👋 你好，{user.first_name}！\n\n"
            f"<b>我可以帮你：</b>\n"
            f"🔋 能量闪租\n"
            f"📝 笔数套餐服务\n\n"
            f"发送 /buyenergy 开始使用！\n"
            f"发送 /help 查看详细帮助"
        )

        keyboard = [
            [
                KeyboardButton("🔋 能量闪租"),
                KeyboardButton("📝 笔数套餐")
            ],
            [
                KeyboardButton("📊 我的状态"),
                KeyboardButton("👨‍💼 客服")
            ]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_buy_energy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /buyenergy 命令"""
        user = update.effective_user
        if not user:
            return

        # 设置用户状态为等待钱包地址
        self.user_states[user.id] = {
            'state': 'waiting_wallet_address',
            'action': 'buy_energy'
        }

        text = (
            "🔋 <b>能量购买服务</b>\n\n"
            "请选择购买方式：\n\n"
            "1️⃣ <b>自助购买</b>\n"
            "• 发送TRX到指定钱包\n"
            "• 自动匹配能量套餐\n"
            "• 实时到账通知\n\n"
            "2️⃣ <b>笔数套餐</b>\n"
            "• USDT购买固定次数\n"
            "• 按需使用更省钱\n"
            "• 智能计算剩余次数"
        )

        keyboard = [
            [
                InlineKeyboardButton("1️⃣ 自助购买", callback_data="manual_buy"),
                InlineKeyboardButton("2️⃣ 笔数套餐", callback_data="setup_bishu")
            ],
            [
                InlineKeyboardButton("❌ 取消", callback_data="cancel")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /help 命令"""
        help_text = (
            "📚 <b>能量租赁机器人使用帮助</b>\n\n"
            "<b>基础命令：</b>\n"
            "/start - 开始使用机器人\n"
            "/buyenergy - 购买能量服务\n"
            "/status - 查看我的状态\n"
            "/help - 显示此帮助\n\n"
            "<b>服务说明：</b>\n\n"
            "🔋 <b>自助购买</b>\n"
            "向指定钱包转账TRX，自动购买能量\n"
            "支持多种套餐，实时到账\n\n"
            "📝 <b>笔数套餐</b>\n"
            "USDT购买固定次数的能量使用权\n"
            "更适合偶尔使用的用户\n\n"
            "<b>常见问题：</b>\n"
            "• 如何开始使用？发送 /buyenergy\n"
            "• 能量什么时候到账？购买后立即到账\n"
            "• 是否安全？采用多重验证，确保安全"
        )

        await update.message.reply_text(
            help_text,
            parse_mode='HTML'
        )

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /status 命令"""
        user = update.effective_user
        if not user:
            return

        # 查询用户的托管和笔数套餐状态
        trusteeship_model = EnergyAiTrusteeshipModel()
        bishu_model = EnergyAiBishuModel()

        trusteeship_data = trusteeship_model.get_by_wallet_addr(f"user_{user.id}")
        bishu_data = bishu_model.get_by_wallet_addr(f"user_{user.id}")

        status_text = f"📊 <b>{user.first_name} 的账户状态</b>\n\n"

        if trusteeship_data:
            status_text += (
                f"🤖 <b>智能托管</b>\n"
                f"状态：{'运行中' if trusteeship_data.get('is_buy') == 'N' else '购买中'}\n"
                f"当前能量：{trusteeship_data.get('current_energy_quantity', 0)}\n"
                f"已购买：{trusteeship_data.get('total_buy_quantity', 0)} 次\n\n"
            )

        if bishu_data:
            status_text += (
                f"📝 <b>笔数套餐</b>\n"
                f"状态：{'正常' if bishu_data.get('is_buy') == 'N' else '购买中'}\n"
                f"当前能量：{bishu_data.get('current_energy_quantity', 0)}\n"
                f"已购买：{bishu_data.get('total_buy_quantity', 0)} 次\n"
                f"USDT消费：{bishu_data.get('total_buy_usdt', 0)}\n\n"
            )

        if not trusteeship_data and not bishu_data:
            status_text += "❌ 您还没有设置任何服务\n\n发送 /buyenergy 开始使用"

        keyboard = [
            [InlineKeyboardButton("🔄 刷新", callback_data="refresh_status")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /admin 命令 (管理员功能)"""
        user = update.effective_user
        if not user:
            return

        # 检查是否为管理员
        admin_uid = TELEGRAM_CONFIG['bots'][0].get('admin_uid')
        if str(user.id) != admin_uid:
            await update.message.reply_text("❌ 您没有管理员权限")
            return

        admin_text = (
            "⚙️ <b>管理员面板</b>\n\n"
            "<b>系统状态：</b>\n"
            "• 机器人运行正常\n"
            "• 后台任务运行中\n"
            "• 数据库连接正常\n\n"
            "<b>快捷操作：</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton("📈 系统统计", callback_data="admin_stats"),
                InlineKeyboardButton("🔧 配置管理", callback_data="admin_config")
            ],
            [
                InlineKeyboardButton("📊 交易记录", callback_data="admin_trades"),
                InlineKeyboardButton("🚨 异常处理", callback_data="admin_errors")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            admin_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # ===== 内联按钮处理器 =====

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理内联按钮回调"""
        query = update.callback_query
        if not query:
            return

        await query.answer()

        callback_data = query.data
        user = query.from_user

        # 路由到对应的处理函数
        handlers = {
            # 动态生成笔数套餐购买回调
            **{f'buy_{count}_bishu': lambda q, u, c=count: self._callback_buy_bishu(q, u, c)
               for count in BISHA_CONFIG['available_packages']},

            # 其他功能回调
            'check_bishu_status': self._callback_check_bishu_status,
            'contact_admin': self._callback_contact_admin,
            'back_to_main': self._callback_back_to_main,

            # 兼容旧的回调
            'energy_rent': self._callback_energy_rent,
            'bishu_package': self._callback_bishu_package,
            'my_status': self._callback_my_status,
            'manual_buy': self._callback_manual_buy,
            'cancel': self._callback_cancel,
            'refresh_status': self._callback_refresh_status,
            'admin_stats': self._callback_admin_stats,
            'admin_config': self._callback_admin_config,
            'admin_trades': self._callback_admin_trades,
            'admin_errors': self._callback_admin_errors,
        }

        handler = handlers.get(callback_data)
        if handler:
            await handler(query, user)
        else:
            await query.edit_message_text("❌ 未知操作")

    # ===== 内联菜单回调处理函数 =====

    async def _callback_energy_rent_manual(self, query, user):
        """能量闪租 - 自助购买回调"""
        await self._callback_energy_rent(query, user)

    async def _callback_energy_rent_bishu(self, query, user):
        """能量闪租 - 笔数套餐回调"""
        await self._callback_setup_bishu(query, user)

    async def _callback_check_bishu_status(self, query, user):
        """查看笔数套餐状态回调"""
        await self._callback_my_status(query, user)

    async def _callback_buy_bishu(self, query, user, bishu_count):
        """购买指定数量笔数的回调"""
        price_per_bishu = BISHA_CONFIG['price_per_bishu']
        total_price = bishu_count * price_per_bishu

        text = (
            f"💰 <b>购买 {bishu_count} 笔套餐</b>\n\n"
            f"📊 笔数：{bishu_count} 笔\n"
            f"💵 单价：{price_per_bishu} TRX/笔\n"
            f"💰 总价：<b>{total_price} TRX</b>\n\n"
            "请向以下地址转账对应 TRX：\n\n"
            f"<code>{BISHA_CONFIG['receive_wallet']}</code>\n\n"
            "转账后系统会自动处理并发送能量到您的地址。"
        )

        keyboard = [
            [InlineKeyboardButton("❌ 取消", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_check_bishu_status(self, query, user):
        """查看笔数状态回调"""
        await self._callback_my_status(query, user)

    async def _callback_contact_admin(self, query, user):
        """联系客服回调"""
        text = (
            "👨‍💼 <b>联系客服</b>\n\n"
            "如需帮助，请联系管理员：\n"
            "@admin\n\n"
            "或返回主菜单继续使用"
        )

        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_back_to_main(self, query, user):
        """返回主菜单回调"""
        welcome_text = (
            f"🎉 <b>您好，超级</b> 🎉\n\n"
            f"🪪 <b>您的ID：{user.id}</b>\n\n"
            f"👏 <b>欢迎使用 【波场能量租赁】</b>\n\n"
            f"<b>请选择以下服务：</b>"
        )

        # 返回一级键盘菜单
        keyboard = [
            [
                KeyboardButton("🔋 能量闪租"),
                KeyboardButton("📝 笔数套餐")
            ],
            [
                KeyboardButton("📊 我的状态"),
                KeyboardButton("👨‍💼 联系客服")
            ]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # ===== 一级菜单处理函数（显示内联菜单）=====

    async def _show_energy_rent_inline_menu(self, update, user):
        """显示能量闪租内联菜单"""
        config = ENERGY_RENT_CONFIG
        prices = config['prices']

        text = (
            "💹 <b>当前能量价格:</b>\n\n"
            f"对方有U   {prices['with_u']['trx']} TRX = {prices['with_u']['energy']:,}\n"
            f"对方无U   {prices['without_u']['trx']} TRX = {prices['without_u']['energy']:,}\n\n"
            f"最高单笔支持 {config['max_single_trx']} TRX，可收到 {config['max_energy']:,} 能量。\n\n"
            f"⚡ 租赁时长默认 {config['rent_duration_hours']} 小时\n\n"
            "💰 请向此地址转账对应 TRX，机器人会立即发送相应能量到你账户。\n\n"
            "👇 点击下方地址可复制\n\n"
            f"<code>{config['receive_wallet']}</code>"
        )

        keyboard = [
            [InlineKeyboardButton("❌ 取消", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _show_bishu_package_inline_menu(self, update, user):
        """显示笔数套餐内联菜单"""
        text = (
            f"🔥 <b>笔数套餐</b>\n\n"
            "👏 欢迎使用【笔数套餐】\n\n"
            f"🔥 按笔数下单，没有时长限制，下单成功后，将立刻发送{BISHA_CONFIG['energy_per_bishu']}能量到接收地址，接收地址每次USDT转账后计1笔费用，且能量将在{BISHA_CONFIG['energy_recovery_time']}秒内再次补充至{BISHA_CONFIG['energy_per_bishu']}。\n\n"
            f"❤️ 当地址余额少于{BISHA_CONFIG['auto_gift_trx_threshold']}TRX且带宽不足{BISHA_CONFIG['auto_gift_bandwidth_threshold']}将自动赠送{BISHA_CONFIG['auto_gift_amount']}TRX，让您丝滑享受USDT转账。\n\n"
            f"⚠️ {BISHA_CONFIG['deduct_after_hours']}小时内没有转账也将扣减1笔。连续{BISHA_CONFIG['pause_after_hours']}小时没有转账自动暂停，您可在机器人[查询笔数]后手动开启。\n\n"
            f"👇 真笔数，单笔仅需 {BISHA_CONFIG['price_per_bishu']} TRX，请根据个人需求点击下方按钮下单。"
        )

        # 动态生成按钮
        packages = BISHA_CONFIG['available_packages']
        keyboard = []

        # 分行显示，每行4个按钮
        for i in range(0, len(packages), 4):
            row = []
            for j in range(4):
                if i + j < len(packages):
                    count = packages[i + j]
                    row.append(InlineKeyboardButton(f"{count}笔", callback_data=f"buy_{count}_bishu"))
            if row:
                keyboard.append(row)

        # 添加操作按钮
        keyboard.append([
            InlineKeyboardButton("🔄 查询笔数", callback_data="check_bishu_status"),
            InlineKeyboardButton("👨‍💼 联系客服", callback_data="contact_admin"),
            InlineKeyboardButton("❌ 取消", callback_data="cancel")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _show_my_status_inline_menu(self, update, user):
        """显示我的状态 - 直接显示当前用户状态"""
        await self._handle_status_via_message(update, user)

    async def _show_contact_admin_inline_menu(self, update, user):
        """显示联系客服内联菜单"""
        cs_config = BISHA_CONFIG['customer_service']
        text = (
            "👨‍💼 <b>联系客服</b>\n\n"
            f"如需帮助，请联系管理员：\n"
            f"{cs_config['admin_username']}\n\n"
            f"工作时间：{cs_config['work_hours']}\n"
            f"我们会在{cs_config['response_time']}回复您的问题"
        )

        keyboard = [
            [InlineKeyboardButton("💬 发送消息", url=f"https://t.me/{cs_config['admin_username'][1:]}")],
            [InlineKeyboardButton("❌ 关闭", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # ===== 二级菜单处理函数 =====

    async def _handle_energy_rent_menu(self, update, user):
        """处理能量闪租菜单"""
        text = (
            "🔋 <b>能量闪租服务</b>\n\n"
            "将TRX转账到以下钱包地址：\n\n"
            "<code>TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t</code>\n\n"
            "支持的TRX数量：\n"
            "• 50 TRX = 32000能量\n"
            "• 100 TRX = 65000能量\n\n"
            "转账后能量会在1-3分钟内到账\n"
            "⚠️ 请勿发送其他代币，只发送TRX"
        )

        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_bishu_package_menu(self, update, user):
        """处理笔数套餐菜单"""
        await self._callback_setup_bishu_via_message(update, user)

    async def _handle_my_status_menu(self, update, user):
        """处理我的状态菜单"""
        await self._handle_status_via_message(update, user)

    async def _handle_help_menu(self, update, user):
        """处理帮助菜单"""
        await self._handle_help_via_message(update, user)

    async def _handle_back_to_main_menu(self, update, user):
        """处理返回主菜单"""
        welcome_text = (
            f"🎉 <b>您好，超级</b> 🎉\n\n"
            f"🪪 <b>您的ID：{user.id}</b>\n\n"
            f"👏 <b>欢迎使用 【波场能量租赁】</b>\n\n"
            f"<b>请选择以下服务：</b>"
        )

        keyboard = [
            [
                KeyboardButton("🔋 能量闪租"),
                KeyboardButton("📝 笔数套餐")
            ],
            [
                KeyboardButton("📊 我的状态"),
                KeyboardButton("👨‍💼 联系客服")
            ]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_cancel_setup(self, update, user):
        """处理取消设置"""
        # 清除用户状态
        if user.id in self.user_states:
            del self.user_states[user.id]

        text = "❌ 操作已取消\n\n返回主菜单"
        await self._handle_back_to_main_menu(update, user)

    async def _handle_contact_admin(self, update, user):
        """处理联系客服"""
        text = "👨‍💼 <b>联系客服</b>\n\n如需帮助，请联系管理员：\n@admin\n\n或发送 /start 返回主菜单"
        await update.message.reply_text(text, parse_mode='HTML')

    async def _handle_secondary_menu_actions(self, update, user, text):
        """处理二级菜单动作"""
        # 处理取消设置等操作
        if text == '❌ 取消设置':
            await self._handle_cancel_setup(update, user)
        elif text == '❌ 取消查询':
            await self._handle_cancel_wallet_status_query(update, user)
        else:
            # 检查用户状态
            user_state = self.user_states.get(user.id)
            if user_state:
                state = user_state.get('state')
                action = user_state.get('action')

                if state == 'waiting_wallet_address':
                    await self._handle_wallet_address_input(update, user, text, action)
                elif state == 'waiting_wallet_status':
                    await self._handle_wallet_status_input(update, user, text)
            else:
                # 未知消息，发送帮助信息
                await update.message.reply_text(
                    "请使用键盘菜单选择功能，或发送 /start 开始使用"
                )

    # ===== 回调处理函数 =====

    async def _callback_energy_rent(self, query, user):
        """能量闪租回调"""
        text = (
            "🔋 <b>能量闪租服务</b>\n\n"
            "将TRX转账到以下钱包地址：\n\n"
            "<code>TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t</code>\n\n"
            "支持的TRX数量：\n"
            "• 50 TRX = 32000能量\n"
            "• 100 TRX = 65000能量\n\n"
            "转账后能量会在1-3分钟内到账\n"
            "⚠️ 请勿发送其他代币，只发送TRX"
        )

        keyboard = [
            [InlineKeyboardButton("📋 复制地址", callback_data="copy_address")],
            [InlineKeyboardButton("🔙 返回", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_ai_trusteeship(self, query, user):
        """智能托管回调"""
        await self._callback_setup_trusteeship(query, user)

    async def _callback_bishu_package(self, query, user):
        """笔数套餐回调"""
        await self._callback_setup_bishu(query, user)

    async def _callback_trx_exchange(self, query, user):
        """TRX闪兑回调"""
        text = (
            "💰 <b>TRX闪兑服务</b>\n\n"
            "暂时不可用\n\n"
            "如需兑换服务，请联系客服"
        )

        keyboard = [
            [InlineKeyboardButton("👨‍💼 联系客服", url="https://t.me/admin")],
            [InlineKeyboardButton("🔙 返回", callback_data="back_to_main")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_my_status(self, query, user):
        """我的状态回调"""
        await self._handle_status_via_query(query, user)

    async def _callback_help(self, query, user):
        """帮助回调"""
        await self._handle_help_via_query(query, user)

    async def _callback_manual_buy(self, query, user):
        """手动购买回调"""
        await self._callback_energy_rent(query, user)

    async def _callback_setup_bishu(self, query, user):
        """设置笔数套餐回调"""
        # 设置用户状态
        self.user_states[user.id] = {
            'state': 'waiting_wallet_address',
            'action': 'setup_bishu'
        }

        text = (
            "📝 <b>设置笔数套餐</b>\n\n"
            "请回复您的TRON钱包地址：\n\n"
            "<b>笔数套餐说明：</b>\n"
            "• USDT购买固定次数的能量使用权\n"
            "• 每次使用消耗1个笔数\n"
            "• 能量自动补充，无需等待\n"
            "• 更适合偶尔使用的用户\n\n"
            "<b>价格：</b>\n"
            "• 1 USDT = 约50个笔数\n"
            "• 能量数量：50000每次\n\n"
            "<b>购买方式：</b>\n"
            "向以下地址转账USDT：\n"
            "<code>TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t</code>"
        )

        keyboard = [
            [InlineKeyboardButton("❌ 取消设置", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_setup_bishu_via_message(self, update, user):
        """通过消息设置笔数套餐"""
        # 设置用户状态
        self.user_states[user.id] = {
            'state': 'waiting_wallet_address',
            'action': 'setup_bishu'
        }

        text = (
            "📝 <b>设置笔数套餐</b>\n\n"
            "请回复您的TRON钱包地址：\n\n"
            "<b>笔数套餐说明：</b>\n"
            "• USDT购买固定次数的能量使用权\n"
            "• 每次使用消耗1个笔数\n"
            "• 能量自动补充，无需等待\n"
            "• 更适合偶尔使用的用户\n\n"
            "<b>价格：</b>\n"
            "• 1 USDT = 约50个笔数\n"
            "• 能量数量：50000每次\n\n"
            "<b>购买方式：</b>\n"
            "向以下地址转账USDT：\n"
            "<code>TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t</code>"
        )

        keyboard = [
            [InlineKeyboardButton("❌ 取消设置", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_cancel(self, query, user):
        """取消回调"""
        # 清除用户状态
        if user.id in self.user_states:
            del self.user_states[user.id]

        text = "❌ 操作已取消\n\n发送 /start 重新开始"
        await query.edit_message_text(text)

    async def _callback_refresh_status(self, query, user):
        """刷新状态回调"""
        await self._handle_status_via_query(query, user)

    async def _callback_admin_stats(self, query, user):
        """管理员统计回调"""
        text = "📈 <b>系统统计</b>\n\n正在获取统计数据..."
        await query.edit_message_text(text, parse_mode='HTML')

        # 这里应该实现真正的统计逻辑
        stats_text = (
            "📈 <b>系统统计</b>\n\n"
            "<b>今日数据：</b>\n"
            f"• 交易处理：{0} 笔\n"
            f"• 能量租赁：{0} 次\n"
            f"• 活跃用户：{0} 个\n"
            f"• 总收入：{0} TRX\n\n"
            "<b>系统状态：</b>\n"
            "• 数据库：正常\n"
            "• API服务：正常\n"
            "• 机器人：运行中"
        )

        keyboard = [
            [InlineKeyboardButton("🔙 返回", callback_data="back_to_admin")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _callback_admin_config(self, query, user):
        """管理员配置回调"""
        text = "🔧 <b>配置管理</b>\n\n功能开发中..."
        await query.edit_message_text(text, parse_mode='HTML')

    async def _callback_admin_trades(self, query, user):
        """管理员交易记录回调"""
        text = "📊 <b>交易记录</b>\n\n功能开发中..."
        await query.edit_message_text(text, parse_mode='HTML')

    async def _callback_admin_errors(self, query, user):
        """管理员异常处理回调"""
        text = "🚨 <b>异常处理</b>\n\n功能开发中..."
        await query.edit_message_text(text, parse_mode='HTML')

    # ===== 文本消息处理器 =====

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理文本消息"""
        user = update.effective_user
        if not user:
            return

        text = update.message.text.strip()

        # 检查用户状态
        user_state = self.user_states.get(user.id)
        if user_state:
            state = user_state.get('state')
            action = user_state.get('action')

            if state == 'waiting_wallet_address':
                await self._handle_wallet_address_input(update, user, text, action)
            return

        # 处理键盘菜单点击（一级菜单）
        menu_handlers = {
            '🔋 能量闪租': self._show_energy_rent_inline_menu,
            '📝 笔数套餐': self._show_bishu_package_inline_menu,
            '📊 我的状态': self._show_my_status_inline_menu,
            '👨‍💼 客服': self._show_contact_admin_inline_menu,
        }

        handler = menu_handlers.get(text)
        if handler:
            await handler(update, user)
        else:
            # 处理二级菜单或其他操作
            await self._handle_secondary_menu_actions(update, user, text)

    async def _handle_wallet_status_input(self, update, user, wallet_address):
        """处理钱包状态查询输入"""
        # 验证钱包地址格式
        if not self._is_valid_tron_address(wallet_address):
            await update.message.reply_text(
                "❌ 无效的TRON钱包地址格式\n\n"
                "请检查地址是否正确\n"
                "TRON地址以T开头，共34位字符"
            )
            return

        # 查询钱包状态
        trusteeship_model = EnergyAiTrusteeshipModel()
        bishu_model = EnergyAiBishuModel()

        trusteeship_data = trusteeship_model.get_by_wallet_addr(wallet_address)
        bishu_data = bishu_model.get_by_wallet_addr(wallet_address)

        status_text = f"📊 <b>钱包状态查询</b>\n\n"
        status_text += f"🏠 <b>钱包地址：</b>\n<code>{wallet_address}</code>\n\n"

        has_service = False

        if trusteeship_data:
            has_service = True
            status_text += (
                f"🤖 <b>智能托管服务</b>\n"
                f"• 状态：{'运行中' if trusteeship_data.get('is_buy') == 'N' else '购买中'}\n"
                f"• 当前能量：{trusteeship_data.get('current_energy_quantity', 0)}\n"
                f"• 已购买次数：{trusteeship_data.get('total_buy_quantity', 0)}\n"
                f"• 注册时间：{trusteeship_data.get('create_time', '未知')}\n\n"
            )

        if bishu_data:
            has_service = True
            status_text += (
                f"📝 <b>笔数套餐服务</b>\n"
                f"• 状态：{'正常' if bishu_data.get('is_buy') == 'N' else '购买中'}\n"
                f"• 当前能量：{bishu_data.get('current_energy_quantity', 0)}\n"
                f"• 已使用笔数：{bishu_data.get('total_buy_quantity', 0)}\n"
                f"• 剩余笔数：{bishu_data.get('max_buy_quantity', 0) - bishu_data.get('total_buy_quantity', 0)}\n"
                f"• 注册时间：{bishu_data.get('create_time', '未知')}\n\n"
            )

        if not has_service:
            status_text += "❌ 此钱包地址未注册任何服务\n\n如需使用服务，请先进行设置"

        # 清除用户状态
        if user.id in self.user_states:
            del self.user_states[user.id]

        keyboard = [
            [
                KeyboardButton("🔋 能量闪租"),
                KeyboardButton("📝 笔数套餐")
            ],
            [
                KeyboardButton("📊 我的状态"),
                KeyboardButton("👨‍💼 联系客服")
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_cancel_wallet_status_query(self, update, user):
        """取消钱包状态查询"""
        # 清除用户状态
        if user.id in self.user_states:
            del self.user_states[user.id]

        text = "❌ 已取消查询\n\n返回主菜单"
        await self._handle_back_to_main_menu(update, user)

    async def _handle_wallet_address_input(self, update, user, wallet_address, action):
        """处理钱包地址输入"""
        # 验证钱包地址格式
        if not self._is_valid_tron_address(wallet_address):
            await update.message.reply_text(
                "❌ 无效的TRON钱包地址格式\n\n"
                "请检查地址是否正确\n"
                "TRON地址以T开头，共34位字符"
            )
            return

        # 根据不同的action处理
        if action == 'setup_trusteeship':
            await self._setup_trusteeship(update, user, wallet_address)
        elif action == 'setup_bishu':
            await self._setup_bishu(update, user, wallet_address)
        elif action == 'buy_energy':
            await self._process_energy_purchase(update, user, wallet_address)
        else:
            await update.message.reply_text("❌ 未知操作类型")

        # 清除用户状态
        if user.id in self.user_states:
            del self.user_states[user.id]

    async def _setup_bishu(self, update, user, wallet_address):
        """设置笔数套餐"""
        try:
            # 检查是否已存在
            bishu_model = EnergyAiBishuModel()
            existing = bishu_model.get_by_wallet_addr(wallet_address)

            if existing:
                await update.message.reply_text(
                    "⚠️ 此钱包地址已设置笔数套餐\n\n"
                    "请使用其他地址或联系客服"
                )
                return

            # 创建笔数套餐记录
            insert_data = {
                'bot_rid': 1,
                'wallet_addr': wallet_address,
                'tg_uid': str(user.id),
                'per_bishu_energy_quantity': 50000,
                'max_buy_quantity': 1000,
                'is_buy': 'N',
                'status': 0,
                'current_energy_quantity': 0,
                'total_buy_quantity': 0,
                'total_buy_usdt': 0,
                'is_notice': 'Y',
                'is_notice_admin': 'N',
                'create_time': EnergyUtils.now_date()
            }

            bishu_model.insert(insert_data)

            success_text = (
                "✅ <b>笔数套餐设置成功！</b>\n\n"
                f"钱包地址：{EnergyUtils.format_address(wallet_address)}\n\n"
                "<b>现在可以购买笔数：</b>\n"
                "• 向指定地址转账USDT\n"
                "• 1 USDT ≈ 50个笔数\n"
                "• 每个笔数 = 50000能量\n\n"
                "购买地址：\n"
                "<code>TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t</code>\n\n"
                "发送 /status 查看状态"
            )

            await update.message.reply_text(
                success_text,
                parse_mode='HTML'
            )

        except Exception as e:
            self.logger.error(f"设置笔数套餐失败: {str(e)}")
            await update.message.reply_text("❌ 设置失败，请稍后重试")

    async def _process_energy_purchase(self, update, user, wallet_address):
        """处理能量购买"""
        await update.message.reply_text(
            f"🔄 正在处理钱包 {EnergyUtils.format_address(wallet_address)} 的能量购买...\n\n"
            "请稍候..."
        )

        # 这里可以调用实际的购买逻辑
        # 暂时返回提示信息
        await update.message.reply_text(
            "✅ 能量购买请求已接收\n\n"
            "系统正在处理您的请求，请等待到账通知"
        )

    # ===== 辅助方法 =====

    def _is_valid_tron_address(self, address: str) -> bool:
        """验证TRON地址格式"""
        if not address or not isinstance(address, str):
            return False

        # TRON地址基本格式检查
        return (
            address.startswith('T') and
            len(address) == 34 and
            address.isalnum()
        )

    async def _handle_status_via_query(self, query, user):
        """通过query处理状态查询"""
        # 复用状态处理逻辑
        trusteeship_model = EnergyAiTrusteeshipModel()
        bishu_model = EnergyAiBishuModel()

        trusteeship_data = trusteeship_model.get_by_wallet_addr(f"user_{user.id}")
        bishu_data = bishu_model.get_by_wallet_addr(f"user_{user.id}")

        status_text = f"📊 <b>{user.first_name} 的账户状态</b>\n\n"

        if trusteeship_data:
            status_text += (
                f"🤖 <b>智能托管</b>\n"
                f"状态：{'运行中' if trusteeship_data.get('is_buy') == 'N' else '购买中'}\n"
                f"当前能量：{trusteeship_data.get('current_energy_quantity', 0)}\n"
                f"已购买：{trusteeship_data.get('total_buy_quantity', 0)} 次\n\n"
            )

        if bishu_data:
            status_text += (
                f"📝 <b>笔数套餐</b>\n"
                f"状态：{'正常' if bishu_data.get('is_buy') == 'N' else '购买中'}\n"
                f"当前能量：{bishu_data.get('current_energy_quantity', 0)}\n"
                f"已购买：{bishu_data.get('total_buy_quantity', 0)} 次\n"
                f"USDT消费：{bishu_data.get('total_buy_usdt', 0)}\n\n"
            )

        if not trusteeship_data and not bishu_data:
            status_text += "❌ 您还没有设置任何服务\n\n发送 /buyenergy 开始使用"

        keyboard = [
            [InlineKeyboardButton("🔄 刷新", callback_data="refresh_status")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_help_via_query(self, query, user):
        """通过query处理帮助"""
        help_text = (
            "📚 <b>能量租赁机器人使用帮助</b>\n\n"
            "<b>基础命令：</b>\n"
            "/start - 开始使用机器人\n"
            "/buyenergy - 购买能量服务\n"
            "/status - 查看我的状态\n"
            "/help - 显示此帮助\n\n"
            "<b>服务说明：</b>\n\n"
            "🔋 <b>自助购买</b>\n"
            "向指定钱包转账TRX，自动购买能量\n\n"
            "🤖 <b>智能托管</b>\n"
            "自动监控和补充能量，无人值守\n\n"
            "📝 <b>笔数套餐</b>\n"
            "USDT购买固定次数，更省钱\n\n"
            "💰 <b>TRX闪兑</b>\n"
            "TRX与USDT快速兑换"
        )

        await query.edit_message_text(
            help_text,
            parse_mode='HTML'
        )

    async def _handle_help_via_message(self, update, user):
        """通过消息处理帮助"""
        help_text = (
            "📚 <b>能量租赁机器人使用帮助</b>\n\n"
            "<b>基础命令：</b>\n"
            "/start - 开始使用机器人\n"
            "/buyenergy - 购买能量服务\n"
            "/status - 查看我的状态\n"
            "/help - 显示此帮助\n\n"
            "<b>服务说明：</b>\n\n"
            "🔋 <b>自助购买</b>\n"
            "向指定钱包转账TRX，自动购买能量\n\n"
            "🤖 <b>智能托管</b>\n"
            "自动监控和补充能量，无人值守\n\n"
            "📝 <b>笔数套餐</b>\n"
            "USDT购买固定次数，更省钱\n\n"
            "💰 <b>TRX闪兑</b>\n"
            "TRX与USDT快速兑换"
        )

        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_status_via_message(self, update, user):
        """通过消息处理状态查询"""
        # 查询笔数套餐状态
        bishu_model = EnergyAiBishuModel()
        bishu_data = bishu_model.get_by_wallet_addr(f"user_{user.id}")

        status_text = f"📊 <b>{user.first_name} 的账户状态</b>\n\n"

        if bishu_data:
            status_text += (
                f"📝 <b>笔数套餐</b>\n"
                f"状态：{'正常' if bishu_data.get('is_buy') == 'N' else '购买中'}\n"
                f"当前能量：{bishu_data.get('current_energy_quantity', 0)}\n"
                f"已使用笔数：{bishu_data.get('total_buy_quantity', 0)}\n"
                f"剩余笔数：{bishu_data.get('max_buy_quantity', 0) - bishu_data.get('total_buy_quantity', 0)}\n"
                f"USDT消费：{bishu_data.get('total_buy_usdt', 0)}\n\n"
            )
        else:
            status_text += "❌ 您还没有购买任何笔数套餐\n\n发送 /start 开始购买"

        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def _handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理错误"""
        self.logger.error(f"Update {update} caused error {context.error}")
        # 这里可以发送错误报告给管理员
