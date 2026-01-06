# ⚙️ 能量租赁机器人配置指南

## 📋 基础设置

### 1. 环境变量配置 (.env 文件)

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=energy_bot
DB_USER=root
DB_PASSWORD=your_password

# TRON API配置 (获取真实API Key)
TRON_API_KEY_1=9fba5480-0c82-4553-acb1-63ffcd528e31  # TronGrid API Key
TRON_API_KEY_2=your_tron_api_key_2
TRON_API_KEY_3=your_tron_api_key_3

# Telegram配置
TELEGRAM_BOT_TOKEN=8569104536:AAFC8J3qdP-JfXMz0PieDTJTcelLg3feZOs  # Bot Token
TELEGRAM_BOT_USERNAME=@nengliangRent_bot
TELEGRAM_ADMIN_USERNAME=@momo99884

# 钱包地址配置
ENERGY_RENT_WALLET=TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh  # 能量闪租接收地址
BISHA_WALLET=TWHNEdk5o5qt84bSbFQKqK8LxVxp5wKxgh         # 笔数套餐接收地址
```

## 💰 盈利设置

### 1. 能量闪租盈利模式

**当前配置 (config.py):**
```python
ENERGY_RENT_CONFIG = {
    # 能量价格配置 (TRX -> 能量)
    'prices': {
        'with_u': {'trx': 2.5, 'energy': 65000},    # 对方有U的情况
        'without_u': {'trx': 5.0, 'energy': 131000}  # 对方无U的情况
    },

    # 盈利配置
    'profit_margin': 0.1,          # 利润率 10%
    'platform_fee': 0.05           # 平台手续费 5%
}
```

**盈利计算示例:**
- 用户支付 2.5 TRX 获得 65000 能量
- 实际成本: 2.5 TRX × (1 - 0.1 - 0.05) = 2.0 TRX
- 利润: 2.5 - 2.0 = 0.5 TRX (20%利润率)

### 2. 笔数套餐盈利模式

**当前配置:**
```python
BISHA_CONFIG = {
    'price_per_bishu': 4.4,        # 每笔4.4 TRX
    'energy_per_bishu': 131000,    # 每笔提供131000能量
    # ... 其他配置
}
```

**盈利机制:**
- 按笔收费，无时间限制
- 自动能量补充机制
- 超时扣费保护

## 🏦 钱包地址设置

### 1. 能量闪租地址
```bash
ENERGY_RENT_WALLET=你的TRON钱包地址
```
- 用于接收能量闪租的TRX支付
- 机器人会自动监控此地址的交易

### 2. 笔数套餐地址
```bash
BISHA_WALLET=你的TRON钱包地址
```
- 用于接收笔数套餐的TRX支付
- 支持USDT自动转账触发能量补充

## 🔧 高级配置

### 1. 价格调整

**修改能量价格:**
```python
ENERGY_RENT_CONFIG = {
    'prices': {
        'with_u': {'trx': 3.0, 'energy': 75000},    # 提高价格
        'without_u': {'trx': 6.0, 'energy': 150000} # 提高价格
    }
}
```

**修改笔数价格:**
```python
BISHA_CONFIG = {
    'price_per_bishu': 5.0,  # 从4.4提高到5.0
}
```

### 2. 盈利率调整

**增加利润率:**
```python
ENERGY_RENT_CONFIG = {
    'profit_margin': 0.15,    # 从10%提高到15%
    'platform_fee': 0.08      # 从5%提高到8%
}
```

### 3. 限制调整

**修改单笔限额:**
```python
ENERGY_RENT_CONFIG = {
    'max_single_trx': 100.0,     # 从50提高到100
    'max_energy': 2600000,       # 对应调整最大能量
}
```

## 🚀 部署步骤

1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入真实配置
   ```

2. **获取API Key**
   - TronGrid: https://www.trongrid.io/
   - Telegram Bot Token: @BotFather

3. **设置钱包地址**
   - 创建TRON钱包
   - 在.env中配置接收地址

4. **启动机器人**
   ```bash
   python run_bot.py
   ```

## 📊 盈利监控

机器人会自动记录所有交易数据，你可以通过数据库查询盈利情况：

```sql
-- 查看总盈利
SELECT
    SUM(profit_trx) as total_profit,
    COUNT(*) as total_orders
FROM energy_orders
WHERE status = 'completed';

-- 按日期统计
SELECT
    DATE(created_at) as date,
    SUM(profit_trx) as daily_profit,
    COUNT(*) as daily_orders
FROM energy_orders
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```
