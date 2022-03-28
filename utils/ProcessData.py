import os
import sys
import re
from typing import List

# 递归获取目录下所有文件
def getAllFiles(path):
    result = []
    for root, dirs, files in os.walk(path):
        print(root)
        files.sort()
        for file in files:
            result.append(os.path.join(root, file))
    return result

# 递归获取目录下名称中有关键字的文件
def getFilesByKeywords(path, keywords: List[str]):
    result = []
    for root, dirs, files in os.walk(path):
        print(root)
        for file in files:
            yes = True
            for keyword in keywords:
                if keyword in file:
                    continue
                else:
                    yes = False
                    break
            if yes:
                result.append(os.path.join(root, file))
    return result

# 获取文件中关键词后数据
def getDataByKeywords(file, keywords: List[str], data_key: str):
    with open(file, 'r') as f:
        lines = f.readlines()
    result = []
    for line in lines:
        yes = True
        for keyword in keywords:
            if keyword in line:
                continue
            else:
                yes = False
                break
        if yes:
            match = re.search(data_key + ':[0-9]+\.[0-9]+', line)
            if match:
                result.append(match.group())
    return result

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 ProcessData.py <data directory>")
        sys.exit(1)
    dataDirectory = sys.argv[1]
    if not os.path.isdir(dataDirectory):
        print("Error: data directory does not exist")
        sys.exit(1)
    # 获取目录下所有文件
    files = getFilesByKeywords(dataDirectory, ['bulk'])
    print(len(files))
    # 获取文件中关键词后数据
    # 'pause\(s\)' 'speed\(mbps\)'
    keys = ["speed\(mbps\)"]
    data = []
    for key in keys:
        for file in files:
            print(file)
            result = getDataByKeywords(file, ['Complete'], key)[0]
            data.append("{},{}".format(str(file).split('/')[-1].split('.')[0], re.search('[0-9]+\.[0-9]+', result).group()))

    header = 'file_name,' + ','.join([key.replace('\\', '') for key in keys])
    print(header)
    print('\n'.join(data))