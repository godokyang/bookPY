#coding=utf8
import requests
import csv
import random
import time
import socket
import os
import re
import json
import subprocess
from lxml import etree

def getContent(url,header = None,path = None,keywords = None,Referer = None):
    if header!=None:
        headers = header
    else:
        headers={
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Host":"www.zxcs8.com",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
        }

    fullPath = url
    if path != None:
        fullPath = url + path

    if Referer!=None:
        headers['Referer'] = Referer
    elif 'Referer' in headers:
        del headers['Referer']

    timeout = random.choice(range(30,60))

    while True:
        try:
            rep = requests.get(fullPath,headers=headers,params=keywords,timeout=timeout)
            rep.encoding = "utf-8"
            break

        except socket.timeout as e:
            print("超时:", e)
            time.sleep(random.choice(range(8,15)))

        except socket.error as e:
            print( '错误:', e)
            time.sleep(random.choice(range(20, 60)))

    return rep.text

def getMainPage():
    mainPageHTML = getContent(init_url)

    try:
        mainPageXpath = etree.HTML(mainPageHTML.lower())
        mainURLs = mainPageXpath.xpath('//div[@class="title"]/a[@class="more" and contains(@href,"http://www.zxcs8.com/sort/")]/@href')
        mainTypes = mainPageXpath.xpath('//div[@class="title"]/a[@class="more" and contains(@href,"http://www.zxcs8.com/sort/")]/preceding-sibling::strong/text()')
        print("mainURLs: " + str(mainURLs))
        print("mainTypes: " + str(mainTypes))
    except Exception as e:
        time.sleep(random.choice(range(8,15)))
        print("主页拉取失败--重试： " + str(e))


    for index,value in enumerate(mainURLs):
        # print(str(value))
        # if index == 0:
        dUrls = getBooksURL(value)
        print("dUrls ：" + str(dUrls))
        thisPath = init_download_path + "/download/" + mainTypes[index]
        if not os.path.exists(thisPath):
            print("it is in")
            rem = subprocess.call('mkdir'+" "+thisPath,shell=True)

        for dUrl in dUrls:
            res = subprocess.call('wget -P '+thisPath+" "+dUrl,shell=True)




def getBooksURL(mainURL):

    def setBookId(values):
        for index,value in enumerate(values):
            values[index] = re.sub("http://www.zxcs8.com/post/","http://www.zxcs8.com/download.php?id=",value)

    downloadAddress = []

    groupHeader = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control":"max-age=0",
        "Connection":"keep-alive",
        "Host":"www.zxcs8.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
    }

    downloadHeader = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control":"max-age=0",
        "Connection":"keep-alive",
        "Host":"www.zxcs8.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
    }

    booksGroup = getContent(mainURL,groupHeader)
    groupsURLs = []
    singleBookInfo = []
    try:
        groupXpath = etree.HTML(booksGroup.lower())
        groupURLs = groupXpath.xpath(u'//div[@id="pagenavi"]/a[@title="尾页"]/@href')
        singleBookInfo = groupXpath.xpath('//dl[@id="plist"]/dt/a[contains(@href,"http://www.zxcs8.com/")]/@href')
        setBookId(singleBookInfo)

        for value in range(2, int(re.sub(str(mainURL)+"/page/","",groupURLs[0]))):
        # for value in range(2,3):
            groupsURLs.append(str(mainURL)+"/page/"+str(value))
    except Exception as e:
        time.sleep(random.choice(range(15,32)))
        print("书籍list拉取失败1--重试： " + str(e))

    for indexUrl in groupsURLs:
        try:
            booksData = getContent(indexUrl,groupHeader)
            bookXpath =  etree.HTML(booksData.lower())
            singleBookInfo2 = bookXpath.xpath('//dl[@id="plist"]/dt/a[contains(@href,"http://www.zxcs8.com/")]/@href')
            setBookId(singleBookInfo2)
            singleBookInfo = singleBookInfo + singleBookInfo2
            print("listGetRate: ",str(indexUrl))
        except Exception as e:
            print("书籍list拉取失败2: " + str(e))


    for index,value in enumerate(singleBookInfo):
        # if index == 0 or index == 1:
        try:
            downloadData = getContent(value,downloadHeader)
            downloadXpath = etree.HTML(downloadData.lower())
            downloadUrl = downloadXpath.xpath('//span[@class="downfile"]/a/@href')[0]
            downloadAddress.append(downloadUrl)
            print("downloadRate: ",str(index),str(value))
        except Exception as e:
            print("下载信息获取失败：" + str(value) + "--" + str(e))

    return downloadAddress

def mainSpider():
    getMainPage()

if __name__ == '__main__':
    init_download_path = "/opt/download"
    init_url = 'http://www.zxcs8.com'
    init_path = ''
    init_keywords = {
    }
    mainSpider()
