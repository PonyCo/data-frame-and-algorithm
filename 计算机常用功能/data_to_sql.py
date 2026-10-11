import pandas as pd
import pymysql
from sqlalchemy import create_engine
import os


# ================================
# MySQL 配置
# ================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "242600"


# ================================
# 1. 输入数据库名称
# ================================

database_name = input(
    "请输入你要使用的数据库名称: "
)


print(
    "✅ 数据库名称:",
    database_name
)



# ================================
# 2. 创建数据库
# ================================

try:

    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )

    cursor = conn.cursor()


    cursor.execute(
        f"""
        CREATE DATABASE IF NOT EXISTS `{database_name}`
        CHARACTER SET utf8mb4
        """
    )


    conn.commit()

    cursor.close()
    conn.close()


    print(
        "✅ 数据库准备完成"
    )


except Exception as e:

    print(
        "❌ 创建数据库失败:",
        e
    )

    exit()



# ================================
# 3. 输入文件路径
# ================================


file_path = input(
    "请输入文件路径: "
)


# 去掉用户可能输入的引号

file_path = file_path.replace(
    '"',
    ''
)


if not os.path.exists(file_path):

    print(
        "❌ 文件不存在"
    )

    exit()



# ================================
# 4. 输入表名
# ================================


table_name = input(
    "请输入MySQL表名: "
)



# ================================
# 5. 自动读取文件
# ================================


print(
    "\n📥 正在读取文件:",
    file_path
)


extension = os.path.splitext(
    file_path
)[1].lower()



df = None



# -------- CSV --------

if extension == ".csv":


    encoding_list = [
        "gb18030",
        "gbk",
        "gb2312",
        "utf-8-sig",
        "utf-8"
    ]


    for enc in encoding_list:

        try:

            print(
                "尝试编码:",
                enc
            )


            df = pd.read_csv(
                file_path,
                encoding=enc,
                low_memory=False
            )


            print(
                "✅ CSV读取成功:",
                enc
            )


            break


        except Exception:

            pass



# -------- Excel --------

elif extension in [
    ".xlsx",
    ".xls"
]:


    try:

        df = pd.read_excel(
            file_path
        )


        print(
            "✅ Excel读取成功"
        )


    except Exception as e:

        print(
            "❌ Excel读取失败:",
            e
        )



else:

    print(
        "❌ 不支持的文件格式"
    )

    exit()



if df is None:

    print(
        "❌ 文件读取失败"
    )

    exit()



# ================================
# 6. 查看数据
# ================================


print(
    "\n数据量:",
    df.shape
)


print(
    "\n字段:"
)

print(
    df.columns.tolist()
)



print(
    "\n前5行:"
)

print(
    df.head()
)



# ================================
# 7. 导入MySQL
# ================================


engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{database_name}?charset=utf8mb4"
)



try:


    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False
    )


    print(
        "\n🎉 导入MySQL成功!"
    )


except Exception as e:

    print(
        "❌ MySQL导入失败:",
        e
    )

    exit()



# ================================
# 8. 查询验证
# ================================


try:


    result = pd.read_sql(
        f"""
        SELECT *
        FROM `{table_name}`
        LIMIT 5
        """,
        engine
    )


    print(
        "\n========== 数据库预览 =========="
    )

    print(result)



except Exception as e:

    print(
        "查询失败:",
        e
    )



print(
    "\n🔌 程序结束"
)