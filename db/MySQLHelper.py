#encoding=UTF8

import pymysql
import re
import time

class MySQLHelper():
    # 类初始化
    __BookCreateSql = '''
        CREATE TABLE IF NOT EXISTS Greader_books
        (
        id int(10) NOT NULL AUTO_INCREMENT,
        bookName char(50) NOT NULL,
        writer char(20) NOT NULL,
        wordsCount char(10) NOT NULL,
        status int(10) DEFAULT 1,
        bookId int(10) NOT NULL,
        grade float DEFAULT 0,
        createTime float NOT NULL,
        commentCount int(10) DEFAULT 0,
        bookType char(20) NOT NULL,
        typeName char(20) NOT NULL,
        PRIMARY key (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    '''

    __CommentCreateSql = '''
        CREATE TABLE IF NOT EXISTS Greader_comments
        (
            id int(10) NOT NULL AUTO_INCREMENT,
            bookName char(50) NOT NULL,
            bookId int(10) NOT NULL,
            content varchar(500) DEFAULT NULL,
            fromUid int(10) ZEROFILL DEFAULT 1,
            createTime float NOT NULL,
            PRIMARY key (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=UTF8;
    '''

    __CreateBookSession = '''
        CREATE TABLE IF NOT EXISTS Greader_sessions
        (
            id int(10) NOT NULL AUTO_INCREMENT,
            bookName char(50) NOT NULL,
            bookId int(10) NOT NULL,
            chapter varchar(100) NOT NULL,
            sessionContent text NOT NULL,
            saveTime float NOT NULL,
            PRIMARY key (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=UTF8;
    '''

    def __init__(self):
        self.host = 'localhost'
        self.port = 3306
        self.user = 'root'
        self.password = '!qaz2wsx'
        self.db = 'Greader'
        self.table = 'Greader_books'

    # 判断表是否存在
    def ifExistTable(self, tableName):
        sqlShowTable = "SHOW TABLES;"
        self.cursor.execute(sqlShowTable)
        tables=[self.cursor.fetchall()]# 返回的数据类似(('city',),('country',))

        try:
            table_list = re.findall("(\'.*?\')")# 去掉括号
            table_list = [re.sub("'",'',each) for each in table_list] # 去掉引号
        except Exception as e:
            print("数据格式化失败："+str(e))
            return 0

        if tableName in table_list:
            return 1
        else:
            print('table not exist')
            return 0

    # 连接数据库
    def connectMysql(self):
        try:
            self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                        passwd=self.password, db=self.db, charset='utf8')
            self.cursor = self.conn.cursor()
        except:
            print("sql connect failed.")

    def insertData(self, tableName, my_dict, repeatCheck=False):
        bookCheck = False
        if not self.ifExistTable(tableName):
            if tableName == 'Greader_books':
                self.cursor.execute(re.sub('[\n\t\r]','',self.__BookCreateSql))
            elif tableName == 'Greader_comments':
                self.cursor.execute(re.sub('[\n\t\r]','',self.__CommentCreateSql))
            elif tableName == 'Greader_sessions':
                self.cursor.execute(re.sub('[\n\t\r]','',self.__CreateBookSession))
                bookCheck = True

        table = tableName and tableName or "Greader_books"

        if bookCheck:
            checkSQL = 'SELECT * FROM Greader_books WHERE bookName="' + str(my_dict["bookName"]) +'";'
            maxIdSQL = "SELECT MAX(bookId) FROM Greader_books;"
            countSQL = "SELECT max(id) FROM Greader_books;"
            self.cursor.execute(maxIdSQL)
            maxId = self.cursor.fetchone()
            self.cursor.execute(countSQL)
            thisId = self.cursor.fetchone()
            my_dict['bookId'] = maxId[0]+1
            print(type(my_dict["writer"]))
            insertSQL = "INSERT INTO Greader_books (id,bookName,writer,wordsCount,status,bookId,grade,createTime,commentCount,bookType,typeName) VALUES ("+str(thisId[0]+1)+",'"+my_dict["bookName"]+"','"+my_dict["writer"]+"',0,2,"+str(my_dict['bookId'])+",0,"+str(time.time())+",0,'"+my_dict["bookType"]+"','"+my_dict["typeName"]+"');"
            res = self.cursor.execute(checkSQL)
            if res:
                print("书籍已经存在",res)
            else:
                print(str(insertSQL))
                self.cursor.execute(insertSQL)

        if repeatCheck:
            sqlExit = "SELECT " + repeatCheck + " FROM "+ tableName + " WHERE " + repeatCheck + " = '%s';" % (str(my_dict[repeatCheck]))
            # print("sqlExit:  " + sqlExit)
            res = self.cursor.execute(sqlExit)

            if res:
                print("数据已经存在",res)
                return 0

        if tableName == 'Greader_sessions':
            del my_dict["writer"]
            del my_dict["bookType"]
            del my_dict["typeName"]

        cols = ', '.join(my_dict.keys())#用，分割
        values = '", "'.join('%s' %id for id in my_dict.values())#将list中所有数据转换为string并用","分割
        sql = "INSERT INTO "+ tableName +"(%s) VALUES (%s);" % (cols, '"' + values + '"')
        #拼装后的sql如下
        #INSERT INTO tableName (key1, key2, key3...) VALUES ("value1","value2","value3"...)

        # print("sql: "+ sql)

        try:
            result = self.cursor.execute(sql)
            insert_id = self.conn.insert_id()
            self.conn.commit()
            # 判断是否执行成功
            if result:
                print("插入成功", insert_id)
                return insert_id + 1
        except pymysql.Error as e:
            # 发生错误回滚
            self.conn.rollback()
            # 主键唯一，无法插入
            if "key 'PRIMARY'" in e.args[1]:
                print("数据已存在，未插入数据")
            else:
                print("插入数据失败，原因 %d: %s" % (e.args[0], e.args[1]))
        except pymysql.Error as e:
            print("数据库错误，原因%d: %s" % (e.args[0], e.args[1]))

    def getLastId(self,tableName):
        sql = "SELECT max(id) FROM " + tableName
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone() # 获取查询到的第一条数据
            if row[0]:
                return row[0] # 返回最后一条数据的id
            else:
                return 0 # 否则返回0
        except:
            print(sql + ' execute failed.')
            return 0

    def closeMysql(self):
        self.cursor.close()
        self.conn.close()
