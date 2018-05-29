import Bot
from time import sleep
import unicodedata

test=Bot.Bot()
test.connectToDB()

#test.tweet("test")
#test.getSQL("select * from `＼` where prefix=convert('＼' using binary) and suffix1=convert('%space%' using binary) and suffix2=convert('🍡＼' using binary);")
print(test.addFromCSV("tweets.csv",200))
#print(test.getInitial('🍡おいしい'))
#sleep(1)
#print(ary)
#print('🍡='+str(hex(ord('🍡'))))
#if(unicodedata.category('🍡')=='So'):
#    print('🍡is emoji')
test.disConnectToDB()
#print(hex(ord(tl[0])))
#print(hex(ord(tl[1])))
#print(hex(ord(tl[2])))
#print(hex(ord(tl[3])))
#s=test.getInitial(tl)
#print("initial="+s)
#s=test.formatForTable(s)
#print("tableName="+s)
#a="\\"
#print("a="+hex(ord(a)))
#print(chr(0xa5))
#print(chr(0x5c))
#print(chr(0x61))s