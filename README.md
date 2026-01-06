# 能量租赁机器人 (Python版)

基于Python重写的能量租赁机器人系统，支持TRON网络能量租赁和Telegram机器人通知功能。

## 📁 项目结构

```
energy_rental_bot/
├── config/                 # 配置文件
│   ├── config.py          # 主要配置
│   └── __init__.py
├── controllers/            # 控制器层 - API接口处理
│   ├── energy_controller.py
│   └── __init__.py
├── models/                 # 模型层 - 数据库操作
│   ├── base_model.py      # 基础模型
│   ├── energy_models.py   # 能量相关模型
│   └── __init__.py
├── services/               # 服务层 - 业务逻辑处理
│   ├── energy_services.py
│   └── __init__.py
├── tasks/                  # 任务层 - 定时任务执行
│   ├── handle_energy_order_task.py
│   ├── get_energy_wallet_trx_trade_task.py
│   ├── get_ai_trusteeship_wallet_resource_task.py
│   ├── handle_ai_energy_order_task.py
│   ├── send_energy_tg_message_task.py
│   └── __init__.py
├── utils/                  # 工具函数
│   ├── energy_utils.py
│   └── __init__.py
├── main.py                 # 主入口文件
└── __init__.py
```

## 🎯 核心功能

### 1. 自助能量购买
- 用户转账TRX到指定钱包
- 自动匹配套餐并下单
- 支持4个主流能量平台
- 实时Telegram通知

### 2. 智能托管
- 自动监控钱包能量余额
- 能量不足时自动补充
- 支持余额和次数限制
- 智能计算剩余额度

### 3. 笔数套餐
- USDT购买能量使用次数
- 自动监控和补充能量
- 按需购买，避免浪费
- 详细的使用统计

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd energy-rental-bot

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库和API密钥
```

### 2. 配置数据库

创建MySQL数据库并导入表结构：

```sql
-- 数据库表结构请参考项目文档
CREATE DATABASE energy_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

```bash
# Telegram Bot配置 (必需)
export TELEGRAM_BOT_TOKEN=your_bot_token_here

# 数据库配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=energy_bot
export DB_USER=root
export DB_PASSWORD=password

# TRON API配置 (用于获取交易数据)
export TRON_API_KEY_1=your_tronscan_api_key_1
export TRON_API_KEY_2=your_tronscan_api_key_2
export TRON_API_KEY_3=your_tronscan_api_key_3

export GRID_API_KEY_1=your_trongrid_api_key_1
export GRID_API_KEY_2=your_trongrid_api_key_2
export GRID_API_KEY_3=your_trongrid_api_key_3

# 可选配置
export TELEGRAM_ADMIN_UID=123456789  # 管理员用户ID
export LOG_LEVEL=INFO
```

### 4. 启动机器人

#### 直接启动
```bash
python run_bot.py
```

#### 测试模式 (检查配置)
```bash
python run_bot.py --test
```

#### 详细输出
```bash
python run_bot.py --verbose
```

### 5. 使用机器人

#### Telegram Bot 交互

启动后，用户可以通过 Telegram 与机器人交互：

1. **发送 `/start`** 开始使用
2. **发送 `/buyenergy`** 选择购买服务
3. **发送 `/status`** 查看账户状态
4. **发送 `/help`** 获取帮助
5. **发送 `/admin`** 管理员功能（需要管理员权限）

#### 主要功能

**🔋 能量闪租**
- 向指定钱包转账TRX自动购买能量
- 支持多种套餐和实时到账

**🤖 智能托管**
- 自动监控钱包能量余额
- 能量不足时自动补充
- 支持余额和次数限制

**📝 笔数套餐**
- USDT购买固定次数的能量使用权
- 按需使用，避免浪费

**💰 TRX闪兑**
- TRX与USDT快速兑换服务
- 便捷的交易功能

### 6. 后台任务

机器人会自动运行以下后台任务：

- **每分钟**: 获取TRX交易数据、处理能量订单、发送通知
- **每10分钟**: 检查钱包资源、处理AI能量订单

无需手动配置定时任务，机器人会自动管理。

## 🏗️ 架构说明

### 控制器层 (Controller)
- 处理API请求和回调
- `TrongasIoController` - 处理笔数能量回调通知

### 服务层 (Service)
- 封装业务逻辑
- `EnergyWalletServices` - 钱包基础服务
- `EnergyWalletTradeTrxServices` - TRX交易处理
- `EnergyWalletTradeUsdtServices` - USDT交易处理

### 任务层 (Task)
- 定时任务执行
- `HandleEnergyOrderTask` - 处理能量订单
- `HandleAiEnergyOrderTask` - AI智能订单处理
- `GetEnergyWalletTrxTradeTask` - 获取TRX交易
- `SendEnergyTgMessageTask` - 消息通知

### 模型层 (Model)
- 数据库操作封装
- `EnergyAiBishuModel` - 笔数套餐模型
- `EnergyAiTrusteeshipModel` - 智能托管模型
- `EnergyPlatformModel` - 平台配置模型

### 工具层 (Utils)
- 通用工具函数
- `EnergyUtils` - 基础工具类
- `DatabaseConnection` - 数据库连接
- `Concurrent` - 协程并发处理

## 📊 数据库表结构

### 核心表

- `energy_platform_bot` - 能量平台机器人配置
- `energy_platform` - 能量平台配置
- `energy_platform_package` - 能量套餐配置
- `energy_wallet_trade_list` - 钱包交易记录
- `energy_platform_order` - 平台订单记录
- `energy_ai_trusteeship` - 智能托管配置
- `energy_ai_bishu` - 笔数套餐配置

## 🔧 配置说明

### 平台支持

1. **nee.cc** - 支持能量租赁
2. **RentEnergysBot** - 机器人能量服务
3. **自己质押** - 自托管质押
4. **trongas.io** - 第三方能量平台

### 通知渠道

- Telegram机器人通知
- 支持自定义键盘和链接
- 多种消息模板

## ⚠️ 注意事项

### 安全注意事项

1. **API密钥安全**
   - 使用环境变量存储密钥
   - 定期轮换API密钥
   - 限制API调用频率

2. **数据库安全**
   - 使用强密码
   - 定期备份数据
   - 限制数据库访问权限

3. **交易安全**
   - 校验交易哈希唯一性
   - 实现交易金额验证
   - 添加黑名单过滤机制

### 性能优化

1. **并发处理**
   - 使用协程提高并发性能
   - 合理设置并发数量
   - 实现请求频率限制

2. **缓存策略**
   - 缓存热点数据
   - 使用Redis缓存配置
   - 实现数据预加载

3. **监控告警**
   - 实时监控系统状态
   - 设置异常告警机制
   - 定期生成性能报告

## 🔄 迁移指南

### 从PHP版本迁移

1. **代码结构调整**
   - 将类方法转换为实例方法
   - 调整继承关系和接口
   - 重写静态方法调用

2. **语法转换**
   - PHP数组 → Python字典/列表
   - PHP对象 → Python类实例
   - 调整字符串处理和编码

3. **依赖管理**
   - 替换PHP扩展为Python包
   - 更新数据库连接方式
   - 重写HTTP请求处理

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   ```
   解决方案：检查数据库配置和网络连接
   ```

2. **API请求失败**
   ```
   解决方案：验证API密钥和网络配置
   ```

3. **Telegram通知失败**
   ```
   解决方案：检查机器人Token和权限设置
   ```

4. **任务执行异常**
   ```
   解决方案：查看日志文件定位问题
   ```

### 日志分析

系统会生成详细的日志文件：
- `/tmp/energy_rental_bot.log` - 主日志文件
- `/tmp/energy_log.txt` - 工具类日志

## 📈 扩展开发

### 添加新平台

1. 在 `config/config.py` 中添加平台配置
2. 在 `tasks/handle_energy_order_task.py` 中实现下单逻辑
3. 测试平台兼容性

### 添加新通知渠道

1. 扩展 `SendEnergyTgMessageTask` 类
2. 实现新的通知发送逻辑
3. 更新配置和模板

### 添加新监控指标

1. 扩展工具类添加监控方法
2. 实现数据收集和上报
3. 配置告警规则

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📞 联系方式

- 项目维护者: Energy Rental Bot Team
- 邮箱: energy@example.com

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！**
# energy
