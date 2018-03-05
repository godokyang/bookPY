#encoding=UTF8
import requests
import csv
import random
import time
import socket
# import http.client
import os
import xlwt
import re
import json
from lxml import etree
from xlrd import open_workbook
from xlutils.copy import copy
from db.MySQLHelper import MySQLHelper

sheetExcel = ["书名/bookName","作者/writer","编号/bookId","字数/wordsNum","状态/status(1-更，2-完，3-宦官）","评分/grade","评价数/commentCount"]

commentSheet = ["id","书名/topicName","编号/topicId","内容/content","评论用户Id/fromUid","评论目标用户Id/toUid"]

def getContent(url,path = None,keywords = None,Referer = None,header = None):
    if header!=None:
        headers = header
    else:
        headers={
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Cookie":"hd=cc0a6305fa4efb366c98a155a905b1e267a00cae5728817ba08f4f9bc907f0dab5d46dcc64ce5f71fb56f6fca7c63e78;souser=e261a30f",
            "Host":"www.yousuu.com",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
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

        # except http.client.BadStatusLine as e:
        #     print( '5:', e)
        #     time.sleep(random.choice(range(30, 80)))
        #
        # except http.client.IncompleteRead as e:
        #     print( '6:', e)
        #     time.sleep(random.choice(range(5, 15)))

    return rep.text

def parseListHtml(htmlText):
    data = []
    page = etree.HTML(htmlText.lower()) #读取html解析成xpath支持的格式
    tag_a = page.xpath('//a[starts-with(@href,"/book/")]/@href') #获取page下面所有的a标href属性包含「/book/」开头的
    tag_a = delRepeat(tag_a)
    # if not tag_a or len(tag_a) == 0 or int(init_keywords['page']) >2:#抓到第二页停止，测试用
    if not tag_a or len(tag_a) == 0:
        print("tag_a: " + str(tag_a))
        return True
    else:
        for value in tag_a:
            # parseDataToLocal(value)
            parseDataToSql(value)

def parseDataToSql(bookPath):
    bookPageText = getContent(init_url, bookPath)
    book = etree.HTML(bookPageText.lower())

    bookData = {}
    bookName = book.xpath('//div[@class="col-sm-7"]/div[1]/span[1]/text()')[0]
    writer = book.xpath(u'//div[@class="media-body ys-bookmain"]/ul/li[starts-with(text(),"作者")]/a/text()')[0]
    bookId = re.sub("\D","",bookPath)
    wordsCount = re.sub("\D","",book.xpath(u'//div[@class="media-body ys-bookmain"]/ul/li[starts-with(text(),"字数")]/text()')[0])
    status = int(init_keywords["status"])
    grade = book.xpath('//div[@class="ys-book-averrate xs-align-left"]/span/text()')[1].strip()
    commentCount = re.sub("\D","",book.xpath('//div[@class="ys-book-averrate xs-align-left"]/small/text()')[0])

    typesXpath = book.xpath('//a[contains(@href,"/category/")]/@href')
    if typesXpath and len(typesXpath) > 0:
        bookType = re.sub("/category/","",book.xpath('//a[contains(@href,"/category/")]/@href')[0])
        typeName = book.xpath('//a[contains(@href,"/category/")]/text()')[0]
    else:
        bookType = "others"
        typeName = "其他"

    bookData['bookName'] = bookName
    bookData['writer'] = writer
    bookData['bookId'] = bookId
    bookData['wordsCount'] = wordsCount
    bookData['status'] = status
    bookData['grade'] = grade
    bookData['commentCount'] = commentCount
    bookData['createTime'] = time.time()
    bookData['bookType'] = bookType
    bookData['typeName'] = typeName

    # print(bookName,writer,bookId,wordsCount,status,grade,commentCount)
    sqlConnecter = MySQLHelper()
    sqlConnecter.connectMysql()

    bookCount = int(sqlConnecter.getLastId('Greader_books')) + 1
    bookData['id'] = bookCount
    bookInsertStatus = True
    try:
        res = sqlConnecter.insertData('Greader_books', bookData,"bookId")
        if res:
            bookCount = res
    except Exception as e:
        print('插入书籍数据失败: ' + str(e))
        bookInsertStatus = False

    if not bookInsertStatus:
        sqlConnecter.closeMysql()
        return

    nextStatus = book.xpath('//a[starts-with(@onclick,"ys.book.nextcomment")]/@onclick')
    if nextStatus and len(nextStatus) > 0:
        newStr = re.findall(r"\d+\.?\d",nextStatus[0])
        comments = getComment(newStr[0],newStr[1],bookPath)
        for index,value in enumerate(comments):
            commentTable = {}
            commentTable['bookId'] = bookId
            commentTable['bookName'] = bookName
            commentTable['content'] = value
            commentTable['fromUid'] = 1 # 此ID代表administrator
            commentCount = int(sqlConnecter.getLastId('Greader_comments')) + 1
            commentTable['createTime'] = time.time()
            commentTable['id'] = commentCount
            try:
                rec = sqlConnecter.insertData('Greader_comments', commentTable, False)
                if rec:
                    commentCount = rec
            except Exception as e:
                print('插入评论数据失败: ' + str(e))
    sqlConnecter.closeMysql()

def parseDataToLocal(bookPath):
    bookPageText = getContent(init_url, bookPath)
    book = etree.HTML(bookPageText.lower())

    bookData = []
    bookName = book.xpath('//div[@class="col-sm-7"]/div[1]/span[1]/text()')[0]
    writer = book.xpath(u'//div[@class="media-body ys-bookmain"]/ul/li[starts-with(text(),"作者")]/a/text()')[0]# 加U防止因中文编码引起的语法错误
    bookId = re.sub("\D","",bookPath)
    wordsNum = re.sub("\D","",book.xpath(u'//div[@class="media-body ys-bookmain"]/ul/li[starts-with(text(),"字数")]/text()')[0])
    status = int(init_keywords["status"])
    grade = book.xpath('//div[@class="ys-book-averrate xs-align-left"]/span/text()')[1].strip()
    commentCount = re.sub("\D","",book.xpath('//div[@class="ys-book-averrate xs-align-left"]/small/text()')[0])

    bookData.append(bookName)
    bookData.append(writer)
    bookData.append(bookId)
    bookData.append(wordsNum)
    bookData.append(status)
    bookData.append(grade)
    bookData.append(commentCount)
    # print(bookName,writer,bookId,wordsNum,status,grade,commentCount)

    data_save_path = init_txt_path + "bookData.xls"
    writeToExcel(data_save_path,bookData)

    nextStatus = book.xpath('//a[starts-with(@onclick,"ys.book.nextcomment")]/@onclick')
    if nextStatus and len(nextStatus) > 0:
        newStr = re.findall(r"\d+\.?\d",nextStatus[0])
        comments = getComment(newStr[0],newStr[1],bookPath)
        for index,value in enumerate(comments):
            commentTable = [bookId,bookName,bookId,value,"网友",None]
            writeToExcel(data_save_path,commentTable,"comments",commentSheet)

def writeToExcel(dataSavePath,data,sheetName="bookData",defultSheet=sheetExcel):
    if not os.path.exists(dataSavePath):
        excelObj = xlwt.Workbook(encoding = 'utf-8')
        sheet = excelObj.add_sheet(sheetName)
        for index,value in enumerate(defultSheet):
            sheet.write(0,index,value)
        excelObj.save(dataSavePath)

    bookXcel = open_workbook(dataSavePath) # 用wlrd提供的方法读取一个excel文件
    sheetNames = bookXcel.sheet_names()

    if sheetName in sheetNames:
        rows = bookXcel.sheet_by_name(sheetName).nrows # 用wlrd提供的方法获得现在已有的行数
        excel = copy(bookXcel) # 用xlutils提供的copy方法将xlrd的对象转化为xlwt的对象
        table = excel.get_sheet(sheetName) # 用xlwt对象的方法获得要操作的sheet
    else:
        excel = copy(bookXcel) # 用xlutils提供的copy方法将xlrd的对象转化为xlwt的对象
        table = excel.add_sheet(sheetName) # 当sheet不存在时创建
        for index,value in enumerate(defultSheet):
            table.write(0,index,value)
        rows = 1

    for index,value in enumerate(data):
        table.write(rows,index,value)
    excel.save(dataSavePath)

def getComment(bid,nexttime,bookPath):

    def getKeyWord(bid,nextTime):
        return {
                "bid":str(bid),
                "nexttime":str(nextTime)
                }

    commentHeaders = {
        "Accept":"application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding":"gzip, deflate",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
        "Connection":"keep-alive",
        "Cookie":"souser=6ba2fb48",
        "Host":"www.yousuu.com",
        "Referer":"http://www.yousuu.com/book/21235",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "X-Requested-With":"XMLHttpRequest"
    }


    keyWords = getKeyWord(bid,nexttime)
    thisReferer = init_url+bookPath
    commentHTML = getContent(init_url,"/ajax/nextcomment",keyWords,thisReferer,commentHeaders)
    commentHTML = json.loads(commentHTML)['comment']
    comments = []
    try:
        commentXpath = etree.HTML(commentHTML.lower())
        comments = commentXpath.xpath('//p[contains(@class,"commentcontent")]/text()')
    except Exception as e:
        print("评论拉取出错--跳过： " + str(e))

    goingOn = True
    while goingOn:
        #循环获取评论数据数据
        try:
            nextStatus = commentXpath.xpath('//a[starts-with(@onclick,"ys.book.nextcomment")]/@onclick')
        except Exception as e:
            nextStatus = False
            print("首次评论拉取出错--跳过： " + str(e))

        if nextStatus and len(nextStatus) > 0:
            newStr = re.findall(r"\d+\.?\d",nextStatus[0])
            keyWords = getKeyWord(newStr[0],newStr[1])
            commentHTML = getContent(init_url,"/ajax/nextcomment",keyWords,thisReferer,commentHeaders)
            commentHTML = json.loads(commentHTML)['comment']
            try:
                commentXpath = etree.HTML(commentHTML.lower())
                comments1 = commentXpath.xpath('//p[contains(@class,"commentcontent")]/text()')
                comments.extend(comments1)
            except Exception as e:
                goingOn = False
                print("评论拉取出错--跳过： " + str(e))
        else:
            break

    return comments

def delRepeat(table):
    s = set(table)
    c = [i for i in s]

    return c

def mainSpider():
    while True:
        html = getContent(init_url,init_path, init_keywords)
        isEndPage = parseListHtml(html)

        # if (isEndPage and int(init_keywords['status']) >= 3) or int(init_keywords['page']) >1:#page>1时跳出，测试用
        if (isEndPage and int(init_keywords['status']) >= 3):
            print("--------END---------"+str(isEndPage) +" " +init_keywords['status'] +" "+ init_keywords['page'])
            break
        elif isEndPage and int(init_keywords['status']) < 3 :
            init_keywords['page'] = "1"
            init_keywords['status'] = str(int(init_keywords['status']) + 1)
        else:
            init_keywords['page'] = str(int(init_keywords['page']) + 1)

if __name__ == '__main__':
    init_txt_path = '/Users/yangke/Personal/Python/pyData/save/'
    init_url = 'http://www.yousuu.com'
    init_path = '/category/all'
    init_keywords = {
        "sort":"rate",
        "page":"1",
        "status":"1"
    }
    mainSpider()
