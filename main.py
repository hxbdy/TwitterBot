import Bot
from time import sleep
import unicodedata

test=Bot.Bot()
test.connectToDB()
t=test.stringGenRandom()
test.tweet(t)
test.lerningFromTL(10)
test.disConnectToDB()