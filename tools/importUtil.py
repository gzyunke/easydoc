# -*- coding:utf8 -*-

import requests
import random
import json
import os
import time
import sys
import logging
import argparse

logger = logging.getLogger('easydoc')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt="%m-%d %H:%M:%S")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# 请使用python2.x版本
# 从./src目录导入java后缀的文件，运行示例：
# python importUtil.py -d ./src -e java

# 请填写下面两个参数
branchId = '分支ID，在文档编辑页面，地址栏的最后一串字符串'
apikey = '在个人中心-APIKEY 获取你的apikey'

def getRandomStr(length=32):
    resultStr = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    for i in range(0, length):
        resultStr += random.choice(chars)
    return resultStr


# 计算缩进数量，包括空格和\t
def intendCount(content):
    count = 0
    for c in content:
        if c in ['\t', ' ']:
            count += 1
        else:
            break
    return count


def parseFile(file):
    lastIntendCount = -1
    startIndex = -1
    markdownIntentCount = -1
    docs = []
    doc = {}
    section = None
    parents = {}

    # logger.info('start parse file:%s', file.name)
    try:
        for index, line in enumerate(file):
            if startIndex == -1:
                startIndex = line.find('@easydoc api')
                if startIndex > 0:
                    doc = {}
            else:
                if '@end' in line:
                    startIndex = -1
                    if doc:
                        docs.append(doc)
                        logger.info('found %s: %s' % (doc.get('method', ''), doc.get('url')))
                    doc = {}
                    continue
                content = line[startIndex:]
                if section in ['headers', 'params', 'response']:
                    # 参数块必须要缩进
                    count = intendCount(content)
                    if count > 0:
                        # 第一次初始化
                        if not doc.get(section):
                            doc[section] = []
                            parents[count] = doc[section]
                            lastIntendCount = count

                        arr = content.split()
                        if len(arr) < 4:
                            logger.info('error on line:%s' % (index + 1))
                            continue

                        row = {
                            'id': getRandomStr(6),
                            'name': arr[0],
                            'type': arr[1],
                            'required': arr[2] == 'required',
                            'desc': arr[3].strip(),
                            'children': [],
                        }
                        if count > lastIntendCount:
                            parents[count] = parents[lastIntendCount][-1]['children']
                            lastIntendCount = count
                        parents[count].append(row)
                    else:
                        lastIntendCount = -1
                        section = None
                elif section == 'markdown':
                    count = intendCount(content)
                    if markdownIntentCount == -1:
                        markdownIntentCount = count
                    if count >= markdownIntentCount or (count == 0 and not content):
                        mkcontent = content[markdownIntentCount:]
                        if not mkcontent:
                            mkcontent += '\n'
                        if not doc.get('markdown'):
                            doc['markdown'] = ''
                        doc['markdown'] += mkcontent
                    else:
                        markdownIntentCount = -1
                        section = None

                arr = content.split(':', 1)
                if len(arr) >= 2:
                    key = arr[0].strip()
                    value = arr[1].strip()
                    if key in ['desc', 'method', 'title', 'url', 'mock']:
                        doc[key] = value
                        section = None
                        continue

                    if key in ['headers', 'params', 'response', 'markdown']:
                        section = key
                        continue
                    # logger.info('%s=%s' % (key, value))

        if not docs:
            return True

        data = {
            'branchId': branchId,
            'docs': docs,
            'apikey': apikey,
        }
        result = requests.post('https://easydoc.xyz/openapi/v1/updateDocs', json=data)
        result = json.loads(result.content)
        if result.get('code') < 0:
            logger.info('error: %s', result)
            return False
        else:
            logger.info('update success\n')
            time.sleep(1)
            return True
    except:
        logger.info('error or file:%s', file.name)
        sys.excepthook(*sys.exc_info())
        return False


def searchFiles(dir, ext):
    for filename in os.listdir(dir):
        path = os.path.join(dir, filename)
        extension = path.rsplit('.', 1)[-1]
        if os.path.isdir(path):
            searchFiles(path, ext)
        elif ext is None or extension == ext:
            with open(path, 'r') as file:
                if not parseFile(file):
                    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # -d 参数指定搜索目录，不指定则表示当前目录
    parser.add_argument("--dir", "-d", default='./', help='folder to search files')
    # -e 指定搜索的文件后缀，不指定则全部
    parser.add_argument("--ext", "-e", help='file extension, sample: java/py/php/lua')
    args = parser.parse_args()

    searchFiles(args.dir, args.ext)