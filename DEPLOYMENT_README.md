# 🚀 能量租赁机器人部署指南

## 📋 前置要求

### 1. 系统环境
- Python 3.11+
- MySQL 8.0+
- Linux/macOS/Windows

### 2. 申请必要服务
- **Telegram Bot Token**: 在 [@BotFather](https://t.me/botfather) 申请
- **TronGrid API Key**: 在 [TronGrid](https://www.trongrid.io/) 注册获取
- **MySQL数据库**: 本地安装或云数据库

## 🛠️ 部署步骤

### 步骤1: 克隆项目
```bash
git clone <repository-url>
cd energyRent
```

### 步骤2: 安装依赖
```bash
pip install -r requirements.txt
pip install mysql-connector-python
```

### 步骤3: 配置数据库
```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE energy_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 导入表结构
source database_schema.sql;

# 退出MySQL
exit;
```

### 步骤4: 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入真实配置
vim .env
```

**.env 文件配置示例:**
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=energy_bot
DB_USER=root
DB_PASSWORD=your_mysql_password

# TRON API配置
TRON_API_KEY_1=9fba5480-0c82-4553-acb1-63ffcd528e31
TRON_API_KEY_2=your_tron_api_key_2
TRON_API_KEY_3=your_tron_api_key_3

# Telegram配置
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=@yourbot
TELEGRAM_ADMIN_USERNAME=@admin
TELEGRAM_ADMIN_UID=123456789

# 钱包地址配置
ENERGY_RENT_WALLET=TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh
BISHA_WALLET=TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh
```

### 步骤5: 获取管理员UID
1. 在Telegram中搜索 `@userinfobot`
2. 发送任意消息，获取你的用户ID
3. 将ID填入 `.env` 文件的 `TELEGRAM_ADMIN_UID`

### 步骤6: 测试配置
```bash
python run_bot.py --test
```

### 步骤7: 启动机器人
```bash
python run_bot.py
```

## 💰 盈利配置

### 1. 能量闪租盈利设置

**修改 `config/config.py`:**
```python
ENERGY_RENT_CONFIG = {
    'prices': {
        'with_u': {'trx': 3.0, 'energy': 75000},      # 提高价格
        'without_u': {'trx': 6.0, 'energy': 150000}   # 提高价格
    },
    'profit_margin': 0.15,    # 15%利润率
    'platform_fee': 0.08      # 8%平台费用
}
```

### 2. 笔数套餐盈利设置

**修改 `config/config.py`:**
```python
BISHA_CONFIG = {
    'price_per_bishu': 5.0,  # 每笔5 TRX
    'energy_per_bishu': 131000,
}
```

### 3. 平台配置

**添加上游平台 (可选):**
```sql
-- 在数据库中插入平台信息
INSERT INTO energy_platform (platform_name, platform_balance, api_url, api_key, status, seq_sn)
VALUES ('nee.cc', 1000.00, 'https://api.nee.cc/v1/order', 'your_api_key', 0, 1);
```

## 🔧 高级配置

### 1. 数据库连接池
```python
# config/config.py 中的连接池配置
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="energy_pool",
    pool_size=10,  # 根据并发量调整
    pool_reset_session=True,
    host=DATABASE_CONFIG['host'],
    port=DATABASE_CONFIG['port'],
    database=DATABASE_CONFIG['database'],
    user=DATABASE_CONFIG['username'],
    password=DATABASE_CONFIG['password']
)
```

### 2. 日志配置
```python
LOG_CONFIG = {
    'level': 'INFO',
    'file': '/var/log/energy_bot.log',  # 修改日志路径
    'max_size': 50 * 1024 * 1024,       # 50MB
    'backup_count': 10
}
```

### 3. 监控配置
```python
MONITOR_CONFIG = {
    'alerts': {
        'low_balance_threshold': 500,     # 余额告警阈值
        'high_error_rate_threshold': 0.05  # 错误率告警阈值
    }
}
```

## 📊 监控和维护

### 1. 查看交易统计
```sql
-- 今日交易统计
SELECT
    COUNT(*) as total_orders,
    SUM(amount) as total_trx,
    SUM(energy_amount) as total_energy
FROM energy_wallet_trade_list
WHERE DATE(create_time) = CURDATE()
AND process_status = 9;

-- 用户统计
SELECT
    tg_uid,
    COUNT(*) as order_count,
    SUM(amount) as total_spent
FROM energy_wallet_trade_list
WHERE process_status = 9
GROUP BY tg_uid
ORDER BY total_spent DESC;
```

### 2. 平台余额监控
```sql
SELECT
    platform_name,
    platform_balance,
    status
FROM energy_platform
ORDER BY seq_sn;
```

### 3. 日志监控
```bash
# 查看实时日志
tail -f /tmp/energy_rental_bot.log

# 搜索错误日志
grep "ERROR" /tmp/energy_rental_bot.log
```

## 🚨 故障排除

### 1. 数据库连接失败
```
DB_CONNECT_ERROR: 获取数据库连接失败
```
**解决方案:**
- 检查MySQL服务是否运行
- 验证数据库配置是否正确
- 确认用户权限

### 2. API请求失败
```
HTTP_REQUEST_ERROR: 请求失败: 401 Client Error
```
**解决方案:**
- 检查TronGrid API Key是否有效
- 确认网络连接正常
- 查看API调用频率限制

### 3. Telegram消息发送失败
```
Error: BadRequest: Chat not found
```
**解决方案:**
- 确认用户已开始与机器人对话
- 检查chat_id是否正确
- 验证机器人Token有效性

## 🔒 安全建议

### 1. 环境变量保护
- 不要将 `.env` 文件提交到版本控制
- 使用强密码
- 定期更换API密钥

### 2. 钱包安全
- 使用硬件钱包存储私钥
- 定期备份数据库
- 监控异常交易

### 3. 服务器安全
- 使用防火墙限制端口访问
- 定期更新系统和依赖
- 监控服务器资源使用

## 📞 技术支持

如遇到问题，请：
1. 查看日志文件获取错误信息
2. 检查数据库连接和配置
3. 确认API服务状态
4. 查看本文档的故障排除部分

---

## 🎯 快速开始检查清单

- [ ] Python 3.11+ 已安装
- [ ] MySQL 8.0+ 已安装并运行
- [ ] Telegram Bot Token 已获取
- [ ] TronGrid API Key 已获取
- [ ] 数据库已创建并导入表结构
- [ ] .env 文件已正确配置
- [ ] 管理员UID已设置
- [ ] 测试通过 (`python run_bot.py --test`)
- [ ] 机器人成功启动

**恭喜！你的能量租赁机器人现在已经准备就绪，可以开始盈利了！🚀**
