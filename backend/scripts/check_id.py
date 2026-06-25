import sys
import pymysql
sys.path.append('/app')
from app.config import settings

print("正在直接连接 MySQL 数据库...")

# 适配 Docker 内部的主机名
host = 'mysql' if settings.MYSQL_HOST == 'localhost' else settings.MYSQL_HOST

try:
    # 建立最底层的原生连接
    conn = pymysql.connect(
        host=host,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        port=int(settings.MYSQL_PORT)
    )
    
    with conn.cursor() as cursor:
        # 先自动找一下用户表叫什么名字（可能是 user 也可能是 users）
        cursor.execute("SHOW TABLES LIKE '%user%';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 没有找到用户表！")
        else:
            table_name = tables[0][0]
            # 直接提取数据
            cursor.execute(f"SELECT id, username, full_name FROM {table_name}")
            rows = cursor.fetchall()
            
            print("-" * 40)
            for row in rows:
                print(f"👉 真实ID: {row[0]}  |  登录账号: {row[1]}  |  姓名: {row[2]}")
            print("-" * 40)
            
except Exception as e:
    print(f"❌ 数据库查询失败: {e}")