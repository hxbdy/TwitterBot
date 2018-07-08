import Bot
from time import sleep
import unicodedata

test=Bot.Bot()
test.connectToDB()
while True:
    t=test.stringGenRandom()
    if test.isMention(t) or test.isURL(t):
        continue
    else:
        break
test.tweet(t)
test.lerningFromTL(10)
test.disConnectToDB()