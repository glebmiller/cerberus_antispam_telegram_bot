import logging
import random
from aiogram import Bot, Dispatcher, types
import asyncio
from time import sleep
import config

# Replace with your own Telegram Bot Token
BOT_TOKEN = config.BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
shuffle_options = True

welcome_message_text = "Welcome to the channel! To prove you're not a bot, please answer the following question:\nHow much is 42+27?"
correct_answer = "69"  # Correct answer is 69

@dp.message_handler(content_types=types.ContentType.LEFT_CHAT_MEMBER)
async def on_user_leave(message: types.Message):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_new_member(message: types.Message):
    print("message= ", message)
    
    username = message.from_user.username
    print("username = ", username)
    print("message.new_chat_members: = ", message.new_chat_members)
    for user in message.new_chat_members:
        if user.id == (await bot.me).id:
            continue
        if user.id not in dp.data:  # Check if the user is new
            # Check if the message is the default "joined the chat" message
            
            keyboard = types.InlineKeyboardMarkup()
            options = ["69", "42", "27", "500"]
            if shuffle_options:
                random.shuffle(options)

            for option in options:
                keyboard.add(types.InlineKeyboardButton(text=option, callback_data=option))
            if isinstance(username, str):
                welcome_text = username + ', ' + welcome_message_text
            else:
                welcome_text = welcome_message_text
            welcome_message = await bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)
            user_data = {"user_id": user.id, "welcome_message_id": welcome_message.message_id}
            print('user_data = ', user_data)
            dp.data[user.id] = user_data  # Store user data for future reference

            # Mute the new user
            permissions = types.ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(message.chat.id, user.id, permissions)
            timer = asyncio.create_task(delete_welcome_message(message, message.from_user.id, user_data))

    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

@dp.callback_query_handler(lambda query: query.data == correct_answer)
async def process_correct_answer(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_data = dp.data.get(user_id)
    
    if user_data:
        await query.answer("Correct answer! You are now unmuted.")
        permissions = types.ChatPermissions(can_send_messages=True)
        await bot.restrict_chat_member(query.message.chat.id, user_id, permissions)
        await bot.delete_message(query.message.chat.id, user_data["welcome_message_id"])
        del dp.data[user_id]

@dp.callback_query_handler(lambda query: query.data != correct_answer)
async def process_incorrect_answer(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_data = dp.data.get(user_id)
    
    if user_data:
        await query.answer("Incorrect answer! You are banned from the channel.")
        await bot.kick_chat_member(query.message.chat.id, user_id)
        await bot.delete_message(query.message.chat.id, user_data["welcome_message_id"])
        del dp.data[user_id]

async def delete_welcome_message(message: types.Message, user_id: int, user_data):

    await asyncio.sleep(60)
    
    # Check if the welcome message still exists
    if "welcome_message_id" in user_data:
        #print('"welcome_message_id" in user_data:')
        try:
            await bot.delete_message(message.chat.id, user_data["welcome_message_id"])
        except Exception as e:
            print(f"Error deleting welcome message: {e}")

if __name__ == '__main__':
    from aiogram import executor
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            #Wait for a minute before reconnecting
            sleep(5)

