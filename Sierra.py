from google import genai
import telebot
import json
import os
import sys
from openrouter import OpenRouter
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
file_path = os.path.join(current_dir, "config.json")

with open(file_path, "r", encoding="utf-8") as f:
    config = json.load(f)

api_gemini = config["api_gemini"]
tg_api = config["tg_api"]
id_chat = config["id_chat"]
openrouter = config["openrouter"]

limit_tokens_swith = True
iterations_switch = False
long_request = False

bot = telebot.TeleBot(tg_api)
openrouter_client = OpenRouter(api_key=openrouter)


# Ответ дикпик
async def deepseek_work(input_text_deepseek):
    try:
# Модуль ограничения токенов
        if limit_tokens_swith == True:
            lim_tok = 6000
        else:
            lim_tok = None

# Модуль включения длинного ответа
        if long_request == False:
            prompt = "Кратно ответь на мой вопрос."
        else:
            prompt = "Развернуто ответь на мои вопросы."

        response = await openrouter_client.chat.send_async(
            model="deepseek/deepseek-v4-flash",#deepseek/deepseek-r1
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text_deepseek},
            ],
            max_tokens=lim_tok
        )
        clean_content = response.choices[0].message.content
        print(f"\n Ответ DeepSeek: {clean_content}")
        return clean_content
        
    except Exception as e:
            print(f"Ошибка выполнения deepseek-v4-flash: {e}")
            bot.send_message (chat_id=id_chat, text=f"Ошибка выполнения deepseek-v4-flash: {e}")
            return None
# Ответ hy3
async def gpt_work (input_text_gpt):
    try:
# Модуль ограничения токенов
        if limit_tokens_swith == True:
            lim_tok = 6000
        else:
            lim_tok = None

# Модуль включения длинного ответа
        if long_request == False:
            prompt = "Кратно ответь на мой вопрос."
        else:
            prompt = "Развернуто ответь на мои вопросы."

        response = await openrouter_client.chat.send_async(
            model="tencent/hy3",#openai/gpt-4o-mini-2024-07-18
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text_gpt}
            ],
            max_tokens=lim_tok
        )
    
        clean_content =  response.choices[0].message.content
        print(f"\n Ответ gpt: {clean_content}")
        #bot.send_message(chat_id=id_chat, text=f"Ответ GPT: {clean_content}")
        return clean_content
        
    except Exception as e:
                print(f"Ошибка выполнения hy3: {e}")
                bot.send_message (chat_id=id_chat, text=f"Ошибка выполнения hy3: {e}")
                return None
    
# Ответ гемени
client_gemini = genai.Client(api_key=api_gemini)

async def gemini_work (input_text_gemini):
    try:
# Модуль включения длинного ответа
        if long_request == False:
            prompt = "Кратно ответь на мой вопрос."
        else:
            prompt = "Развернуто ответь на мои вопросы."

        response = await client_gemini.aio.models.generate_content(
            model="gemini-3.6-flash",
            contents=input_text_gemini,
            config={
            "system_instruction": prompt
            }
            )
        
        clean_content = response.text
        print(f"\n Ответ gemini: {clean_content}")
        #bot.send_message(chat_id=id_chat, text=f"Ответ Gemini: {clean_content}")
        return clean_content
    
    except Exception as e:
                print(f"Ошибка выполнения gemini-3.6-flash: {e}")
                bot.send_message(chat_id=id_chat, text=f"Ошибка выполнения gemini-3.6-flash: {e}")

#Ответ Gemma
async def gemma_work (input_text_gemma):
    try:
# Модуль включения длинного ответа
        if long_request == False:
            prompt = "Кратно ответь на мой вопрос."
        else:
            prompt = "Давай развернутый, полный ответ модели."

        response = await client_gemini.aio.models.generate_content(
            model="gemma-4-31b-it",
            contents=input_text_gemma,
            config={
            "system_instruction": prompt
            }
            )
        
        clean_content = response.text
        print(f"\n Ответ gemma: {clean_content}")
        #bot.send_message(chat_id=id_chat, text=f"Ответ Gemma: {clean_content}")
        return clean_content
    
    except Exception as e:
            print(f"Ошибка выполнения gemma-4-31b-it: {e}")
            bot.send_message(chat_id=id_chat, text=f"Ошибка выполнения gemma-4-31b-it: {e}")


