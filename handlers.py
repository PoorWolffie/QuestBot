from db import quest_time_enabled, register_time_enabled



def quest_enabled(func):
    async def wrapper(update, context, *args, **kwargs):
        if not quest_time_enabled():
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Quest time is currently disabled.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def register_enabled(func):
    async def wrapper(update, context, *args, **kwargs):
        if not register_time_enabled():
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Registration time is currently disabled.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def private_chat_only(func):
    async def wrapper(update, context, *args, **kwargs):
        if update.effective_chat.type != "private":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="This command can only be used in private chats.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper