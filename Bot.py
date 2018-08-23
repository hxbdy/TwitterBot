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
import unicodedata
import re
from datetime import datetime

class Bot:
    def __init__(self):
        pass

    def connectToDB(self):
        """DBに接続"""
        self.conn=mysql.connector.connect(user=setting.user,password=setting.password,host=setting.host,database=setting.database,buffered=True)
        self.cur = self.conn.cursor()
    
    def disConnectToDB(self):
        """DBから切断"""     
        self.cur.close
        self.conn.close

    def stringGenRandom(self):
        """ランダムに文字列を生成する"""
        sql="select * from start order by rand() limit 1;"
        row=self.getSQL(sql)
        prefix=row[0]
        suffix1=row[1]
        suffix2=row[2]
        sentence=self.stringGenHint(prefix,suffix1,suffix2)
        return sentence

    def stringGen(self,prefix):
        """prefixから文字列を生成する"""
        #prefix=self.getRawString(prefix)
        prefix=self.realEscapeStringEncode(prefix)
        sql="select * from " + self.formatForTable(self.getInitial(prefix)) + " where prefix=convert('" + prefix + "' using binary) order by rand() limit 1;"
        row=self.getSQL(sql)
        #prefix=row[0]
        suffix1=row[1]
        suffix2=row[2]
        sentence=self.stringGenHint(prefix,suffix1,suffix2)
        return sentence

    def addStringToDB(self,string):
        """DBにstringを登録する"""
        array=self.MorphAnalyze(string)
        if len(array)!=0:
            self.addArrayToDB(array)

    
    #!!!下層メソッドに致命的なバグあり!!!
    def addArrayToDB(self,array):
        """
        DBにarrayを登録する\n
        最初の3節のみstartテーブルに登録する
        """
        #try:
        #    array.remove(' ')
        #    array.remove('　')
        #except ValueError:
        #    pass

        array=self.realEscapeStringEncode(array)
        if len(array)==0:
            print("ERROR:MorphAnalyzer return NULL")
            exit(-1)
        elif len(array)==1:
            array.extend(["EOF","EOF"])
        elif len(array)>=2:
            array.append("EOF")
        #print(array)
        for i in range(len(array)-2):
            #prefix =self.getRawString(array[i])
            #suffix1=self.getRawString(array[i+1])
            #suffix2=self.getRawString(array[i+2])
            print("prefix="+array[i]+" suffix1="+array[i+1]+" suffix2="+array[i+2])
            if i==0:
                if not self.isRecordExistFromStart(array[i],array[i+1],array[i+2]):
                    sql="insert into start values(convert('" + self.mysqlRealEscapeString(array[i]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+1]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+2]) + "' using binary));"
                    #print(sql)
                    self.getSQL(sql)
            else:
                if self.isEmoji(array[i]):
                    if not self.isRecordExistFromEmoji(array[i],array[i+1],array[i+2]):
                        sql="insert into emoji values(convert('" + self.mysqlRealEscapeString(array[i]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+1]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+2]) + "' using binary));"
                        self.getSQL(sql)
                else:
                    if not self.isTableExist(array[i]):
                        self.createTable(array[i])
                    if not self.isRecordExist(array[i],array[i+1],array[i+2]):
                        sql="insert into " + self.formatForTable(self.getInitial(array[i])) + " values(convert('" + self.mysqlRealEscapeString(array[i]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+1]) + "' using binary),convert('" + self.mysqlRealEscapeString(array[i+2]) + "' using binary));"
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

    def getSQL(self,sql):
        """sqlを実行して結果を取得する"""
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
        #prefix=self.realEscapeStringEncode(prefix)
        #suffix1=self.realEscapeStringEncode(suffix1)
        #suffix2=self.realEscapeStringEncode(suffix2)
        while prefix!="EOF" and suffix1!="EOF" and suffix2!="EOF":
            if self.isEmoji(suffix1):
                sql="select * from emoji where prefix=convert('" + self.mysqlRealEscapeString(suffix1) + "' using binary) and suffix1=convert('" + self.mysqlRealEscapeString(suffix2) + "' using binary) order by rand() limit 1;"
            else:
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

    #stringのテーブルが既に存在するかを取得する
    #initialをTrueでstringの頭文字のテーブルが存在するか調べる
    #Falseでstringのテーブルが存在するか調べる
    def isTableExist(self,string,initial=True):
        if initial:
            tableName=self.getInitial(string)
        else:
            tableName=string
        tableName=self.mysqlRealEscapeString(tableName)
        #if tableName=="\\n":
        #    tableName=tableName.replace("\\n","\\\\\\\\n")
        tableName=tableName.replace("%","\%")

        sql="show tables from "+setting.database+" like '" + tableName + "';"
        #print(sql)
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #指定レコードが存在するかを取得する
    #start,id,emojiテーブル以外から探す
    def isRecordExist(self,prefix,suffix1,suffix2):
        sql="select * from "+self.formatForTable(self.getInitial(prefix))+" where prefix=convert('" + self.mysqlRealEscapeString(prefix) + "' using binary) and suffix1=convert('"+self.mysqlRealEscapeString(suffix1)+"' using binary) and suffix2=convert('"+self.mysqlRealEscapeString(suffix2)+"' using binary);"
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #指定レコードが存在するかを取得する
    #startテーブルから探す
    def isRecordExistFromStart(self,prefix,suffix1,suffix2):
        sql="select * from start where prefix=convert('" + self.mysqlRealEscapeString(prefix) + "' using binary) and suffix1=convert('"+self.mysqlRealEscapeString(suffix1)+"' using binary) and suffix2=convert('"+self.mysqlRealEscapeString(suffix2)+"' using binary);"
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

    #指定レコードが存在するかを取得する
    #emojiテーブルから探す
    def isRecordExistFromEmoji(self,prefix,suffix1,suffix2):
        sql="select * from emoji where prefix=convert('" + self.mysqlRealEscapeString(prefix) + "' using binary) and suffix1=convert('"+self.mysqlRealEscapeString(suffix1)+"' using binary) and suffix2=convert('"+self.mysqlRealEscapeString(suffix2)+"' using binary);"
        row=self.getSQL(sql)
        if not row:
            flg=False
        else:
            flg=True
        return flg

    #stringを形態素解析してarrayで取得
    #URLは解析対象外
    #返り値にURLを付加するかは考え中。今は除外する。
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
        #print(string)
        requestURL = "https://jlp.yahooapis.jp/MAService/V1/parse"
        parameter = {'appid': setting.appId,
                     'sentence': string,
                     'results': 'ma'}
        r = requests.get(requestURL, params=parameter)
        elem = fromstring(r.text.encode('utf-8'))
        array=[]
        for e in elem.getiterator("{urn:yahoo:jp:jlp}surface"):
            array.append(e.text)
        #以下のコメントアウトを外すとURLも含む
        #if flg:
        #    for i in range(len(URLpos)):
        #        array.append(prepare[URLpos[i]])
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
            self.logging(string)
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
        requestURL = "https://jlp.yahooapis.jp/MAService/V1/parse"
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

    #未返信のリプライに対して宛先tweet_idとtextをディクショナリ形式でnumber件返す
    def getReplyIdDic(self,number):
        url = "https://api.twitter.com/1.1/statuses/mentions_timeline.json"
        params = {"count":number}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        dic={}
        if req.status_code == 200:
            timeline = json.loads(req.text)
            #print(timeline)
            for tweet in timeline:
                #print(tweet)
                if not self.isRecordExistFromId(tweet["id"]):
                    self.addReplyId(tweet["id"])
                    #screen_name=self.getScreenName(tweet["id"])
                    dic[tweet["id"]]=tweet["text"]
        else:
            print ("Error: %d" % req.status_code)
        return dic

    #最新のnumber件のreplyidをDBに登録する
    #登録したreplyidを返す
    def addReplyIdToDB(self,number):
        array=self.getReplyId(number)
        unreply=[]
        for i in range(len(array)):
            if not self.isRecordExistFromId(array[i]):
                sql="insert into reply values('" + str(array[i]) + "');"
                self.getSQL(sql)
                unreply.append(array[i])
        return unreply

    #idをreplyテーブルに登録する
    #登録したらTrue,しなかったらFalseを返す
    def addReplyId(self,id):
        if not self.isRecordExistFromId(id):
            sql="insert into reply values('" + str(id) + "');"
            self.getSQL(sql)
            return True
        return False

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
    def realEscapeStringEncode(self,string):
        if type(string)==str:
            string=string.replace(" ","%space%")
            string=string.replace("　","%space%")
            string=string.replace("_","%underscore%")
            string=string.replace("@","@.")
        elif type(string)==list:
            for i in range(len(string)):
                string[i]=string[i].replace(" ","%space%")
                string[i]=string[i].replace("　","%space%")
                string[i]=string[i].replace("_","%underscore%")
                string[i]=string[i].replace("@","@.")
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
    #使用非推奨メソッド
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

    def isURL(self,string):
        """URLがstring中に含まれているか\n
        有効かどうかは判断しない"""
        #result=urllib.parse.urlparse(url)
        if string.find("http")>-1:
            return True
        else:
            return False
        #if len(result.scheme) > 0:
        #    return True
        #else:
        #    return False
        #if result.scheme=='':
        #    return False
        #else:
        #    return True

    #何行目まで登録するかのendsetが欲しい
    def addFromCSV(self,path,offset=0):
        """csvを読みこんでDBに登録する\n
        csvファイルはutf-8(BOM無し)\n
        何行目から登録するかのoffset"""
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

        self.initializeDB()

        csvFile=open(path,"r")
        f=csv.reader(csvFile)
        cnt=0
        #limit件のみ登録する
        #limit=100
        for row in f:
            #if limit<0:
            #    return
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
                #sleep(0.5)
                cnt+=1
                if(offset<cnt):
                    self.addStringToDB(row[5])
                    #limit-=1

    def isEmoji(self,string):
        """stringの頭文字が絵文字かどうか"""
        head=self.getInitial(string)
        print(unicodedata.category(head))
        if(unicodedata.category(head)=='So' or unicodedata.category(head)=='Cn'):
            return True
        else:
            return False

    def reply(self,number):
        """最新number件に対して返信する"""
        #data[id]=textの形式
        data=self.getReplyIdDic(number)
        print(data)
        id_arr=data.keys()
        for i in id_arr:
            text=self.deleteUserName(data[i])
            n=self.getRandomNoun(text)
            if self.isTableExist(n):
                text=self.stringGen(n)
            else:
                text="It is an unlearned hint"
            text=self.getScreenName(i)+" "+text
            self.replyToId(i,text)

    def deleteUserName(self,text):
        """ユーザ名とツイートを分離し、ツイート部分のみ返す
        """
        regex = r'@\S+'
        iterator = re.finditer(regex ,text)
        for match in iterator:
            text=text.replace(match.group(),"")
        matchObj = re.search(r'\s+', text)
        text=text[matchObj.end():]
        return text

    def getScreenName(self,id):
        """Tweetidからscreen nameを取得する"""
        url = "https://api.twitter.com/1.1/statuses/show.json"
        params = {"id":id}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.get(url, params = params)
        if req.status_code == 200:
            timeline = json.loads(req.text)
            return '@'+timeline["user"]["screen_name"]
        else:
            print("Error: %d" % req.status_code)

    def replyToId(self,id,text):
        """id宛にtextを返信する\n
        textの先頭には@screen_nameが付加されている必要がある"""
        url = "https://api.twitter.com/1.1/statuses/update.json"
        params = {"status": text,
                  "in_reply_to_status_id":id}
        twitter = OAuth1Session(setting.consumerKey, setting.consumerSecret, setting.accessToken, setting.accesssTokenSecert)
        req = twitter.post(url, params = params)
        if req.status_code == 200:
            print ("OK")
        else:
            print ("Error: %d" % req.status_code)

    def initializeDB(self):
        """emoji,reply,startテーブルがない場合は作る"""
        if not self.isTableExist("emoji",False):
            sql="create table emoji (prefix CHAR(50),suffix1 CHAR(50),suffix2 CHAR(50));"
            self.getSQL(sql)
        if not self.isTableExist("reply",False):
            sql="create table reply (id CHAR(50));"
            self.getSQL(sql)
        if not self.isTableExist("start",False):
            sql="create table start (prefix CHAR(50),suffix1 CHAR(50),suffix2 CHAR(50));"
            self.getSQL(sql)

    def isMention(self,string):
        """@\w+が存在するか調べる"""
        if re.search(r'@\w+',string)!=None:
            return True
        else:
            return False

    def lerningFromTL(self,num):
        """TLからnum件取得して学習する"""
        arr=self.getTL(num)
        for i in range(len(arr)):
            if not self.isMention(arr[i]):
                self.addStringToDB(arr[i])

    def logging(self,string):
        """stringを現在時刻とともにロギングする"""
        #print(datetime.now().strftime("%Y/%m/%d %H:%M:%S")+" "+string)
        with open("himazindanaBotLog.txt", mode='a') as f:
            f.write('\n'+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+" "+string)