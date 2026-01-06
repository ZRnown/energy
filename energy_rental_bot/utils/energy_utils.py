"""
能量租赁机器人工具函数
"""

import os
import time
import math
import requests
import random
from datetime import datetime
import logging
import mysql.connector
from mysql.connector import pooling
# 导入配置
from energy_rental_bot.config.config import TRON_CONFIG, DATABASE_CONFIG


class EnergyUtils:
    """工具函数集合"""

    @staticmethod
    def calculate_amount(amount, decimals):
        """计算金额（处理小数位）"""
        return amount / math.pow(10, decimals)

    @staticmethod
    def thirteen_time():
        """获取十三位时间戳"""
        return int(time.time() * 1000)

    @staticmethod
    def now_date():
        """获取当前日期时间"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def send_http_request(url, data=None, headers=None, method='GET'):
        """发送HTTP请求"""
        try:
            if headers is None:
                headers = {}

            # 设置 User-Agent 避免部分API拦截
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'

            if data is not None:
                if method.upper() == 'POST':
                    if isinstance(data, dict):
                        response = requests.post(url, json=data, headers=headers, timeout=10)
                    else:
                        response = requests.post(url, data=data, headers=headers, timeout=10)
                else:
                    response = requests.get(url, params=data, headers=headers, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)

            # 只有 4xx 和 5xx 抛出异常
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            # 记录具体的 HTTP 错误，但不一定要崩溃
            EnergyUtils.log('HTTP_ERROR', f'API请求返回错误: {e.response.status_code} - {url}')
            return None
        except Exception as e:
            EnergyUtils.log('HTTP_REQUEST_ERROR', f'请求失败: {str(e)}')
            return None

    @staticmethod
    def get_random_api_key(key_type):
        """获取随机API密钥"""
        # 从环境变量获取 API Key
        if key_type == 'tronapikey':
            keys = [
                os.getenv('TRON_API_KEY_1'),
                os.getenv('TRON_API_KEY_2'),
                os.getenv('TRON_API_KEY_3')
            ]
        elif key_type == 'gridapikey':
            keys = [
                os.getenv('GRID_API_KEY_1'),
                os.getenv('GRID_API_KEY_2'),
                os.getenv('GRID_API_KEY_3')
            ]
        else:
            return None

        # 过滤掉空值和无效的key
        valid_keys = [k for k in keys if k and k not in ['key1', 'key2', 'key3', 'your_tron_api_key_1', 'your_tron_api_key_2', 'your_tron_api_key_3']]

        if valid_keys:
            return random.choice(valid_keys)

        # 如果没有有效key，返回None，让调用方处理
        return None

    @staticmethod
    def log(title, message):
        """日志记录"""
        logging.basicConfig(
            filename='/tmp/energy_log.txt',
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        log_message = f'[{title}] {message}'
        logging.info(log_message)
        print(log_message)

    @staticmethod
    def format_address(address):
        """地址格式化显示"""
        if len(address) >= 16:
            return address[:8] + '****' + address[-8:]
        return address

    @staticmethod
    def setup_logging():
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/energy_rental_bot.log'),
                logging.StreamHandler()
            ]
        )


# 协程并发类 (模拟异步并发)
class Concurrent:
    """协程并发执行类"""

    def __init__(self, limit):
        self.limit = limit
        self.tasks = []

    def create(self, callable_func):
        """创建协程任务"""
        # 在Python中，这里应该使用asyncio
        # 这里暂时使用同步执行作为模拟
        try:
            callable_func()
        except Exception as e:
            EnergyUtils.log('CONCURRENT_ERROR', f'协程执行异常: {str(e)}')


# RSA加密服务类 (模拟)
class RsaServices:
    """RSA加密服务"""

    @staticmethod
    def private_decrypt(encrypted_data):
        """私钥解密"""
        # 这里应该实现真实的RSA解密
        # 暂时返回原文作为模拟
        return encrypted_data


# 创建全局连接池

db_pool = mysql.connector.pooling.MySQLConnectionPool(

    pool_name="energy_pool",

    pool_size=10,  # 增加连接池大小

    pool_reset_session=True,

    host=DATABASE_CONFIG['host'],

    port=DATABASE_CONFIG['port'],

    database=DATABASE_CONFIG['database'],

    user=DATABASE_CONFIG['username'],

    password=DATABASE_CONFIG['password'],

    connection_timeout=30,  # 添加连接超时

    autocommit=True  # 自动提交

)



class DatabaseConnection:

    """真实数据库连接类"""



    def __init__(self, config=None):

        self.connection = None

        self.cursor = None



    def get_connection(self):

        try:

            self.connection = db_pool.get_connection()

            return self.connection

        except Exception as e:

            EnergyUtils.log('DB_CONNECT_ERROR', f"获取数据库连接失败: {str(e)}")

            return None



    def query(self, sql, params=None):

        """执行查询"""

        conn = None

        cursor = None

        try:

            conn = self.get_connection()

            if not conn:

                return []



            cursor = conn.cursor(dictionary=True)

            if params:

                cursor.execute(sql, params)

            else:

                cursor.execute(sql)



            result = cursor.fetchall()

            return result

        except Exception as e:

            EnergyUtils.log('DATABASE_QUERY_ERROR', f'SQL: {sql} | Error: {str(e)}')

            return []

        finally:

            # 确保资源被释放

            if cursor:

                try:

                    cursor.close()

                except:

                    pass

            if conn:

                try:

                    conn.close()

                except:

                    pass



    def execute(self, sql, params=None):

        """执行更新/插入"""

        conn = None

        cursor = None

        try:

            conn = self.get_connection()

            if not conn:

                return 0



            cursor = conn.cursor()

            if params:

                cursor.execute(sql, params)

            else:

                cursor.execute(sql)



            # 注意：由于设置了autocommit=True，这里不需要手动commit

            last_id = cursor.lastrowid

            affected_rows = cursor.rowcount



            # 如果是插入，返回自增ID，否则返回影响行数

            return last_id if last_id else affected_rows

        except Exception as e:

            EnergyUtils.log('DATABASE_EXECUTE_ERROR', f'SQL: {sql} | Error: {str(e)}')

            return 0

        finally:

            # 确保资源被释放

            if cursor:

                try:

                    cursor.close()

                except:

                    pass

            if conn:

                try:

                    conn.close()

                except:

                    pass



    # 保持向后兼容的方法

    def connect(self):

        """连接数据库（向后兼容）"""

        return self.get_connection()



    def close(self):

        """关闭连接（向后兼容）"""

        if self.connection:

            try:

                self.connection.close()

            except:

                pass

            self.connection = None
