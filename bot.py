import telebot
import logging

bot = telebot.TeleBot('***REMOVED***')

@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, "Поехали!")
    logging.warning('Watch out! ' + str(m.chat.username) + " started the bot")

@bot.message_handler(content_types=["text"])
def handle_text(message):
    bot.send_message(message.chat.id, 'Макс, отстань, задолбал писать: ' + message.text)
    logging.warning('Message received from ' + str(message.chat.username) + ": " + message.text)

def main():
    bot.polling(non_stop=True, interval=0)

if __name__ == '__main__':
    main()