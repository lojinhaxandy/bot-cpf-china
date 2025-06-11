from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from keep_alive import manter_online
from config import TOKEN
from database import pegar_cpfs, remover_cpfs, contar_estoque, adicionar_cpfs
from pagamento import gerar_link_pagamento, verificar_pagamento
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

user_pagamentos = {{}}
aguardando_qtd = set()

def menu_principal():
    botoes = [
        [InlineKeyboardButton("🛒 Comprar CPFs", callback_data="comprar")],
        [InlineKeyboardButton("✅ Verificar pagamento", callback_data="verificar")],
        [InlineKeyboardButton("❓ Ajuda", callback_data="ajuda")],
        [InlineKeyboardButton("📩 Suporte Telegram", url="https://t.me/cpfbotttchina")],
    ]
    return InlineKeyboardMarkup(botoes)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estoque = contar_estoque()
    texto = (
        f"🧾 Bem-vindo ao bot!\n"
        f"Cada CPF custa R$ 0,25.\n"
        f"Estoque atual: {{estoque}} CPFs\n\n"
        "Use o menu abaixo para navegar:"
    )
    await update.message.reply_text(texto, reply_markup=menu_principal())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "comprar":
        botoes = [[InlineKeyboardButton(str(i), callback_data=str(i))] for i in range(1, 6)]
        botoes.append([InlineKeyboardButton("Digite a quantidade", callback_data="digitar")])
        markup = InlineKeyboardMarkup(botoes)
        await query.edit_message_text("Escolha a quantidade:", reply_markup=markup)

    elif data == "verificar":
        await verificar(update, context)

    elif data == "ajuda":
        await query.edit_message_text(
            "🤖 Comandos disponíveis:\n"
            "/start - Reiniciar menu\n"
            "Use os botões para comprar CPFs ou verificar pagamento."
        )

    elif data == "digitar":
        aguardando_qtd.add(user_id)
        await query.edit_message_text("Digite a quantidade de CPFs que deseja comprar:")

    elif data.isdigit():
        qtd = int(data)
        await processar_pagamento(update, qtd)

async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in aguardando_qtd:
        text = update.message.text
        if not text.isdigit():
            await update.message.reply_text("❌ Por favor, digite um número válido.")
            return
        qtd = int(text)
        if qtd < 1:
            await update.message.reply_text("❌ A quantidade deve ser pelo menos 1.")
            return
        aguardando_qtd.remove(user_id)
        await processar_pagamento(update, qtd)
        return

    estoque = contar_estoque()
    texto = (
        "👤 *Bem-vindo ao Bot de CPFs para China!*\n\n"
        "💸 *Preço:* R$ 0,25 por CPF\n"
        "📄 *Produto:* CPF PARA CHINA\n"
        "✅ *Compatível com:* GoBank, FastBank\n\n"
        f"📦 *Estoque atual:* {{estoque}} CPFs\n\n"
        "👇 Use o menu abaixo para navegar e realizar sua compra."
    )
    await update.message.reply_text(text=texto, reply_markup=menu_principal(), parse_mode="Markdown")

async def processar_pagamento(update, qtd):
    preco = qtd * 0.25
    user_id = update.effective_user.id
    link, external_ref = gerar_link_pagamento(preco, user_id, qtd)
    user_pagamentos[user_id] = {{"qtd": qtd, "external_ref": external_ref}}

    mensagem = (
        f"💰 Total: R$ {{preco:.2f}}. Pague no link abaixo:\n{{link}}\n\n"
        "✅ Após o pagamento, clique em 'Verificar pagamento' no menu."
    )

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(mensagem)
    elif hasattr(update, 'message') and update.message:
        await update.message.reply_text(mensagem)

async def verificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, 'callback_query') and update.callback_query:
        user_id = update.callback_query.from_user.id
        chat = update.callback_query.message.chat
    else:
        user_id = update.message.from_user.id
        chat = update.message.chat

    if user_id not in user_pagamentos:
        await context.bot.send_message(chat_id=chat.id, text="⚠️ Você ainda não fez um pedido.")
        return

    external_ref = user_pagamentos[user_id]['external_ref']
    qtd = user_pagamentos[user_id]['qtd']

    if verificar_pagamento(external_ref):
        cpfs = pegar_cpfs(qtd)
        remover_cpfs(cpfs)

        filename = f"cpfs_{{user_id}}.txt"
        with open(filename, "w") as f:
            f.write('\n'.join(cpfs))

        await context.bot.send_message(chat_id=chat.id, text="✅ Pagamento confirmado! Aqui está seu arquivo com os CPFs:")
        with open(filename, "rb") as f:
            await context.bot.send_document(chat_id=chat.id, document=f)

        os.remove(filename)
        del user_pagamentos[user_id]
    else:
        await context.bot.send_message(chat_id=chat.id, text="❌ Pagamento ainda não foi confirmado. Tente novamente em 1 minuto.")

def main():
    manter_online()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), receber_texto))

    app.run_polling()

if __name__ == "__main__":
    main()
