#!/bin/bash
# 演示配置文件 - 设置测试环境变量

export TELEGRAM_BOT_TOKEN="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="energy_bot"
export DB_USER="root"
export DB_PASSWORD="password"

# 可选配置
export TELEGRAM_ADMIN_UID="123456789"

echo "演示环境变量已设置"
echo "TELEGRAM_BOT_TOKEN: $TELEGRAM_BOT_TOKEN"
echo "DB_HOST: $DB_HOST"
echo "DB_NAME: $DB_NAME"
