import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'ravinsight.settings'
django.setup()

import logging
import json
from ravinsight.web_constant import Space_Group_ID, COMMUNITY_URL
from apps.users.models import TelegramUserData, User
from apps.atpace_community.models import Spaces, Post
from telegram.utils.request import Request
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from datetime import datetime
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext,
)

API_KEY = "5869646121:AAF3WUxlyTvpXlpEyCySCNwewPUk-UlGxzE"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

print("bot start")


def handle_document(update, context):
    user = update.message.from_user
    # db_user = User.objects.filter(first_name__icontains=user.first_name)
    # telegram_user = TelegramUserData.objects.create(user_id=user.id, username=user.first_name, file)
    # telegram_user = TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=text, message_id=message_id, chat_type=update.message.chat.type)
    update.message.reply_text(f"Hi {update['message']['chat']['first_name']}, "
            "My name is Peace Bot. Send /help if you need any help\nwhat to do with this document")
    

def start():
    pass

def help(update, context):
    text = str(update.message.text).lower()
    print(text)
    logger.info("help command")
    old_message = update.to_json()
    message = json.loads(old_message)
    user = update.message.from_user
    db_user = User.objects.filter(first_name__icontains=user.first_name)
    TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=update.message.text, message_id=update.message.message_id, is_command=True, chat_type=update.message.chat.type)
    if update.message.chat.type == "private":
        update.message.reply_text(f"Hi {update['message']['chat']['first_name']}, " 
        "Please contact to Info@growatpace.com for more information.")
    else:
        update.message.reply_text(f"Hi {message['message']['from']['first_name']}, "
        "Please contact to Info@growatpace.com for more information.\n"
        "type /cancel to close the conversation")

def greet_message(update, context):
    text = str(update.message.text).lower()
    print(text)
    logger.info("help command")
    old_message = update.to_json()
    message = json.loads(old_message)
    user = update.message.from_user
    db_user = User.objects.filter(first_name__icontains=user.first_name)
    TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=update.message.text, message_id=update.message.message_id, is_command=True, chat_type=update.message.chat.type)
    if update.message.chat.type == "private":
        update.message.reply_text(f"Hi {update['message']['chat']['first_name']}, "
        "My name is Peace Bot. Send /help if you need any help")
    else:
        update.message.reply_text(f"Hi {message['message']['from']['first_name']}, "
        "My name is Peace Bot. Send /help if you need any help")

def handle_message(update, context):
    text = str(update.message.text).lower()
    logger.info("message handling")
    old_message = update.to_json()
    message = json.loads(old_message)
    print(message)
    if update.message.chat.type == "private":
        update.message.reply_text(f"Hi {update['message']['chat']['first_name']}, "
        "My name is Peace Bot. Send /help if you need any help")
    else:
        user = update.message.from_user
        db_user = User.objects.filter(first_name__icontains=user.first_name)
        text = message['message']['text']
        # print(f"text: {text}")
        message_id = update.message.message_id
        telegram_user = TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=text, message_id=message_id)
        print(f"user_id: {user.id}, message_id: {message_id}")
        if message['message']['entities'] and message['message']['entities'][0]['type'] == "url":
            telegram_user.url_link = True
            telegram_user.save()
            reply_keyboard = [["Yes", "No"]]
            update.message.reply_text(
                f"Hi {message['message']['from']['first_name']}, "
                "Shall I post it on forum?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True, input_field_placeholder="Yes or No?"
                ),
            )

def post_reply(update, context):
    text = str(update.message.text).lower()
    logger.info("message handling")
    print(text)
    print(update.message)
    user = update.message.from_user
    db_user = User.objects.filter(first_name__icontains=user.first_name)
    message_id = update.message.message_id
    print(f"user_id: {user.id}, message_id: {message_id}")
    logger.info(f"Ans of {user.first_name}: {update.message.text}")
    old_message = update.to_json()
    message = json.loads(old_message)
    telegram_channel_id = None
    if update.message.chat.type == "group":
        telegram_channel_id = update.message.chat.id
    if text in {"Yes", "yes"}:
        telegram_user = TelegramUserData.objects.filter(user_id=user.id, message_id__lt=message_id).first()
        print(f"telegram_user.url_link {telegram_user.url_link}")
        if telegram_user.url_link:
            space = Spaces.objects.get(id="d3f1459e-83f8-4908-bee2-b012cab397e5")
            post = Post.objects.create(title=f"Telegram Post By {user.first_name}", Body=telegram_user.description, space=space, space_group=space.space_group, created_by=space.created_by)
            post_url = f"{COMMUNITY_URL}/post-details/{post.id}"
            print(post_url)
            telegram_user = TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=text, message_id=message_id)
            update.message.reply_text(f"Thanks, We have posted your message on forum with **{post.title}**\nHere is the link for post detail\n\n{post_url}", reply_markup=ReplyKeyboardRemove())
    else:
        db_user = User.objects.filter(first_name__icontains=user.first_name)
        telegram_user = TelegramUserData.objects.filter(user_id=user.id, message_id__lt=message_id).first()
        if telegram_user.url_link:
            TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=text, message_id=message_id)
            update.message.reply_text("Thanks for the answer!", reply_markup=ReplyKeyboardRemove())


def cancel(update, context):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=update.message.text, message_id=update.message.message_id, is_command=True)
    update.message.reply_text(
        "Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END

def get_time(update, context):
    print(update.message.text)
    user = update.message.from_user
    current_date_time = datetime.now()
    TelegramUserData.objects.create(user_id=user.id, username=user.first_name, description=update.message.text, message_id=update.message.message_id, is_command=True)
    update.message.reply_text(f"current time is {current_date_time}")


if __name__ == '__main__':
    req = Request(connect_timeout=0.5)
    bot = Bot(token=API_KEY, request=req)
    updater = Updater(API_KEY, use_context=True)
    application = updater.dispatcher
    # bot.set_my_commands(["getcurrenttime"])
    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("start", start)],
    #     states={
    #         GENDER: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
    #         PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("skip", skip_photo)],
    #         LOCATION: [
    #             MessageHandler(filters.LOCATION, location),
    #             CommandHandler("skip", skip_location),
    #         ],
    #         BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
    #     },
    #     fallbacks=[CommandHandler("cancel", cancel)],
    # )

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("getcurrenttime", get_time))
    application.add_handler(MessageHandler(Filters.document, handle_document))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(Filters.regex("^(Yes|No|yes|no)$"), post_reply))
    application.add_handler(MessageHandler(Filters.regex("^(Hi|Hey|Hello|hi|hy|hello|hey)$"), greet_message))
    application.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling(1.0)
    updater.idle


