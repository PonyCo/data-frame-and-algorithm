from bs4 import BeautifulSoup
import requests
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36 Core/1.116.505.400 QQBrowser/19.0.6404.400"
}

response = requests.get("https://www.zhipin.com/shanghai/?seoRefer=index", headers=headers)
if response.ok:
    print("请求成功")
else:
    print("请求失败")
content = response.text
soup = BeautifulSoup(content, "html.parser")
all_salary_list = soup.find_all("div", class_="sub-li-top")
data = []
for salary_list in all_salary_list:
    name = salary_list.find("p", class_="name").get_text()
    salary = salary_list.find("p", class_="salary").get_text()
    print(name, salary)
    data.append([name, salary])
if data:
    df = pd.DataFrame(data, columns=['职位名称', '薪资'])
    save_path = r"C:\Users\asus\Desktop\04_09\合并\职位信息_new.csv"

    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n已导出 {len(df)} 条数据到: {save_path}")
    print(df.head())
else:
    print("没有数据可以导出")