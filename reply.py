import Bot
from time import sleep
import unicodedata

test=Bot.Bot()
test.connectToDB()

test.reply(5)

test.disConnectToDB()