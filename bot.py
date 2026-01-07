# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
import logging
import os

from database import init_db, add_order, get_orders, get_supplier_orders, delete_order

# ---------- CONFIG ----------
BOT_TOKEN = "8529614987:AAGcJgGU3n_9so1F-KTAv_9-A888rv72Z40"  # replace if needed
SUPER_ADMINS = [261688257]  # fill with your super-admin Telegram IDs

# supplier_name -> [telegram_id, ...]
SUPPLIER_ADMINS = {
    "Tyre_Co": [261688257],    # add real Telegram IDs here
    "Lamp_Co": [],
    "Wind_Co": [],
    "Roof_Co": [],
    "Sunroof_Co": []
}

CAR_MODELS = ["S", "H", "V"]
OPTIONS = ["LS", "LT", "Premier"]
COLORS = ["white", "black", "silver", "red", "blue"]
# ----------------------------

ASK_NAME, ASK_LASTNAME, ASK_PHONE = range(3)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# -------------------------
# User flow
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"model:{m}")] for m in CAR_MODELS]
    await update.message.reply_text("Choose a car model:", reply_markup=InlineKeyboardMarkup(keyboard))


async def select_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    model = q.data.split(":", 1)[1]
    context.user_data["model"] = model
    keyboard = [[InlineKeyboardButton(o, callback_data=f"option:{o}")] for o in OPTIONS]
    await q.edit_message_text(f"Selected model: {model}\nChoose an option:", reply_markup=InlineKeyboardMarkup(keyboard))


async def select_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    option = q.data.split(":", 1)[1]
    context.user_data["option"] = option
    keyboard = [[InlineKeyboardButton(c, callback_data=f"color:{c}")] for c in COLORS]
    await q.edit_message_text(f"Selected option: {option}\nChoose a color:", reply_markup=InlineKeyboardMarkup(keyboard))


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    color = q.data.split(":", 1)[1]
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
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data.split(":", 1)[1]
    if choice == "yes":
        await q.edit_message_text("Iltimos ismingizni kiriting:")
        return ASK_NAME
    # no -> restart
    keyboard = [[InlineKeyboardButton(m, callback_data=f"model:{m}")] for m in CAR_MODELS]
    await q.edit_message_text("Qayta tanlang:\nQuyidagi modellardan birini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Endi familiyangizni kiriting:")
    return ASK_LASTNAME


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting (masalan: +998 90 123 45 67):")
    return ASK_PHONE


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    first = context.user_data.get("first_name", "")
    last = context.user_data.get("last_name", "")
    phone = update.message.text
    model = context.user_data.get("model")
    option = context.user_data.get("option")
    color = context.user_data.get("color")

    if not (model and option and color):
        await update.message.reply_text("Buyurtma ma'lumotlari yetarli emas. Iltimos /start bilan qayta boshlang.")
        return ConversationHandler.END

    add_order(user_id, first, last, phone, model, option, color)
    await update.message.reply_text("✔ Buyurtma saqlandi! Rahmat.")
    return ConversationHandler.END


async def wrong_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Iltimos tugmalardan foydalaning 🙂")


# -------------------------
# Admin functionality
# -------------------------
def fmt_order(r):
    # id, user_id, first, last, phone, model, option, color, created_at
    oid, uid, first, last, phone, model, option, color, created_at = r
    return f"🆔 {oid} — {first} {last} ({phone})\n🚗 {model}/{option}/{color}\n⏱ {created_at}\n"


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # super admin
    if user_id in SUPER_ADMINS:
        keyboard = [
            [InlineKeyboardButton("📋 All orders", callback_data="admin:all_orders")],
            [InlineKeyboardButton("🏭 View by supplier", callback_data="admin:choose_supplier")],
            [InlineKeyboardButton("❌ Delete order", callback_data="admin:delete")]
        ]
        return await update.message.reply_text("Super Admin panel:", reply_markup=InlineKeyboardMarkup(keyboard))

    # supplier admin
    for supplier_name, ids in SUPPLIER_ADMINS.items():
        if user_id in ids:
            rows = get_supplier_orders(supplier_name)
            if not rows:
                return await update.message.reply_text(f"No orders for {supplier_name}.")
            text = f"🏭 {supplier_name} orders:\n\n"
            for row in rows:
                so_id, order_id, supplier, part, qty, s_created, o_first, o_last, o_phone, o_model, o_option, o_color, o_created = row
                text += f"Order {order_id}: {part} ×{qty} — {o_first} {o_last} ({o_phone}) — {o_model}/{o_option}/{o_color} — {o_created}\n"
            return await update.message.reply_text(text)

    return await update.message.reply_text("❌ You are not admin.")


async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # all orders
    if data == "admin:all_orders":
        rows = get_orders()
        if not rows:
            return await q.edit_message_text("No orders yet.")
        text = "📋 All orders:\n\n" + "\n----------------\n".join(fmt_order(r) for r in rows)
        return await q.edit_message_text(text)

    if data == "admin:choose_supplier":
        keyboard = [[InlineKeyboardButton(s, callback_data=f"supplier_view:{s}")] for s in SUPPLIER_ADMINS.keys()]
        return await q.edit_message_text("Choose supplier to view:", reply_markup=InlineKeyboardMarkup(keyboard))

    if data.startswith("supplier_view:"):
        supplier_name = data.split(":", 1)[1]
        rows = get_supplier_orders(supplier_name)
        if not rows:
            return await q.edit_message_text(f"No orders for {supplier_name}.")
        text = f"🏭 {supplier_name} orders:\n\n"
        for row in rows:
            so_id, order_id, supplier, part, qty, s_created, o_first, o_last, o_phone, o_model, o_option, o_color, o_created = row
            text += f"Order {order_id}: {part} ×{qty} — {o_first} {o_last} ({o_phone}) — {o_model}/{o_option}/{o_color} — {o_created}\n"
        return await q.edit_message_text(text)

    if data == "admin:delete":
        rows = get_orders()
        if not rows:
            return await q.edit_message_text("No orders to delete.")
        keyboard = [[InlineKeyboardButton(f"Delete ID {r[0]}", callback_data=f"delete:{r[0]}")] for r in rows]
        return await q.edit_message_text("Select order to delete:", reply_markup=InlineKeyboardMarkup(keyboard))

    if data.startswith("delete:"):
        oid = int(data.split(":", 1)[1])
        delete_order(oid)
        return await q.edit_message_text(f"✔ Order {oid} deleted.")


# -------------------------
# MAIN
# -------------------------
def main():
    init_db()
    log.info("DB initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_confirmation, pattern="^confirm:")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_lastname)],
            ASK_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_order)],
        },
        fallbacks=[]
    )
    app.add_handler(conv)

    # user flow
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_option, pattern="^model:"))
    app.add_handler(CallbackQueryHandler(select_color, pattern="^option:"))
    app.add_handler(CallbackQueryHandler(confirm_order, pattern="^color:"))
    app.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm:"))

    # admin handlers
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^supplier_view:"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^delete:"))

    # last fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_message))

    log.info("Starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
