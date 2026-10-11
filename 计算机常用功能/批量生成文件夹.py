import os
start = 1#带数字
end = 14
parent_dir = r'F:\pythonproject\2026新生培训附件材料new\培训_xk'

os.makedirs(parent_dir, exist_ok=True)

for i in range(start, end + 1):
    folder_name = f'task {i}'
    folder_path = os.path.join(parent_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    print(f'已创建：{folder_path}')