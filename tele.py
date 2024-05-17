

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, Updater, CallbackContext



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")

async def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")

def start(update:Update, context: CallbackContext) -> None:
    """Start the loop to send messages"""
    context.job_queue.run_repeating(alarm, interval=1, first=0, context=context)


# Replace with your bot token
def main():
    """Start the bot."""

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set", start))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    TOKEN = '7108794076:AAHwGv4QsvujDyvlEE2aR7A447Myg-ocH5k'

    main()