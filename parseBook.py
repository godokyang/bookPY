#encoding=utf8
import re
import os
import time
import codecs
from db.MySQLHelper import MySQLHelper

import sys
reload(sys)
sys.setdefaultencoding('gbk')

def parser(target):
    bnRegex = re.compile("<.*>")
    writerRegex = re.compile("\[.*\]")
    sessionData = {}

    bookType = "others"
    if os.path.exists(target):
        for (dirs,childDirs,chindFiles) in os.walk(target):
            for cDir in childDirs:
                thisPath = target+"/"+cDir
                if cDir == "仙侠武侠":
                    bookType = "wuxia"
                elif cDir == "历史军事":
                    bookType = "history"
                elif cDir == "文学艺术":
                    bookType = "literature"
                elif cDir == "游戏竞技":
                    bookType = "game"
                elif cDir == "玄幻奇幻":
                    bookType = "fantasy"
                elif cDir == "现代都市":
                    bookType = "city"
                elif cDir == "科幻灵异":
                    bookType = "future"


                for (tgt,tgtDirs,tgtFiles) in os.walk(thisPath):
                    for value in tgtFiles:
                        bookPath = thisPath + "/" + value
                        bookName = bnRegex.findall(value)[0].strip("<").strip(">")
                        bookWriter = writerRegex.findall(value)[0].strip("[").strip("]")
                        try:
                            bookName = bookName.decode("GB2312")
                        except Exception as e:
                            bookName = bookName.decode("utf-8")

                        try:
                            bookWriter = bookWriter.decode("GB2312")
                        except Exception as e:
                            bookWriter = bookWriter.decode("utf-8")

                        print(str(bookName),str(len(bookWriter)))

                        # print(str(writerRegex.findall(value)),str(bnRegex.findall(value)))
                        pattern = re.compile(u'[第].*[章回话节集卷].*?[ ].*?\n')
                        chapter = ""
                        session = ""

                        # print(str(bookPath))
                        try:
                            fbook = codecs.open(bookPath,"r+",'utf-8')
                        except Exception as e:
                            print("打开文件失败",str(e))

                        try:
                            for line in fbook.readlines():
                                chapters = pattern.findall(line)

                                if type(chapters) == list and len(chapters) > 0:
                                    if chapter == "":
                                        chapter = "序言"
                                    else:
                                        chapter = chapters[0]
                                    # print(chapter,session)
                                    print(chapter)
                                    sessionData["writer"] = bookWriter
                                    sessionData["bookName"] = bookName
                                    sessionData["bookType"] = bookType
                                    sessionData["typeName"] = cDir.decode('utf-8')
                                    sessionData['saveTime'] = time.time()
                                    sessionData["sessionContent"] = session
                                    sessionData['chapter'] = chapter
                                    sqlConnecter.insertData("Greader_sessions",sessionData)
                                    # reset session
                                    session = ""
                                else:
                                    session = session + line
                        except Exception as e:
                            print("读取文件失败",str(e))
                        fbook.close()


    # with open(target) as f:
    #     for line in f:
    #         chapters = pattern.findall("u'" + line + "'")
    #         print(chapters)


if __name__ == '__main__':
    path = "/opt/downloads"
    sqlConnecter = MySQLHelper()
    sqlConnecter.connectMysql()
    parser(path)
    sqlConnecter.closeMysql()
