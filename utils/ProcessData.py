import os
import sys

# 递归获取目录下所有文件
def getAllFiles(path):
    result = []
    for root, dirs, files in os.walk(path):
        for file in files:
            result.append(os.path.join(root, file))
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
    files = getAllFiles(dataDirectory)
    # 将文件名和文件内容分开
    fileNames = []
    fileContents = []
    for file in files:
        fileNames.append(file)
        fileContents.append(open(file, 'r').read())
    # 将文件名和文件内容写入文件
    for i in range(len(fileNames)):
        pass