#Модуль 1
async def model_2(request_user, response_gemini_1):
    prompt = f"Изначальный вопрос: {request_user}. Ответ gemini: {response_gemini_1}"
    return await gpt_work(prompt)

async def model_3(request_user, response_gemini_1, response_gpt_1):
    prompt = f"Изначальный вопрос: {request_user}. Ответ gemini: {response_gemini_1}. Ответ gpt на gemini: {response_gpt_1}"
    return await deepseek_work(prompt)

async def module_1(request_user):
    res_gemini = await gemini_work(request_user)
    bot.send_message(chat_id=id_chat, text=f"Модуль-1: 25%...")

    res_gpt = await model_2(request_user, res_gemini)
    bot.send_message(chat_id=id_chat, text=f"Модуль-1: 50%...")

    res_deepseek = await model_3(request_user, res_gemini, res_gpt)
    bot.send_message(chat_id=id_chat, text=f"Модуль-1: 75%...")
    
    prompt = (
        f"Твоя задача обобщить эти ответы не меняя их сути, если есть расхождения в ответах — прямо укажи на них и добавь на против ответа количество голосов за вариант. Если голос None то не учитывай его.\n"
        f"Ответ gemini: {res_gemini}\n"
        f"Ответ gpt: {res_gpt}\n"
        f"Ответ deepseek: {res_deepseek}"
    )
    gemma_ret = await gemma_work(prompt)
    bot.send_message(chat_id=id_chat, text=f"Модуль-1: 100%...")
    return gemma_ret

#Модуль 2
async def module_2(request_user):
    res_gemini, res_deepseek, res_gpt = await asyncio.gather(
        gemini_work(request_user),
        deepseek_work(request_user),
        gpt_work(request_user)
    )
    bot.send_message(chat_id=id_chat, text=f"Модуль-2: 75%...")

    prompt = (
        f"Твоя задача обобщить эти ответы не меняя их сути, если есть расхождения в ответах — прямо укажи на них и добавь на против ответа количество голосов за вариант. Если голос None то не учитывай его.\n"
        f"Подсчитывай количество голосов за каждый из отдельных ответов, если они расходятся.\n"
        f"Ответ gemini: {res_gemini}\n"
        f"Ответ deepseek: {res_deepseek}\n"
        f"Ответ gpt: {res_gpt}"
    )
    gemma_ret = await gemma_work(prompt)
    bot.send_message(chat_id=id_chat, text=f"Модуль-2: 100%...")
    return gemma_ret

#Модуль 3
async def module_3(request_user):
    iterations_while = 0
    history_outputs = []
    while iterations_while < 3:
        if iterations_switch == False:
            iterations_while += 3
        response_gemma_1, response_gemma_2 = await asyncio.gather(
            module_1(request_user),
            module_2(request_user)
        )

        prompt = (
            f"Твоя задача подытожить эти ответы. Если есть расхождения в них, вынеси их отдельно. И суммируй голоса обоих вариантов."
            f"Подсчитывай количество голосов за каждый из отдельных ответов, если они расходятся.\n"
            f"Ответ 1: {response_gemma_1}\n"
            f"Ответ 2: {response_gemma_2}"
        )

        final_output = await gemma_work(prompt)
        bot.send_message(chat_id=id_chat, text=f"Модуль-3...")

        history_outputs.append(f"*Итерация №{iterations_while}**\n{final_output}")
#Модуль 4
        if iterations_switch == True:
            prompt_2 = (
                f"Твоя задача из начальных вопросов достать только те(в полном их содержании), что есть в блоке расхождения в ответах."
                f"Вопросы: {request_user}\n"
                f"Ответы: {final_output}"
            )

            request_user = await gemma_work(prompt_2)
            bot.send_message(chat_id=id_chat, text=f"0%... Новый круг...")

        iterations_while += 1
    return "-------------------\n".join(history_outputs)


