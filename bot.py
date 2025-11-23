from telegram.ext import ConversationHandler
ASK_NAME, ASK_LASTNAME, ASK_PHONE = range(3)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

import os
print("RUNNING BOT.PY FROM THIS DIRECTORY:", os.getcwd())

from database import init_db, add_order, get_orders, delete_order


# ----------------------
# CONFIG
# ----------------------
BOT_TOKEN = "8529614987:AAGcJgGU3n_9so1F-KTAv_9-A888rv72Z40"
ADMINS = [261688257]

CAR_MODELS = ["S", "H", "V"]
OPTIONS = ["LS", "LT", "Premier"]
COLORS = ["white", "black", "silver", "red", "blue"]
# ----------------------


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")]
                for model in CAR_MODELS]
    await update.message.reply_text("Choose a car model:", reply_markup=InlineKeyboardMarkup(keyboard))


# 1) MODEL → OPTION
async def select_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model = query.data.split(":")[1]
    context.user_data["model"] = model

    keyboard = [[InlineKeyboardButton(option, callback_data=f"option:{option}")]
                for option in OPTIONS]

    await query.edit_message_text(
        f"Selected model: {model}\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 2) OPTION → COLOR
async def select_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    option = query.data.split(":")[1]
    context.user_data["option"] = option

    keyboard = [[InlineKeyboardButton(color, callback_data=f"color:{color}")]
                for color in COLORS]

    await query.edit_message_text(
        f"Selected option: {option}\nChoose a color:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 3) COLOR → CONFIRM
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    color = query.data.split(":")[1]
    context.user_data["color"] = color

    model = context.user_data["model"]
    option = context.user_data["option"]

    text = (
        "Siz quyidagi avtoni tanladingiz:\n\n"
        f"🚗 Model: {model}\n"
        f"⚙️ Option: {option}\n"
        f"🎨 Rang: {color}\n\n"
        "Iltimos ma’lumotlarni tekshiring va buyurtmani tasdiqlang."
    )

    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm:yes")],
        [InlineKeyboardButton("🔄 Qayta tanlash", callback_data="confirm:no")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# Confirm handler
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":")[1]

    if choice == "yes":
        await query.edit_message_text("Iltimos ismingizni kiriting:")
        return ASK_NAME

    if choice == "no":
        keyboard = [[InlineKeyboardButton(m, callback_data=f"model:{m}")]
                    for m in CAR_MODELS]

        await query.edit_message_text(
            "Qayta tanlang:\nQuyidagi modellardan birini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END


# 4) Ask lastname
async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Endi familiyangizni kiriting:")
    return ASK_LASTNAME


# 5) Ask phone
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return ASK_PHONE


# 6) Save to DB
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    add_order(
        user_id,
        context.user_data["first_name"],
        context.user_data["last_name"],
        update.message.text,
        context.user_data["model"],
        context.user_data["option"],
        context.user_data["color"]
    )

    await update.message.reply_text("✔ Buyurtma saqlandi!")
    return ConversationHandler.END


# Admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return await update.message.reply_text("❌ Siz admin emassiz.")

    keyboard = [
        [InlineKeyboardButton("📋 Buyurtmalar ro'yxati", callback_data="admin:orders")],
        [InlineKeyboardButton("❌ Buyurtmani o‘chirish", callback_data="admin:delete")]
    ]

    await update.message.reply_text("Admin paneli:", reply_markup=InlineKeyboardMarkup(keyboard))


# Admin actions
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin:orders":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("Buyurtmalar yo‘q.")

        text = "\n\n".join([
            f"ID {oid}\n"
            f"{first} {last} ({phone})\n"
            f"{model} / {option} / {color}\n"
            f"🕒 {timestamp}"
            for oid, uid, first, last, phone, model, option, color, timestamp in orders
        ])

        return await query.edit_message_text(text)

    if data == "admin:delete":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("O‘chirish uchun buyurtma yo‘q.")

        keyboard = [
            [InlineKeyboardButton(f"Delete ID {oid}", callback_data=f"delete:{oid}")]
            for oid, *_ in orders
        ]

        return await query.edit_message_text(
            "Qaysi buyurtmani o‘chirmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard)
        )


# Delete order
async def delete_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    delete_order(int(query.data.split(":")[1]))
    await query.edit_message_text("✔ Buyurtma o‘chirildi.")


async def wrong_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Iltimos tugmalardan foydalaning 🙂")


# MAIN
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_confirmation, pattern="^confirm:")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
            ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_order)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(CallbackQueryHandler(select_option, pattern="^model:"))
    app.add_handler(CallbackQueryHandler(select_color, pattern="^option:"))
    app.add_handler(CallbackQueryHandler(confirm_order, pattern="^color:"))

    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(delete_order_callback, pattern="^delete:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_message))

    print("Bot running with webhook...")

    WEBHOOK_URL = "https://carbot-production.up.railway.app"

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )


if __name__ == "__main__":
    main()
