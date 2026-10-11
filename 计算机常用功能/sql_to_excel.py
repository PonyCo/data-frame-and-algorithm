import pandas as pd
import pymysql
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")#跳出userwarning警告

# ================== 数据库连接配置 ==================
db_config = {
    'host': 'localhost',  # 数据库地址
    'user': 'root',  # 数据库用户名
    'password': '242600',  # 数据库密码
    'database': 'trafficdb',  # 需要导出的数据库名（请根据你的实际情况替换）
    'charset': 'utf8mb4'
}

# ================== 导出配置 ==================
# 要导出的表名（请根据你的实际情况替换）
table_name = 'RawTrafficData'
# 导出文件的完整路径（示例：F:/traffic_data_export.xlsx）
output_file = 'F:/sql表转化为excel/traffic_data_export.xlsx'

try:
    # 1. 建立数据库连接
    conn = pymysql.connect(**db_config)

    # 2. 使用pandas读取整个表的数据
    #   这里会将整个表的数据加载到DataFrame中，如果数据量极大（数百万行），请考虑使用分块读取。
    query = f"SELECT * FROM `{table_name}`"
    df = pd.read_sql(query, conn)

    # 3. 将DataFrame导出为Excel文件
    df.to_excel(output_file, index=False, engine='openpyxl')

    print(f"✅ 成功导出！文件已保存至：{output_file}")
    print(f"📊 共导出了 {len(df)} 行数据。")

except Exception as e:
    print(f"❌ 导出过程中出现错误：{e}")
finally:
    # 4. 关闭数据库连接
    if conn:
        conn.close()