# -*- coding:utf8 -*-
# 本脚本用来扫描代码中的注释，自动生成 API 文档到易文档
import requests
import json
import os
import time
import hashlib
import logging
import argparse
import sys
if sys.version > '3':
    PY3 = True
else:
    PY3 = False

# 从./src目录导入java后缀的文件，运行示例：
# python importUtil.py -d ./src -e java

# 请填写下面两个参数
branchId = '分支ID，在文档编辑页面，地址栏的最后一串字符串'
apikey = '在个人中心-APIKEY 获取你的apikey'

# 接口地址
url = 'https://easydoc.xyz/openapi/v1/updateDocs'


# 变更记录文件，记录哪些文件已经更新过，提高扫描和更新速度
# 如果你需要全量更新，删除这个文件就可以了
upLogFilename = './easydoc.uplog'

logger = logging.getLogger('easydoc')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt="%m-%d %H:%M:%S")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

def parseFile(file):
    lastIntendCount = -1
    startIndex = -1
    markdownIntentCount = -1
    docs = []
    doc = {}
    section = None
    parents = {}
    global upLogDict
    docsMD5 = {}

    # logger.info('start parse file:%s', file.name)
    try:
        for index, line in enumerate(file):
            if PY3:
                line = line.decode()
            if startIndex == -1:
                startIndex = line.find('@easydoc api')
                if startIndex > 0:
                    doc = {}
            else:
                if '@end' in line:
                    startIndex = -1
                    if doc:
                        logger.info('found %s: %s' % (doc.get('method', ''), doc.get('url')))
                        dockey = '%s.%s.%s' % (branchId, doc.get('method', ''), doc.get('url', ''))
                        oldmd5 = upLogDict.get('docsMD5', {}).get(dockey)
                        newmd5 = md5hash(json.dumps(doc))
                        if oldmd5 != newmd5:
                            docs.append(doc)
                            docsMD5[dockey] = newmd5
                        else:
                            logger.info('no change, pass')
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
        result = requests.post(url, json=data, timeout=5)
        try:
            result = json.loads(result.content)
        except:
            logger.info('error:%s', result.content)
            return False
            
        if result.get('code') < 0:
            logger.info('error: %s', result)
            return False
        else:
            logger.info('update success\n')
            # 更新成功后记录这些文档的MD5值，以便下次能识别哪些接口需要更新
            updateDocsMD5(docsMD5)
            # 这里休息一下，避免接口请求太频繁限制
            time.sleep(1)
            return True
    except:
        logger.info('error or file:%s', file.name)
        sys.excepthook(*sys.exc_info())
        return False

def md5hash(string):
    m = hashlib.md5()
    if PY3:
        string = string.encode('utf8')
    m.update(string)
    return m.hexdigest()


# 计算缩进数量，包括空格和\t
def intendCount(content):
    count = 0
    for c in content:
        if c in ['\t', ' ']:
            count += 1
        else:
            break
    return count


upLogDict = {}
def updateDocsMD5(docsMD5):
    global upLogDict
    upLogDict['docsMD5'].update(docsMD5)
    f = open(upLogFilename, 'w')
    f.write(json.dumps(upLogDict))
    f.close()


def searchFiles(dir, ext):
    for filename in os.listdir(dir):
        path = os.path.join(dir, filename)
        extension = path.rsplit('.', 1)[-1]
        if os.path.isdir(path):
            searchFiles(path, ext)
        elif ext is None or extension == ext:
            with open(path, 'rb') as file:
                # 根据修改时间，判断是否需要扫描
                modifyTs = int(os.path.getmtime(path))
                lastModifyTs = upLogDict.get('fileUpTs', {}).get(path)
                if modifyTs == lastModifyTs:
                    logger.info('file:%s not change, pass', path)
                    continue
                if not parseFile(file):
                    # 更新失败，结束程序
                    return
                # 成功之后记住上次修改时间
                upLogDict['fileUpTs'][path] = modifyTs


# 读取更新记录，分两个部分：文件和API，没有修改过的文件、API不会更新，提高扫描和更新速度
# 文件是根据修改时间判断是否需要重新扫描
# API 是根据md5值判断是否有修改
def readUpLog():
    global upLogDict
    if not os.path.exists(upLogFilename):
        upLogDict = {'fileUpTs': {}, 'docsMD5': {}}
        return
    with open(upLogFilename, 'r') as file:
        content = file.read()
        try:
            upLogDict = json.loads(content)
            if upLogDict.get('fileUpTs') is None:
                upLogDict['fileUpTs'] = {}
            if upLogDict.get('docsMD5') is None:
                upLogDict['docsMD5'] = {}
        except:
            upLogDict = {'fileUpTs': {}, 'docsMD5': {}}


# 运行示例：python xxxx.py -d ./src -e java
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # -d 参数指定搜索目录，不指定则表示当前目录
    parser.add_argument("--dir", "-d", default='./', help='folder to search files')
    # -e 指定搜索的文件后缀，不指定则全部
    parser.add_argument("--ext", "-e", help='file extension, sample: java/py/php/lua')
    args = parser.parse_args()

    readUpLog()
    searchFiles(args.dir, args.ext)

    # 写入缓存文件
    f = open(upLogFilename, 'w')
    f.write(json.dumps(upLogDict))
    f.close()
    logger.info('search done')