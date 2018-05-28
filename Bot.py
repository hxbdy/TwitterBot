#2018/03/10
#DBの文字セットはutf8mb4にすること

import mysql.connector
import requests
from xml.etree.ElementTree import *
from requests_oauthlib import OAuth1Session
import json
import csv
import setting
import random
import urllib.parse
from time import sleep

class Bot:
    def __init__(self):
        pass

    #DBに接続
    def connectToDB(self):
        self.conn=mysql.connector.connect(user=setting.user,password=setting.password,host=setting.host,database=setting.database,buffered=True)
        self.cur = self.conn.cursor()
    
    #DBから切断
    def disConnectToDB(self):
        self.cur.close
        self.conn.close
    
    #ランダムに文字列を生成する
    def stringGenRandom(self):
        sql="select * from start order by rand() limit 1;"
        row=self.getSQL(sql)
        prefix=row[0]
        suffix1=row[1]
        suffix2=row[2]
        sentence=self.stringGenHint(prefix,suffix1,suffix2)
        return sentence

    #prefixから文字列を生成する
    def stringGen(self,prefix):
        prefix=self.getRawString(prefix)
        sql="select * from " + self.formatForTable(self.getInitial(prefix)) + " where prefix=convert('" + prefix + "' using binary) order by rand() limit 1;"
        row=self.getSQL(sql)
        #prefix=row[0]
        suffix1=row[1]
        suffix2=row[2]
        sentence=self.stringGenHint(prefix,suffix1,suffix2)
        return sentence

    #DBにstringを登録する
    def addStringToDB(self,string):
        array=self.MorphAnalyze(string)
        self.addArrayToDB(array)

    #DBにarrayを登録する
    #最初の3節のみstartテーブルに登録する
    #!!!下層メソッドに致命的なバグあり!!!
    def addArrayToDB(self,array):
        
        #try:
        #    array.remove(' ')
        #    array.remove('　')
        #except ValueError:
        #    pass

        array=self.realEscapeStringEncode(array)
        if len(array)==1:
            array.extend(["EOF","EOF"])
        elif len(array)>=2:
            array.append("EOF")
        #print(array)
        for i in range(len(array)-2):
            #prefix =self.getRawString(array[i])
            #suffix1=self.getRawString(array[i+1])
            #suffix2=self.getRawString(array[i+2])
            if i==0:
                if not self.isRecordExistFromStart(array[i],array[i+1],array[i+2]):
                    sql="insert into start values('" + self.mysqlRealEscapeString(array[i]) + "','" + self.mysqlRealEscapeString(array[i+1]) + "','" + self.mysqlRealEscapeString(array[i+2]) + "');"
                    #print(sql)
                    self.getSQL(sql)
            else:
                if not self.isTableExist(array[i]):
                    self.createTable(array[i])
                if not self.isRecordExist(array[i],array[i+1],array[i+2]):
                    sql="insert into " + self.formatForTable(self.getInitial(array[i])) + " values('" + self.mysqlRealEscapeString(array[i]) + "','" + self.mysqlRealEscapeString(array[i+1]) + "','" + self.mysqlRealEscapeString(array[i+2]) + "');"
                    self.getSQL(sql)
    
    #stringの頭文字1文字目を取得する
    #PHPのmysql_real_escape_string
    #これは以下の文字について先頭にバックスラッシュを付加します
    #\x00, \n, \r, \, ', " そして \x1a.
    #JIS X 0201
    def getInitial(self,string):
        if len(string)<2:
            return string
        
        first=string[0]
        second=string[1]

        #print(first+"="+str(hex(ord(first))))
        #print(second+"="+str(hex(ord(second))))

        #\
        escape1=0xa5
        escape2=0x5c

        if escape1==ord(first) or escape2==ord(first):
            #\
            if ord(second)==0xa5 or ord(second)==0x5c:
                return first+second
            #'
            elif ord(second)==0x27:
                return first+second
            #"
            elif ord(second)==0x22:
                return first+second
            #n
            elif ord(second)==0x6e:
                return first+second
            #r
            elif ord(second)==0x72:
                return first+second

        return first

    #sqlを実行して結果を取得する
    def getSQL(self,sql):
        print(sql)
        self.cur.execute(sql)
        if sql.find("select")>-1 or sql.find("show")>-1:
            row=self.cur.fetchone()
            print(row)
            return row
        else:
            self.conn.commit()

    #3節から文字列を生成する
    #!!!下層メソッドに致命的なバグあり!!!
    #テスト可能
    def stringGenHint(self,prefix,suffix1,suffix2):
        sentence=prefix+suffix1+suffix2
        while prefix!="EOF" and suffix1!="EOF" and suffix2!="EOF":
            sql="select * from " + self.formatForTable(self.getInitial(suffix1)) + " where prefix=convert('" + self.mysqlRealEscapeString(suffix1) + "' using binary) and suffix1=convert('" + self.mysqlRealEscapeString(suffix2) + "' using binary) order by rand() limit 1;"
            row=self.getSQL(sql)
            #print(row)
            if len(row)==0:
                break
            prefix=suffix1
            suffix1=suffix2
            suffix2=row[2]
            sentence+=suffix2
        sentence=sentence.replace("EOF","")
        sentence=self.realEscapeStringDecode(sentence)
        return sentence

    #stringの頭文字のテーブルを作成
    def createTable(self,string):
        first=self.getInitial(string)
        #tableName=self.getRawString(first)
        tableName=self.formatForTable(first)
        #print("tableName="+tableName)
        self.cur.execute("create table "+tableName+" (prefix CHAR(50),suffix1 CHAR(50),suffix2 CHAR(50));")
        self.conn.commit()

    #stringの頭文字のテーブルが既に存在するかを取得する
    def isTableExist(self,string):
        tableName=self.getInitial(string)
        tableName=self.mysqlRealEscapeString(tableName)
        #if tableName=="\\n":
        #    tableName=tableName.replace("\\n","\\\\\\\\n")
        tableName=tableName.replace("%","\%")

        sql="show tables from test like '" + tableName + "';"
        #print(sql)
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #指定レコードが存在するかを取得する
    #start,idテーブル以外から探す
    def isRecordExist(self,prefix,suffix1,suffix2):
        sql="select * from "+self.formatForTable(self.getInitial(prefix))+" where prefix=convert('" + self.mysqlRealEscapeString(prefix) + "' using binary) and suffix1='"+self.mysqlRealEscapeString(suffix1)+"' and suffix2='"+self.mysqlRealEscapeString(suffix2)+"';"
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #指定レコードが存在するかを取得する
    #startテーブルから探す
    def isRecordExistFromStart(self,prefix,suffix1,suffix2):
        sql="select * from start where prefix=convert('" + self.mysqlRealEscapeString(prefix) + "' using binary) and suffix1='"+self.mysqlRealEscapeString(suffix1)+"' and suffix2='"+self.mysqlRealEscapeString(suffix2)+"';"
        #print(sql)
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #指定レコードが存在するかを取得する
    #idテーブルから探す
    def isRecordExistFromId(self,id):
        sql="select * from reply where id='" + str(id) + "';"
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #stringを形態素解析してarrayで取得
    #URLは解析対象外
    def MorphAnalyze(self,string):
        flg=False
        escape=""
        URLpos=[]
        prepare=string.split()
        #URLの位置を記憶
        for i in range(len(prepare)):
            if self.isURL(prepare[i]):
                flg=True
                URLpos.append(i)
        #URL部分を削除し、元の文章の復元
        for i in range(len(prepare)):
            if not self.isURL(prepare[i]):
                escape+=prepare[i]+" "
        string=escape[:-1]
        print(string)
        requestURL = "http://jlp.yahooapis.jp/MAService/V1/parse"
        parameter = {'appid': setting.appId,
                'sentence': string,
                'results': 'ma'}
        r = requests.get(requestURL, params=parameter)
        elem = fromstring(r.text.encode('utf-8'))
        array=[]
        for e in elem.getiterator("{urn:yahoo:jp:jlp}surface"):
            array.append(e.text)
        if flg:
            for i in range(len(URLpos)):
                array.append(prepare[URLpos[i]])
        return array

    #replyを最新number件取得する
    def getReply(self,number):
        url = "https://api.twitter.com/1.1/statuses/mentions_timeline.json"
        params = {"count":number}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        array=[]
        if req.status_code == 200:
            timeline = json.loads(req.text)
            for tweet in timeline:
                array.append(tweet["text"])
        else:
            print ("Error: %d" % req.status_code)
        return array

    #tweetする
    def tweet(self,string):
        url = "https://api.twitter.com/1.1/statuses/update.json"
        params = {"status": string}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.post(url, params = params)
        if req.status_code == 200:
            print ("OK")
        else:
            print ("Error: %d" % req.status_code)
    
    #指定ユーザのTL最新number件を取得する
    #1<=number<=200
    def getTLUser(self,user,number):
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {"screen_name": user,"count":number}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        array=[]
        if req.status_code == 200:
            timeline = json.loads(req.text)
            for tweet in timeline:
                array.append(tweet["text"])
        else:
            print ("Error: %d" % req.status_code)
        return array

    #TL最新number件のtweetを取得する
    #1<=number<=200
    def getTL(self,number):
        url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
        params = {"count":number}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        array=[]
        if req.status_code == 200:
            timeline = json.loads(req.text)
            for tweet in timeline:
                array.append(tweet["text"])
        else:
            print ("Error: %d" % req.status_code)
        return array

    #string中の名詞すべてを取得する
    def getAllNoun(self,string):
        requestURL = "http://jlp.yahooapis.jp/MAService/V1/parse"
        parameter = {'appid': setting.appId,
                'sentence': string,
                'results': 'ma',
                'filter':'9'}
        r = requests.get(requestURL, params=parameter)
        elem = fromstring(r.text.encode('utf-8'))
        array=[]
        for e in elem.getiterator("{urn:yahoo:jp:jlp}surface"):
            array.append(e.text)
        return array

    #string中の名詞を1つランダムに取得する
    def getRandomNoun(self,string):
        array=self.getAllNoun(string)
        if len(array)==0:
            return False
        num=random.randint(0,len(array)-1)
        return array[num]

    #string中の最初に見つかった名詞を取得する
    def getFirstNoun(self,string):
        array=self.getAllNoun(string)
        if len(array)==0:
            return False
        return array[0]

    #replyidをnumber件取得する
    def getReplyId(self,number):
        url = "https://api.twitter.com/1.1/statuses/mentions_timeline.json"
        params = {"count":number}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        array=[]
        if req.status_code == 200:
            timeline = json.loads(req.text)
            for tweet in timeline:
                array.append(tweet["id"])
        else:
            print ("Error: %d" % req.status_code)
        return array

    #最新のnumber件のreplyidをDBに登録する
    def addReplyIdToDB(self,number):
        array=self.getReplyId(10)
        for i in range(len(array)):
            if not self.isRecordExistFromId(array[i]):
                sql="insert into reply values('" + str(array[i]) + "');"
                self.getSQL(sql)

    #SQLインジェクション攻撃対策
    def antiSQLInjectionAttack(self,array):
        sql="select * from a where suffix=convert('%s' using binary);"
        self.cur.execute(sql,("a"))
        row=self.cur.fetchone()
        return row

    #特殊文字のエスケプ
    #!!!バッククォートは使用できないためシングルクォートに置換している!!!
    def mysqlRealEscapeString(self,string):
        string=string.replace("\n","\\n")
        string=string.replace("\r","\\r")
        string=string.replace("\\","\\\\")
        string=string.replace("`","'")
        string=string.replace("'","\\'")
        string=string.replace('"','\\"')
        #?必要?
        
        #string="'"+string+"'"
        return string

    #エスケープシーケンスを使用しない特殊文字の変換
    #strでもlistでもok
    #絵文字もバイトコードとかで対応したい
    def realEscapeStringEncode(self,string):
        if type(string)==str:
            string=string.replace(" ","%space%")
            string=string.replace("　","%space%")
            string=string.replace("_","%underscore%")
        elif type(string)==list:
            for i in range(len(string)):
                string[i]=string[i].replace(" ","%space%")
                string[i]=string[i].replace("　","%space%")
                string[i]=string[i].replace("_","%underscore%")
        return string

    #エスケープシーケンスを使用しない特殊文字の復号
    #strでもlistでもok
    def realEscapeStringDecode(self,string):
        if type(string)==str:
            string=string.replace("%space%"," ")
            string=string.replace("%underscore","_")
        elif type(string)==list:
            for i in range(len(string)):
                string[i]=string[i].replace("%space%"," ")
                string[i]=string[i].replace("%underscore%","_")
        return string

    #エスケープシーケンス無効の文字列を返す
    #上のメソッドみたいに地道にやる?
    #!!!致命的なバグあり!!!
    def getRawString(self,string):
        print("before="+string)
        string=repr(string)
        string=string[1:]
        string=string[:-1]
        #string=string.replace("'","\\'")
        #string=string.replace('"','\\"')
        #string=string.replace('?','')
        #string=string.replace(' ','')
        #string=string.replace('　','')
        print("after="+string)
        return string

    #テーブル名用の整形
    #getInitialを通してから使用すること
    def formatForTable(self,tableName):
        tableName=tableName.replace("`","'")
        tableName=tableName.replace("\\'","'")
        tableName=tableName.replace('\\"','"')
        tableName=tableName.replace("\n","\\n")
        #tableName=tableName.replace("%","\%")
        tableName="`"+tableName+"`"
        return tableName

    #URLかどうか
    #有効かどうかは判断しない
    def isURL(self,url):
        result=urllib.parse.urlparse(url)
        if result.scheme=='':
            return False
        else:
            return True

    ############################
    #csvを読みこんでDBに登録する
    #csvファイルはutf-8(BOM無し)
    #何行目から登録するかのoffset変数も欲しい
    def addFromCSV(self,path,offset=0):
        tweet_id=[]
        in_reply_to_status_id=[]
        in_reply_to_user_id=[]
        timestamp=[]
        source=[]
        text=[]
        retweeted_status_id=[]
        retweeted_status_user_id=[]
        retweeted_status_timestamp=[]
        expanded_urls=[]

        csvFile=open(path,"r")
        f=csv.reader(csvFile)
        cnt=0
        #limit件のみ登録する
        limit=500
        for row in f:
            if cnt>limit:
                return
            tweet_id.append(row[0])
            in_reply_to_status_id.append(row[1])
            in_reply_to_user_id.append(row[2])
            timestamp.append(row[3])
            source.append(row[4])
            text.append(row[5])
            retweeted_status_id.append(row[6])
            retweeted_status_user_id.append(row[7])
            retweeted_status_timestamp.append(row[8])
            expanded_urls.append(row[9])
            #リプ,RTは除く
            if(row[1]=="" and row[6]==""):
                print(row[5])
                sleep(0.5)
                cnt+=1
                if(offset<cnt):
                    self.addStringToDB(row[5])

    #～テーブル名を扱うためには～
    #ダブル、シングルクォートには\をつけない
    #ただし、\には付ける
    #スペース系は使えないから消すかなんかする

    #debug用
    def debug(self):
        sql=r"show tables from test like '\\\\n';"
        self.cur.execute(sql)
        row=self.cur.fetchall()
        print(row)
        #動作確認済み
        #sql=r"select * from `'` where suffix='\'' and prefix1='こう' and prefix2='いう';"
        #sql=r"select * from `\` where suffix='\\' and prefix1='\'' and prefix2='こう';"
        #sql=r"select * from `\` where suffix='\\';"
        #self.getSQL(sql)