# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
import os
import logging

# import DB functions (from your database.py)
from database import init_db, add_order, get_orders, get_supplier_orders, delete_order

# ---------- CONFIG ----------
BOT_TOKEN = "8529614987:AAGcJgGU3n_9so1F-KTAv_9-A888rv72Z40"  # <- CHANGE if needed
SUPER_ADMINS = [261688257]  # Telegram IDs of super admins

# Supplier admins mapping: supplier_name -> list of telegram IDs
# Fill these lists with real Telegram IDs of supplier admins.
SUPPLIER_ADMINS = {
    "Tyre_Co": [],      # e.g. [1111111, 2222222]
    "Lamp_Co": [],
    "Wind_Co": [],
    "Roof_Co": [],
    "Sunroof_Co": []
}
# ----------------------------

# Conversation states
ASK_NAME, ASK_LASTNAME, ASK_PHONE = range(3)

# Example UI data (models/options/colors) — keep in sync with DB SUPPLIER_DATA
CAR_MODELS = ["S", "H", "V"]
OPTIONS = ["LS", "LT", "Premier"]
COLORS = ["white", "black", "silver", "red", "blue"]

# logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# -------------------------
# Handlers: user flow
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")]
                for model in CAR_MODELS]
    await update.message.reply_text("Choose a car model:", reply_markup=InlineKeyboardMarkup(keyboard))


# model -> show options
async def select_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model = query.data.split(":", 1)[1]
    context.user_data["model"] = model

    keyboard = [[InlineKeyboardButton(opt, callback_data=f"option:{opt}")]
                for opt in OPTIONS]

    await query.edit_message_text(
        f"Selected model: {model}\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# option -> show colors
async def select_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    option = query.data.split(":", 1)[1]
    context.user_data["option"] = option

    keyboard = [[InlineKeyboardButton(color, callback_data=f"color:{color}")]
                for color in COLORS]

    await query.edit_message_text(
        f"Selected option: {option}\nChoose a color:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# color -> confirmation screen
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    color = query.data.split(":", 1)[1]
    context.user_data["color"] = color

    model = context.user_data.get("model")
    option = context.user_data.get("option")

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


# handle confirmation: yes -> ask name; no -> restart models
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":", 1)[1]

    if choice == "yes":
        await query.edit_message_text("Iltimos ismingizni kiriting:")
        return ASK_NAME

    # choice == "no"
    keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")] for model in CAR_MODELS]
    await query.edit_message_text("Qayta tanlang:\nQuyidagi modellardan birini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


# ask lastname
async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Endi familiyangizni kiriting:")
    return ASK_LASTNAME


# ask phone
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting (masalan: +998 90 123 45 67):")
    return ASK_PHONE


# final step — save order (database.add_order handles creating supplier_orders)
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    first = context.user_data.get("first_name", "")
    last = context.user_data.get("last_name", "")
    phone = update.message.get_text() if update.message else ""

    model = context.user_data.get("model")
    option = context.user_data.get("option")
    color = context.user_data.get("color")

    if not (model and option and color):
        await update.message.reply_text("Buyurtma ma'lumotlari to'liq emas. Iltimos /start orqali qayta boshlang.")
        return ConversationHandler.END

    # add_order will also create supplier_orders (as your database.py is set up)
    add_order(user_id, first, last, phone, model, option, color)

    await update.message.reply_text("✔ Buyurtma saqlandi! Rahmat.")
    return ConversationHandler.END


# fallback text handler for when user types instead of pressing buttons
async def wrong_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Iltimos tugmalardan foydalaning 🙂")


# -------------------------
# Admin functionality
# -------------------------
def format_order_row(row):
    # row from get_orders(): id, user_id, first_name, last_name, phone, model, option, color, created_at
    oid, uid, first, last, phone, model, option, color, created_at = row
    created_at_str = created_at or ""
    return f"🆔 {oid} — {first} {last} ({phone})\n🚗 {model} / {option} / {color}\n⏱ {created_at_str}\n"


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # super admin
    if user_id in SUPER_ADMINS:
        keyboard = [
            [InlineKeyboardButton("📋 All orders", callback_data="admin:all_orders")],
            [InlineKeyboardButton("🏭 View by supplier", callback_data="admin:choose_supplier")],
            [InlineKeyboardButton("❌ Delete order", callback_data="admin:delete")]
        ]
        await update.message.reply_text("Super Admin panel:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # supplier admin
    for supplier_name, admins in SUPPLIER_ADMINS.items():
        if user_id in admins:
            rows = get_supplier_orders(supplier_name)
            if not rows:
                return await update.message.reply_text(f"No orders for {supplier_name}.")
            text = f"🏭 {supplier_name} orders:\n\n"
            for row in rows:
                # row: id, order_id, supplier, part, qty, created_at
                so_id, order_id, supplier, part, qty, created_at = row
                text += f"OrderID: {order_id} — {part} ×{qty}  ({created_at})\n"
            return await update.message.reply_text(text)

    # not admin
    await update.message.reply_text("❌ You are not admin.")


async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # super admin wants all orders
    if data == "admin:all_orders":
        rows = get_orders()
        if not rows:
            return await query.edit_message_text("No orders yet.")
        text = "📋 All orders:\n\n"
        for r in rows:
            text += format_order_row(r) + "-----------------\n"
        return await query.edit_message_text(text)

    # super admin choose supplier
    if data == "admin:choose_supplier":
        keyboard = [[InlineKeyboardButton(s, callback_data=f"supplier_view:{s}")] for s in SUPPLIER_ADMINS.keys()]
        return await query.edit_message_text("Choose supplier to view:", reply_markup=InlineKeyboardMarkup(keyboard))

    # super admin delete (show list with delete buttons)
    if data == "admin:delete":
        rows = get_orders()
        if not rows:
            return await query.edit_message_text("No orders to delete.")
        keyboard = [[InlineKeyboardButton(f"Delete ID {r[0]}", callback_data=f"delete:{r[0]}")] for r in rows]
        return await query.edit_message_text("Select order to delete:", reply_markup=InlineKeyboardMarkup(keyboard))

    # supplier selection from choose_supplier
    if data.startswith("supplier_view:"):
        supplier_name = data.split(":", 1)[1]
        rows = get_supplier_orders(supplier_name)
        if not rows:
            return await query.edit_message_text(f"No orders for {supplier_name}.")
        text = f"🏭 {supplier_name} orders:\n\n"
        for row in rows:
            so_id, order_id, supplier, part, qty, created_at = row
            text += f"OrderID: {order_id} — {part} ×{qty}  ({created_at})\n"
        return await query.edit_message_text(text)

    # delete order confirmation (admin pressed a delete ID)
    if data.startswith("delete:"):
        oid = int(data.split(":", 1)[1])
        delete_order(oid)
        return await query.edit_message_text(f"✔ Order {oid} deleted.")


# -------------------------
# MAIN
# -------------------------
def main():
    # init DB (creates tables if not exists)
    init_db()
    log.info("Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler: confirmation -> name -> lastname -> phone
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

    # User flow handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_option, pattern="^model:"))
    app.add_handler(CallbackQueryHandler(select_color, pattern="^option:"))
    app.add_handler(CallbackQueryHandler(confirm_order, pattern="^color:"))

    # Admin handlers
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^supplier_view:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^delete:"))

    # Always last: catch plain texts (tell user to use buttons)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_message))

    # Webhook config
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://carbot-production.up.railway.app")  # change if needed
    log.info("Bot starting webhook at %s", WEBHOOK_URL)

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )


if __name__ == "__main__":
    main()
