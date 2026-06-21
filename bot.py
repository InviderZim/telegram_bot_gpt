from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

import credentials

user_message = None #Глобальна змінна для отримання запиту від користувача

# Словники для конфігурації меню
dead_personality = {
        'talk_cobain': 'Курт Кобейн',
        'talk_hawking': 'Стівен Гокінг',
        'talk_nietzsche': 'Фрідріх Ніцше',
        'talk_tolkien': 'Джон Толкін',
        'talk_queen': 'Єлизавета II',
        'talk_stop': 'Закінчити',
    }

quiz_themes = {
        'quiz_prog': 'Програмування python',
        'quiz_math': 'Математичні теорії',
        'quiz_biology': 'Біологія',
        # 'quiz_more': 'Продовжуємо тему',
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'trainer': 'Словниковий тренажер 🧠',
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })


# Функція обробки выбору користувача
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_user = context.user_data.get('mode')

    if current_user is None:
        await send_text(update, context, "Щоб почати, виберіть щось з меню")
    elif current_user == 'random':
        await random(update, context)
    elif current_user == 'gpt':
        await gpt_handle_text(update, context)
    elif current_user == 'talk':
        await talk_handle_text(update, context)
    elif current_user == 'quiz':
        await quiz_handle_text(update, context)
    elif current_user == 'trainer':
        await trainer_handle_text(update, context)


# Телеграм-бот повинен обробляти команду /random.
# При обробці команди він надсилає заздалегідь підготовлене зображення
# та робить запит до ChatGPT із заздалегідь підготовленим промптом.
# Відповідь ChatGPT потрібно отримати та передати користувачеві.
# До повідомлення має бути прикріплена кнопка "Закінчити", натискання на яку
# працює так само, як команда /start.
# І кнопка "Хочу ще факт", натискання на яку
# працює так само, як команда /random

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'random'
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт')
    await send_image(update, context, 'random')
    # await send_text(update, context, response)
    await send_text_buttons(update, context, response, {
        'random_one_more': 'Хочу ще факт',
        'random_stop': 'Закінчити',
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

# Функція виклику команди /talk
async def talk_with_dead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None
    text = load_message('talk')
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, text, dead_personality)


async def talk_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = await chat_gpt.add_message(user_message)
    await send_text_buttons(update, context, response, {
        'talk_new': 'Змінити особистість',
        'talk_stop': 'Закінчити',
    })

# Обробка кнопок:
# /talk

async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'talk_stop':
        await start(update, context)
        return

    if query == 'talk_new':
        await talk_with_dead(update, context)
        return

    if query in dead_personality:
        context.user_data['mode'] = 'talk'
        prompt = load_prompt(query)
        chat_gpt.set_prompt(prompt)
        await send_text(update, context, f'Зараз ви розмовляєте з {dead_personality[query]}')


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

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None
    if 'quiz_total_score' not in context.user_data:
        context.user_data['quiz_total_score'] = 0
    context.user_data['quiz_topic_score'] = 0

    text = load_message('quiz')
    await send_image(update, context, 'quiz')

    start_menu = {
        'quiz_prog': quiz_themes['quiz_prog'],
        'quiz_math': quiz_themes['quiz_math'],
        'quiz_biology': quiz_themes['quiz_biology']
    }

    await send_text_buttons(update, context, text, start_menu)

async def quiz_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    user_message = update.message.text
    response = await chat_gpt.add_message(user_message)
    lower_response = response.lower()

    is_correct = ("правильно" in lower_response or "correct" in lower_response)
    is_incorrect = ("неправильно" in lower_response or "incorrect" in lower_response)

    if is_correct and not is_incorrect:
        context.user_data['quiz_total_score'] = context.user_data.get('quiz_total_score', 0) + 1
        context.user_data['quiz_topic_score'] = context.user_data.get('quiz_topic_score', 0) + 1

    topic_score = context.user_data.get('quiz_topic_score', 0)
    total_score = context.user_data.get('quiz_total_score', 0)
    score_message = f"\n\n Рахунок теми: {topic_score} | Загальний рахунок: {total_score}"

    quiz_action_menu = {
        'quiz_more': 'Продовжуємо тему',
        'quiz_change': 'Змінити тему',
        'quiz_stop': 'Закінчити',
    }
    await send_text_buttons(update, context, response + score_message, quiz_action_menu)

# Обробка кнопок:
# /quiz

async def quiz_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'quiz_stop':
        final_score = context.user_data.get('quiz_total_score', 0)

        context.user_data['mode'] = None
        if 'quiz_total_score' in context.user_data:
            del context.user_data['quiz_total_score']

        await send_text(update, context,
                        f"Гру закінчено! Ваш загальний рахунок за всі теми: {final_score} балів. Дякуємо за гру!")

        await start(update, context)
        return

    elif query == 'quiz_change':
        await quiz_command(update, context)
        return

    if query == 'quiz_more':
        gpt_request = "quiz_more"
    else:
        theme_name = quiz_themes.get(query)
        context.user_data['quiz_theme'] = theme_name
        gpt_request = query

    context.user_data['mode'] = 'quiz'

    if query != 'quiz_more':
        prompt = load_prompt('quiz')
        chat_gpt.set_prompt(prompt)

    question = await chat_gpt.add_message(gpt_request)

    await send_text(update, context, question)

# Словниковий тренажер
#
# Бот допомагає користувачеві розширювати словниковий запас іноземної мови.
# Може надсилати нове слово з перекладом та прикладами використання.
# При надсиланні слово вважається вивченим. До повідомлення мають бути прикріплені
# кнопки "Ще слово", "Тренуватися", та "Закінчити".
# При натисканні на "Тренуватися" бот повинен проводити тест по вивчених словах
# з валідацією з боку ChatGPT.
#
# Тест повинен представляти собою перебір усіх вивчених слів. Кожне таке слово
# має бути виведене в повідомленні. Наступне повідомлення користувача вважається
# перекладом цього слова. Для валідації правильності можна використовувати ChatGPT.
# В кінці тесту потрібно виводити результат у вигляді кількості правильних відповідей.

# Функція виклику команди /trainer

async def trainer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None

    if 'learned_words' not in context.user_data:
        context.user_data['learned_words'] = []

    text = load_message('trainer')

    await send_image(update, context, 'trainer')
    await send_text_buttons(update, context, text, {
        'trainer_word': 'Ще слово',
        'trainer_test': 'Тренуватися',
        'trainer_stop': 'Закінчити',
    })

async def trainer_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_message
    user_message = update.message.text
    response = await chat_gpt.add_message(user_message)

async def trainer_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()



chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt_command))
app.add_handler(CommandHandler('talk', talk_with_dead))
app.add_handler(CommandHandler('quiz', quiz_command))
app.add_handler(CommandHandler('trainer', trainer_command))

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_button_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_button_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_button_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(trainer_button_handler, pattern='^trainer_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
