from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
        filters,
        MessageHandler,
        ApplicationBuilder,
        ContextTypes,
        CommandHandler,
        CallbackQueryHandler,
        ConversationHandler,
)
import os
from flask import Flask
from db import *
from uuid import uuid4
from handlers import *
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread


app = Flask(__name__)

@app.route("/kill")
def kill():

    return 1
@app.route("/")
def tcp():
    return "HEALTHY"


def run_app():
    app.run(host="0.0.0.0", port=8000)



def timee(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        msg_time = update.message.date
        global timeee
        if msg_time>timeee:
            return await func(update, context, *args, **kwargs)
        else:
            print('YA')
            return
    return wrapper


quest_data = {}
register_gc = get_register_chat_id()
quest_gc = get_quest_chat_id()
WAITING_POINTS, CONFIRM_POINTS, WAITING_REGISTER_APPROVAL = range(3)

@timee
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Quest Bot! Use /register to register yourself.\nUse /quest <options> to submit your completed quests.")

@timee
async def toggle_quest_time_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    toggle_quest_time()
    status = "enabled" if quest_time_enabled() else "disabled"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quest time has been {status}.")

@timee
async def toggle_register_time_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    toggle_register_time()
    status = "enabled" if register_time_enabled() else "disabled"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Registration time has been {status}.")

@timee
@private_chat_only
@register_enabled
async def register_user(update:Update, context:ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id
    if player_exists(userid):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are already registered to the game.")
    else:
        keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"reg_appr_{userid}")],
            [InlineKeyboardButton("Reject", callback_data=f"reg_rej_{userid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=register_gc, text=f"New player registration request from {update.effective_user.first_name} (ID: {userid}). Approve?", reply_markup=reply_markup)
        return WAITING_REGISTER_APPROVAL
    return ConversationHandler.END

async def register_approval_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    print(data)
    if data.startswith("reg_appr"):
        userid = int(data.split("_")[2])
        add_player(userid)
        await query.edit_message_text(text=f"User {userid} has been approved and added to the database.")
        await context.bot.send_message(chat_id=userid, text="Your registration has been approved! You are now in the database.")
    elif data.startswith("reg_rej"):
        userid = int(data.split("_")[2])
        await query.edit_message_text(text=f"User {userid} registration has been rejected.")
        await context.bot.send_message(chat_id=userid, text="Your registration has been rejected. Please contact the admin for more information.")
    return ConversationHandler.END
@timee
@private_chat_only
@quest_enabled
async def quest_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id
    text = update.message.text
    if player_exists(userid):
        pass
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not registered in the event. Please contact the admin.")
        return
    data = text.split(" ", 1)
    if len(data) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide options. Usage: /quest <options>")
        return
    else:
        options = data[1]
        quest_info = ' '.join(options.split()[1:])
        quest_info = quest_info.split()
        game_link = options.split()[0]
        message_id = update.message.message_id
        run_id = str(uuid4())
        quest_data[run_id] = {}
        quest_data[run_id]['message_id'] = message_id
        name = update.message.from_user.first_name
        quest_data[run_id]['userid'] = userid
        quest_data[run_id]['quest'] = quest_info
        quest_str = '\n'.join(quest_info)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your quest has been forwarded to the admins: {quest_str}")
        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=f"approve_{run_id}"),
                InlineKeyboardButton("Reject", callback_data=f"reject_{run_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        quest_str = '\n'.join(quest_info)
        quest_data[run_id]['points_initiated'] = False
        await context.bot.send_message(chat_id=quest_gc, text=f"Message from [{name}](tg://user?id={userid}): \nCompleted quest(s) \n{quest_str} \nin [game link]({game_link})", reply_markup=reply_markup, parse_mode=constants.ParseMode.MARKDOWN_V2)


async def points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    run_id = data.split("_", 1)[1]
    print(quest_data[run_id])
    if not quest_data[run_id]['points_initiated']:
        if data.startswith("approve_"):
            quest_data[run_id]['points_initiated'] = True
            userid = quest_data[run_id]['userid']
            quest_info = quest_data[run_id]['quest']
            quest_str = ';'.join(quest_info)
            quest_data[run_id]['easy_points'] = 0
            quest_data[run_id]['intermediate_points'] = 0
            quest_data[run_id]['hard_points'] = 0
            # Here you can define how many points each quest gives
           
        elif data.startswith("reject_"):
            await query.edit_message_text(text="Quest rejected.")
            del quest_data[run_id]
            quest_data[run_id]['easy_points'] = 0
            quest_data[run_id]['intermediate_points'] = 0
            quest_data[run_id]['hard_points'] = 0
            return ConversationHandler.END
    else:
            if data.startswith("cancel_"):
                await query.edit_message_text(text="Points assignment cancelled.")
                return ConversationHandler.END
            elif data.startswith("confirm_"):
                easy_points = quest_data[run_id]['easy_points']
                intermediate_points = quest_data[run_id]['intermediate_points']
                hard_points = quest_data[run_id]['hard_points']
                total_points = easy_points * 20 + intermediate_points * 40 + hard_points *60
                userid = quest_data[run_id]['userid']
                add_points(userid, total_points)
                await query.edit_message_text(text=f"Assigned {total_points} points to user {userid} for the quest.")
                await context.bot.send_message(chat_id=userid, text=f"You have been awarded {total_points} points for your quest submission!")
                del quest_data[run_id]
                return ConversationHandler.END
            elif data.startswith("clear_"):
                quest_data[run_id]['easy_points'] = 0
                quest_data[run_id]['intermediate_points'] = 0
                quest_data[run_id]['hard_points'] = 0
            userid = quest_data[run_id]['userid']
            quest_info = quest_data[run_id]['quest']
            quest_str = ';'.join(quest_info)
            if data.startswith("easy_"):
                quest_data[run_id]['easy_points']+=1
            elif data.startswith("intermediate_"):
                quest_data[run_id]['intermediate_points']+=1    
            elif data.startswith("hard_"):
                quest_data[run_id]['hard_points']+=1
    easy_points = quest_data[run_id]['easy_points']
    intermediate_points = quest_data[run_id]['intermediate_points']
    hard_points = quest_data[run_id]['hard_points']
    keyboard = [
        [
            InlineKeyboardButton(f"Easy - {easy_points}", callback_data=f"easy_{run_id}")
        ],
            [
                InlineKeyboardButton(f"Intermediate - {intermediate_points}", callback_data=f"intermediate_{run_id}")
            ],
        [
            InlineKeyboardButton(f"Hard - {hard_points}", callback_data=f"hard_{run_id}")
        ],
        [
            InlineKeyboardButton("Clear", callback_data=f"clear_{run_id}")
        ],
        [
            InlineKeyboardButton("Confirm", callback_data=f"confirm_{run_id}")
        ],
        [
            InlineKeyboardButton("Cancel", callback_data=f"cancel_{run_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Choose points for quest: {quest_str}", reply_markup=reply_markup)
    return WAITING_POINTS

async def get_points(update:Update, context:ContextTypes.DEFAULT_TYPE):
    data = update.message.text
    if data.split()[1].isdigit():
        userid = data.split()[1]
        points = get_player_points(userid)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"User {userid} has {points} points.")


if __name__ == '__main__':
    app = ApplicationBuilder().token("7931481444:AAHZqy0eWByV0qaqzIbGHU-RJdMpe3qKcJM").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register_user))
    quest_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(points_handler, pattern='^(approve_|reject)')],
        states={
            WAITING_POINTS: [CallbackQueryHandler(points_handler, pattern='^(easy_|intermediate_|hard_|confirm_|cancel_|clear_)')]
        },
        fallbacks=[]
    )
    register_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_approval_handler, pattern='^(reg_appr_|reg_rej_)')],
        states={
            WAITING_REGISTER_APPROVAL: [CallbackQueryHandler(register_approval_handler, pattern='^(reg_appr|reg_rej)$')]
        },
        fallbacks=[]
    )
    app.add_handler(CommandHandler("quest", quest_handler))
    app.add_handler(register_conv_handler)
    app.add_handler(quest_conv_handler)
    app.add_handler(CommandHandler("questing", toggle_quest_time_handler))
    app.add_handler(CommandHandler("registration", toggle_register_time_handler))
    app.add_handler(CommandHandler("getpoints", get_points))
    global timeee
    timeee = datetime.now(pytz.utc).replace(microsecond=0)
    Thread(target=run_app).start()
    print("Bot started successfully.")
    app.run_polling()