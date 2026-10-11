import pymysql
#连接MySQL()
conn = pymysql.connect (host='localhost', port=3306, user='root', passwd='242600', charset="utf8")
cursor = conn.cursor ()
#1.查看数据库
#发送指令
cursor.execute("show databases")
#获取指令的结果
result = cursor.fetchall()
print(result)
#打印结果示例：(('info('mysql',), ('performance_schema',), ('sys',))

#2.创建数据库
#发送指令
cursor.execute("create database db3 default charset utf8 collate utf8_general_ci")
conn.commit()

#3.查看数据库
#发送指令
cursor.execute("show databases")
#获取指令的结果
result = cursor.fetchall()
print (result)
# 打印结果示例：(('information schema('db3',), ('mysql',), ('performance_schema('sys',))

#4.删除数据库
#发送指令
cursor.execute("drop database db3")
conn.commit ()

#5.查看数据库
#发送指令
cursor.execute("show databases")
#获取指令的结果
result = cursor.fetchall()
print(result)
#打印结果示例：(('information schema',), ('mysql',), ('performance schema',), ('sys',))

#6.关闭连接
cursor.close()
conn.close()