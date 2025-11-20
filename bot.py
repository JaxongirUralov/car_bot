from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import os
print("RUNNING BOT.PY FROM THIS DIRECTORY:", os.getcwd())
from database import init_db, add_order, get_orders, delete_order

BOT_TOKEN = "8529614987:AAGcJgGU3n_9so1F-KTAv_9-A888rv72Z40"
ADMINS = [261688257]  # replace with your Telegram ID

CAR_MODELS = ["Malibu", "Tracker", "Cobalt", "Gentra", "Damas"]
COLORS = ["white", "black", "silver", "red", "blue"]

# /start
# /start
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START FUNCTION WAS CALLED")  # debug

    keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")]
                for model in CAR_MODELS]

    await update.message.reply_text(
        "Choose a car model:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Model selected
async def select_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model = query.data.split(":")[1]
    context.user_data["model"] = model

    keyboard = [[InlineKeyboardButton(color, callback_data=f"color:{color}")]
                for color in COLORS]

    await query.edit_message_text(
        f"Selected model: {model}\n\nChoose a color:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Color selected → save order
async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    color = query.data.split(":")[1]
    model = context.user_data["model"]
    user_id = query.from_user.id

    add_order(user_id, model, color)

    await query.edit_message_text(
        f"✔ Your order is saved!\n\nModel: {model}\nColor: {color}"
    )

# /admin panel
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMINS:
        return await update.message.reply_text("❌ You are not admin.")

    keyboard = [
        [InlineKeyboardButton("📋 View Orders", callback_data="admin:orders")],
        [InlineKeyboardButton("❌ Delete Order", callback_data="admin:delete")]
    ]

    await update.message.reply_text(
        "Admin Panel:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Admin actions
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # Show orders
    if data == "admin:orders":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("No orders yet.")

        text = "📋 *Orders List:*\n\n"
        for oid, uid, model, color in orders:
            text += f"ID {oid} → User {uid}: {model} - {color}\n"

        return await query.edit_message_text(text, parse_mode="Markdown")

    # Delete order (list IDs)
    if data == "admin:delete":
        orders = get_orders()
        if not orders:
            return await query.edit_message_text("No orders to delete.")

        keyboard = [
            [InlineKeyboardButton(f"Delete ID {oid}", callback_data=f"delete:{oid}")]
            for oid, _, _, _ in orders
        ]

        return await query.edit_message_text(
            "Select order to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Confirm delete
async def delete_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split(":")[1])
    delete_order(order_id)

    await query.edit_message_text(f"✔ Order {order_id} deleted.")

async def wrong_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please use the buttons instead of typing text 🙂"
    )

# MAIN
def main():
    
    print("MAIN FUNCTION STARTED")    # <--- ADD THIS

    init_db()  # Create DB if not exists

    print("AFTER INIT_DB")           # <--- ADD THIS

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    print("APP BUILT")               # <--- ADD THIS
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(CallbackQueryHandler(select_color, pattern="^model:"))
    app.add_handler(CallbackQueryHandler(save_order, pattern="^color:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(delete_order_callback, pattern="^delete:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
