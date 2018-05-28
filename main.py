import Bot
from time import sleep

test=Bot.Bot()
test.connectToDB()

print(test.addFromCSV("tweets.csv"))
#sleep(1)
#print(ary)

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