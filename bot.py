# NEW conversation states
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

BOT_TOKEN = "8529614987:AAGcJgGU3n_9so1F-KTAv_9-A888rv72Z40"
ADMINS = [261688257]
CAR_MODELS = ["Malibu", "Tracker", "Cobalt", "Gentra", "Damas"]
COLORS = ["white", "black", "silver", "red", "blue"]


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")]
                for model in CAR_MODELS]
    await update.message.reply_text("Choose a car model:", reply_markup=InlineKeyboardMarkup(keyboard))


# Model selected
async def select_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    model = query.data.split(":")[1]
    context.user_data["model"] = model

    keyboard = [[InlineKeyboardButton(color, callback_data=f"color:{color}")]
                for color in COLORS]
    await query.edit_message_text(f"Selected model: {model}\nChoose a color:", reply_markup=InlineKeyboardMarkup(keyboard))


# Color selected → ask for name
async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["color"] = query.data.split(":")[1]
    await query.edit_message_text("Please enter your *first name*:", parse_mode="Markdown")
    return ASK_NAME


async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Now enter your *last name*:", parse_mode="Markdown")
    return ASK_LASTNAME


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Please enter your phone number (example: +998 90 123 45 67)")
    return ASK_PHONE


# Final step — save to DB
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_order(
        user_id,
        context.user_data['first_name'],
        context.user_data['last_name'],
        update.message.text,
        context.user_data['model'],
        context.user_data['color']
    )
    await update.message.reply_text("✔ Order saved!")
    return ConversationHandler.END


# /admin — SHOW BUTTONS ONLY
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return await update.message.reply_text("❌ You are not admin.")

    keyboard = [
        [InlineKeyboardButton("📋 View Orders", callback_data="admin:orders")],
        [InlineKeyboardButton("❌ Delete Order", callback_data="admin:delete")]
    ]
    await update.message.reply_text("Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))


# Admin actions
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    print("ADMIN ACTION:", data)  # DEBUG — GOOD!

    if data == "admin:orders":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("No orders yet.")

        text = "\n".join([
            f"ID {oid} → {first} {last} ({phone}) : {model} - {color}"
            for oid, uid, first, last, phone, model, color in orders
        ])

        return await query.edit_message_text(text)

    if data == "admin:delete":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("No orders to delete.")

        keyboard = [[InlineKeyboardButton(f"Delete ID {oid}", callback_data=f"delete:{oid}")]
                    for oid, _, _, _ in orders]
        return await query.edit_message_text("Select order to delete:", reply_markup=InlineKeyboardMarkup(keyboard))


async def delete_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    delete_order(int(query.data.split(":")[1]))
    await query.edit_message_text("✔ Order deleted.")


async def wrong_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please use buttons 🙂")


# MAIN
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(save_order, pattern="^color:")],
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
    app.add_handler(CallbackQueryHandler(select_color, pattern="^model:"))
    app.add_handler(CallbackQueryHandler(save_order, pattern="^color:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(delete_order_callback, pattern="^delete:"))

    # always last!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_message))

    print("Bot is running with webhook...")
    WEBHOOK_URL = "https://carbot-production.up.railway.app"
    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 8080)),
                    url_path=BOT_TOKEN, webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}")


if __name__ == "__main__":
    main()
