import telebot
import requests

TOKEN_BOT_2 = "TU_TOKEN_BOT_2"
NODE_SERVER_URL = "http://localhost:4000/api/new_message"

bot = telebot.TeleBot(TOKEN_BOT_2)

@bot.message_handler(func=lambda message: True)
def handle_global_chat(message):
    data = {
        "user": message.from_user.first_name,
        "id": message.from_user.id,
        "text": message.text
    }
    # Enviamos el mensaje de los 5.9K miembros al sitio web
    try:
        requests.post(NODE_SERVER_URL, json=data)
    except:
        print("Error: El servidor de Martín Mp no está escuchando.")

print("🚀 MOTOR 2 (5.9K) INICIADO...")
bot.polling()
