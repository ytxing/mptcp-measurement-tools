import os
import argparse
import subprocess

parser = argparse.ArgumentParser(description = "server create directory or file")
parser.add_argument("-f", "--file", help = "filename")
parser.add_argument("-d", "--directory", help = "directory name")
args = parser.parse_args()

#创建文件夹并避免目录重名
def checkDirectoryExist(directory):
	if os.path.exists(directory):
		if not os.path.isdir(directory):
			raise Exception(directory + "is a existing file")
		else:
			os.makedirs(directory)

#创建文件并避免文件重名
def checkFileExist(fileName, path):
	file = os.path.join(fileName, path)
	if not os.access(file, os.F_OK):
		os.mknod(file)

if __name__ == "__main__":
	if args.directory and args.file:
		checkFileExist(args.file, args.directory)
	elif args.directory:
		checkDirectoryExist(args.directory)