#два блока ответсвенные за кнопочки
@bot.message_handler(commands=['menu'])
def btn_pull(message):
    markup = InlineKeyboardMarkup()

    btn1 = InlineKeyboardButton(text=f'🥵Итерации ON/OFF', callback_data='button_1')
    btn2 = InlineKeyboardButton(text=f'🔥Ограничение токенов ON/OFF', callback_data='button_2')
    btn3 = InlineKeyboardButton(text='‼️Информация', callback_data='button_3')
    btn4 = InlineKeyboardButton(text='📖Подробный/Краткий ответ', callback_data='button_4')

    markup.add(btn1, btn2)
    markup.add(btn4)
    markup.add(btn3)

    bot.send_message(
        message.chat.id, 
        'Дополнительные функции Sierra:', 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.answer_callback_query(call.id)
    
    if call.data == 'button_1':
        bot.send_message(call.message.chat.id, iterations())
    elif call.data == 'button_2':
        bot.send_message(call.message.chat.id, token_switch())
    elif call.data == 'button_3':
            bot.send_message(call.message.chat.id, info())
    elif call.data == 'button_4':
                bot.send_message(call.message.chat.id, length_answer())      

#функции кнопок:
def iterations():
    global iterations_switch
    iterations_switch = not iterations_switch
    
    if iterations_switch:
        print("Итерации ON")
        return "Итерации ON"
    else:
        print("Итерации OFF")
        return "Итерации OFF"

def token_switch():
    global limit_tokens_swith
    limit_tokens_swith = not limit_tokens_swith
    
    if limit_tokens_swith:
        print("Ограничение токенов ON")
        return "Ограничение токенов ON"
    else:
        print("Ограничение токенов OFF")
        return "Ограничение токенов OFF"

def length_answer():
    global long_request
    long_request = not long_request
    
    if long_request:
        print("Длинный ответ ON")
        return "Длинный ответ ON"
    else:
        print("Длинный ответ OFF")
        return "Длинный ответ OFF"

def info():
    text = (
        f"\n🥵Итерации - {iterations_switch}"
        f"\n🔥Ограничение токенов - {limit_tokens_swith}"
        f"\n📖Длинный ответ - {long_request} - Функция в beta версии!"
        "\n-------------------"
        "\n--🥵Итерации это режим при котором Сиера делает 3 круга. Увеличивает охват на n%"
        "\n⚠️ Увеличивает кол-во используемых токенов в ⁓3 раза."
        "\n⚠️ Кратно увеличивает время ответа."
        "\n⚠️ НЕ рекомендуется включать на тестовых заданиях т.к это МОЖЕТ привести к повышению вероятности ошибок в финальных ответах."
        "\n-------------------"
        "\n--🔥Ограничение токенов это режим при котором лимит токенов отключается (по умолчанию 6к токенов)."
        "\n⚠️ Расход токенов может стать безумным. Включать на свой страх и риск!"
        "\n-------------------"
        "\n--📖Подробный/Краткий ответ это режим при котором модель начинает давать более развернутые ответы."
        "\n⚠️ Функция ни разу не тестировалась. Результат не предсказуем!"
        "\n-------------------"
        "\n--❇️Sierra (0.6.2) это узкоспециализированный, продвинутый, безошибочный агент."
        )
    return text

#Принятие сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    request_user = message.text
    chat_id = message.chat.id
    
    bot.send_message(chat_id=chat_id, text="Запрос принят в обработку...")
    
    try:
        final_answer = asyncio.run(module_3(request_user))
        bot.send_message(chat_id=chat_id, text=final_answer)

    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")


print("Sierra (0.6.2) запущена.")
bot.send_message(chat_id=id_chat, text="Sierra (0.6.2) запущена.")
bot.infinity_polling()