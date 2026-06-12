from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

import credentials

user_message = None #Глобальна змінна для отримання запиту від користувача

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })


# Функція обробки выбору користувача
async def text_hendler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_user = context.user_data.get('mode')

    if current_user is None:
        # !!! Переробити gpt все одно працює просто в чаті !!!
        await send_text(update, context, "Щоб почати, виберіть щось з меню")
    elif current_user == 'random':
        await random(update, context)
    elif current_user == 'gpt':
        await gpt_handle_text(update, context)
    elif current_user == 'talk':
        await talk(update, context)


# Телеграм-бот повинен обробляти команду /random.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT із заздалегідь підготовленим промптом.
# Відповідь ChatGPT потрібно отримати та передати користувачеві.
# До повідомлення має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start.
# І кнопка "Хочу ще факт", натискання на яку
# працює так само, як команда /random

# Функція виклику команди /random
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'random'
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт')
    await send_image(update, context, 'random')
    # await send_text(update, context, response)
    await send_text_buttons(update, context, response, {
        'random_stop': 'Закінчити',
        'random_one_more': 'Хочу ще факт',
    })

# Обробка кнопок:
# /random и /stop
async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'random_stop':
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)
    await update.callback_query.answer()


# Телеграм-бот повинен обробляти команду /gpt.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT, передаючи йому
# текст отриманого повідомлення. Відповідь ChatGPT потрібно отримати та
# передати користувачеві текстовим повідомленням

# Функція виклику команди /gpt
async def gpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'gpt'
    text = load_message('gpt')
    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'gpt')
    await send_text(update, context, text)

# Функція обробки тексту GPT (gpt_interface)
async def gpt_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    user_message = update.message.text

    response = await chat_gpt.add_message(user_message)

    # await send_text(update, context, response)
    await send_text_buttons(update, context, response, {
        'gpt_stop': 'Закінчити',
    })

# Обробка кнопок:
# /gpt
async def gpt_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'gpt_stop':
        await start(update, context)
    await update.callback_query.answer()

# Телеграм-бот повинен обробляти команду /talk.
# При обробці команди бот надсилає заздалегідь підготовлене зображення та
# пропонує вибір з декількох відомих особистостей,
# використовуючи кнопки. При натисканні кнопки потрібно встановити промпт обраної особистості.
# Подальші текстові повідомлення від користувача потрібно передавати ChatGPT та
# повертати його відповіді користувачеві.
# До них має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start

dead_personality = {
        'talk_cobain': 'Курт Кобейн',
        'talk_hawking': 'Стівен Гокінг',
        'talk_nietzsche': 'Фрідріх Ніцше',
        'talk_tolkien': 'Джон Толкін',
        'talk_queen': 'Єлизавета II',
        'talk_stop': 'Закінчити',
    }

# Функція виклику команди /talk
async def talk_with_dead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None

    text = load_message('talk')

    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, text, dead_personality)


async def talk_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    user_message = update.message.text

    response = await chat_gpt.add_message(user_message)

    await send_text_buttons(update, context, response, {
        'talk_new': 'Змінити особистість', # !!!Кнопка не працює, ТГ ії не бачить!!!
        'talk_stop': 'Закінчити',
    })

# Обробка кнопок:
# /talk
async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data

    if query == 'talk_stop':
        context.user_data['mode'] = None
        await start(update, context)
        return

    if query == 'talk_new': # !!!Кнопка не працює!!!
        await talk_with_dead(update, context)
        return

    talk_prompt = None

    if query == 'talk_cobain':
        talk_prompt = 'talk_cobain'
    elif query == 'talk_hawking':
        talk_prompt = 'talk_hawking'
    elif query == 'talk_nietzsche':
        talk_prompt = 'talk_nietzsche'
    elif query == 'talk_tolkien':
        talk_prompt = 'talk_tolkien'
    elif query == 'talk_queen':
        talk_prompt = 'talk_queen'

    await update.callback_query.answer()

    if talk_prompt:
        context.user_data['mode'] = 'talk'

        prompt = load_prompt(talk_prompt)
        chat_gpt.set_prompt(prompt)

        await send_text(update, context, f'Зараз ви розмовляєте з {dead_personality[talk_prompt]}')



# Телеграм-бот повинен обробляти команду /quiz.
# При обробці команди бот надсилає заздалегідь підготовлене зображення
# та пропонує вибір з декількох тем, використовуючи кнопки.
# Після вибору теми, передати запит ChatGPT і, отримавши питання квізу, передати його
# користувачеві. Наступне текстове повідомлення користувача вважається відповіддю.
# Його потрібно передати ChatGPT та отримати результат. Результат передати користувачеві
# з можливістю задати ще питання на ту ж тему, змінити тему або закінчити квіз, за допомогою кнопок.
# Бот також повинен вести рахунок правильних відповідей та
# відображати разом з черговим результатом

# Функція виклику команди /quiz

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None

    text = load_message('quiz')

    await send_image(update, context, 'quiz')



chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt_command))
app.add_handler(CommandHandler('talk', talk_with_dead))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), gpt_handle_text))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), talk_handle_text))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_button_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_button_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
