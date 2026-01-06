"""
能量租赁机器人基础模型类
"""

from energy_rental_bot.utils.energy_utils import DatabaseConnection, EnergyUtils


class BaseModel:
    """基础模型类"""

    def __init__(self, table_name):
        self.table = table_name
        self.db = DatabaseConnection()

    def get_by_id(self, rid):
        """根据ID获取记录"""
        sql = f"SELECT * FROM {self.table} WHERE rid = %s"
        result = self.db.query(sql, [rid])
        return result[0] if result else None

    def update(self, rid, data):
        """更新记录"""
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        values = list(data.values()) + [rid]
        sql = f"UPDATE {self.table} SET {set_clause} WHERE rid = %s"
        return self.db.execute(sql, values)

    def insert(self, data):
        """插入记录"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = list(data.values())
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        return self.db.execute(sql, values)

    def delete(self, rid):
        """删除记录"""
        sql = f"DELETE FROM {self.table} WHERE rid = %s"
        return self.db.execute(sql, [rid])
