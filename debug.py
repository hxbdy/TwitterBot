#デバッグ用
import Bot
from time import sleep
import unicodedata

test=Bot.Bot()
test.connectToDB()
print(test.lerningFromTL(10))
#print(len(test.MorphAnalyze("https://t.co/2sW9rcqEtO")))
test.disConnectToDB()