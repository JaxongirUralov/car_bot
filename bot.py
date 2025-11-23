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

# ------------------------------------------
# CONFIG
# ------------------------------------------
BOT_TOKEN = "YOUR_TOKEN_HERE"
ADMINS = [261688257]

CAR_MODELS = ["S", "H", "V"]
OPTIONS = ["LS", "LT", "Premier"]
COLORS = ["white", "black", "silver", "red", "blue"]
# ------------------------------------------


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


# 3) COLOR → CONFIRM SCREEN
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


# Confirmation handler
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":")[1]

    if choice == "yes":
        await query.edit_message_text("Iltimos ismingizni kiriting:")
        return ASK_NAME

    if choice == "no":
        keyboard = [[InlineKeyboardButton(model, callback_data=f"model:{model}")]
                    for model in CAR_MODELS]

        await query.edit_message_text(
            "Qayta tanlang:\nQuyidagi modellardan birini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END


# 4) NAME
async def ask_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Endi familiyangizni kiriting:")
    return ASK_LASTNAME


# 5) LAST NAME → phone
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return ASK_PHONE


# 6) SAVE ORDER
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    add_order(
        user_id,
        context.user_data['first_name'],
        context.user_data['last_name'],
        update.message.text,
        context.user_data['model'],
        context.user_data['option'],
        context.user_data['color']
    )

    await update.message.reply_text("✔ Buyurtma saqlandi!")
    return ConversationHandler.END


# ADMIN
async def admin(update: Update, context: ContextT
