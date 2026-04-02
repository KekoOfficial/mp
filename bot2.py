import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import TOKEN_BOT_2 # Necesitas un nuevo Token de BotFather

async def chat_masivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    # Lógica: Reenviar el mensaje a la interfaz web del Imperio
    print(f"🌐 [GLOBAL CHAT] {user.first_name}: {text}")
    
    # Aquí guardaríamos en una DB o archivo dedicado al Chat Global
    with open("global_chat.log", "a", encoding="utf-8") as f:
        f.write(f"{user.id}|{user.first_name}|{text}\n")

async def main():
    app = Application.builder().token(TOKEN_BOT_2).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_masivo))
    
    print("🚀 BOT 2: ENGINE GLOBAL (5975 MIEMBROS) ONLINE")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
