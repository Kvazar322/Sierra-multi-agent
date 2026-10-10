from google import genai
import telebot
import json
import os
import sys
from openrouter import OpenRouter
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
from google.genai import types


current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
file_path = os.path.join(current_dir, "config.json")

with open(file_path, "r", encoding="utf-8") as f:
    config = json.load(f)

api_gemini = config["api_gemini"]
tg_api = config["tg_api"]
id_chat = config["id_chat"]
openrouter = config["openrouter"]

bot = telebot.TeleBot(tg_api)
openrouter_client = OpenRouter(api_key=openrouter)
client_gemini = genai.Client(api_key=api_gemini)

sample = ("""
    ######   ######   #####   #####    #####      ###
    ##         ##     ##      ##  ##   ##  ##    ## ##
    ######     ##     #####   #####    #####    ##   ##
        ##     ##     ##      ## ##    ## ##    #######
    ######   ######   #####   ##  ##   ##  ##   ##   ##
    """)

class btn_settings:
    def __init__(self, state, label):
        self.state = state
        self.label = label

    def btn_switch(self):
        self.state = not self.state
            
        if self.state:
            print(f"{self.label} ON")
            return f"{self.label} ON"
        else:
            print(f"{self.label} OFF")
            return f"{self.label} OFF"

iterations_switch = btn_settings(False, "Итерации")
limit_tokens_switch = btn_settings(True, "Ограничение токенов")
long_request_switch = btn_settings(False, "Длинный ответ")
swap_fallbacks = btn_settings(True, "Смена в Fallbacks")

def get_params():
# Модуль ограничения токенов
        if limit_tokens_switch.state == True:
            lim_tok = 6000
        else:
            lim_tok = None

# Модуль включения длинного ответа
        if long_request_switch.state == False:
            prompt = "Кратко ответь на мой вопрос."
        else:
            prompt = "Выписуй/пиши с решением задачи."

        return lim_tok, prompt

async def error_handler(error_code, iterations_while, model):
    error_msg = str(error_code)
    is_server_error = any(code in error_msg for code in ("500", "503"))

    fallback_rules = {
        "gemma-4-31b-it": "gemini-3-flash-preview",
        "gemini-3.6-flash": "gemini-3-flash-preview",
        "deepseek/deepseek-v4-flash": "nvidia/nemotron-3-super-120b-a12b:free",
        "tencent/hy3": "nvidia/nemotron-3-super-120b-a12b:free"
    }

    if is_server_error and iterations_while != 3:
        print(f"Повторная попытка для {model}...")
        bot.send_message(chat_id=id_chat, text=f"Повторная попытка для {model}...")

        await asyncio.sleep(10)

        return True, model, iterations_while

    elif is_server_error and swap_fallbacks.state == True:

        if model in fallback_rules:
            next_model = fallback_rules[model]

            print("Попытка смены модели...")
            bot.send_message(chat_id=id_chat, text="Попытка смены модели...")

            return True, next_model, 1

        else:
            print(f"Неопознаная ошибка или не удалось её решить сменой модели. Нулевая модель - {model}: {error_code}")
            bot.send_message(chat_id=id_chat, text=f"Неопознаная ошибка или не удалось её решить сменой модели. Нулевая модель - {model}: {error_code}")
            
            return False, model, iterations_while
            
    print(f"Неопознаная ошибка или не удалось её решить для {model}: {error_code}")
    bot.send_message(chat_id=id_chat, text=f"Неопознаная ошибка или не удалось её решить для {model}: {error_code}")
    
    return False, model, iterations_while

# Ответ deepseek
async def deepseek_work(input_text_deepseek):
    iterations_while = True
    iterations = 0
    model = "deepseek/deepseek-v4-flash"    #deepseek/deepseek-r1
    
    while iterations_while:
        try:
            lim_tok, prompt = get_params()

            response = await openrouter_client.chat.send_async(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text_deepseek},
                ],
                max_tokens=lim_tok
            )

            clean_content = response.choices[0].message.content
            print(f"\n Ответ {model}: {clean_content}")

            return clean_content
            
        except Exception as e:
            iterations_while, model, iterations = await error_handler(e, iterations, model)
            iterations += 1

    return None
    
# Ответ hy3
async def gpt_work (input_text_gpt):
    iterations_while = True
    iterations = 0
    model = "tencent/hy3"    #tencent/hy3    /   qwen/qwen3.8-max-0902  /   qwen/qwen3.8-27b:free
    
    while iterations_while:
        try:
            lim_tok, prompt = get_params()

            response = await openrouter_client.chat.send_async(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text_gpt}
                ],
                max_tokens=lim_tok
            )
        
            clean_content =  response.choices[0].message.content
            print(f"\n Ответ {model}: {clean_content}")

            return clean_content
            
        except Exception as e:
            iterations_while = await error_handler(e, iterations, model)
            iterations += 1

    return None
    
# Ответ gemini
async def gemini_work (input_text_gemini):
    iterations_while = True
    iterations = 0
    model = "gemini-3.6-flash"
    
    while iterations_while:
        try:
            lim_tok, prompt = get_params()

            response = await client_gemini.aio.models.generate_content(
                model=model,
                contents=input_text_gemini,
                config={
                "system_instruction": prompt
                }
                )
            
            clean_content = response.text
            print(f"\n Ответ {model}: {clean_content}")

            return clean_content
        
        except Exception as e:
            iterations_while, model, iterations = await error_handler(e, iterations, model)
            iterations += 1

    return None

#Ответ Gemma
async def gemma_work (input_text_gemma):
    iterations_while = True
    iterations = 0
    model = "gemma-4-31b-it"

    while iterations_while:
        try:
            lim_tok, prompt = get_params()

            response = await client_gemini.aio.models.generate_content(
                model=model,
                contents=input_text_gemma,
                config={
                "system_instruction": prompt
                }
                )
            
            clean_content = response.text
            print(f"\n Ответ {model}: {clean_content}")

            return clean_content

        except Exception as e:
            iterations_while, model, iterations = await error_handler(e, iterations, model)
            iterations += 1

    return None    

#Ответ gemini(oсr)
async def osr_work (input_text_ocr):
    iterations_while = True
    iterations = 0
    model = "gemini-3.5-flash-lite"

    while iterations_while:
        try:
            response = await client_gemini.aio.models.generate_content(
                model=model,
                contents=[
                    "Что изображено на фотографии?",
                    types.Part.from_bytes(
                        data=input_text_ocr,
                        mime_type="image/jpeg"
                    )
                ],
                config={
                "system_instruction": "Тебе дано фото. Твоя задача достать текст из фото для последующей текстовой модели."
                }
            )
            
            clean_content = response.text
            print(f"\n Ответ {model}: {clean_content}")

            return clean_content
        
        except Exception as e:
            iterations_while, model, iterations = await error_handler(e, iterations, model)
            iterations += 1

    return None  


#Модуль 1
async def model_2(request_user, response_gemini_1):
    prompt = f"Изначальный вопрос: {request_user}. Ответ gemini: {response_gemini_1}"
    return await gpt_work(prompt)

async def model_3(request_user, response_gemini_1, response_gpt_1):
    prompt = f"Изначальный вопрос: {request_user}. Ответ gemini: {response_gemini_1}. Ответ gpt на gemini: {response_gpt_1}"
    return await deepseek_work(prompt)

async def module_1(request_user):
    msg = bot.send_message(chat_id=id_chat, text=f"Модуль-1: 0%...")

    res_gemini = await gemini_work(request_user)
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-1: 25%...")

    res_gpt = await model_2(request_user, res_gemini)
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-1: 50%...")

    res_deepseek = await model_3(request_user, res_gemini, res_gpt)
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-1: 75%...")
    
    prompt = (
        f"Твоя задача обобщить эти ответы не меняя их сути, если есть расхождения в ответах — прямо укажи на них и добавь на против ответа количество голосов за вариант."
        f"Если голос None то не учитывай его.\n"
        f"Подсчитывай количество голосов за каждый из отдельных ответов, если они расходятся.\n"
        f"Ответ gemini: {res_gemini}\n"
        f"Ответ gpt: {res_gpt}\n"
        f"Ответ deepseek: {res_deepseek}"
    )
    gemma_ret = await gemma_work(prompt)
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-1: 100%...")

    return gemma_ret

#Модуль 2
async def module_2(request_user):
    msg = bot.send_message(chat_id=id_chat, text=f"Модуль-2: 0%...")

    res_gemini, res_deepseek, res_gpt = await asyncio.gather(
        gemini_work(request_user),
        deepseek_work(request_user),
        gpt_work(request_user)
    )
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-2: 75%...")
    
    prompt = (
        f"Твоя задача обобщить эти ответы не меняя их сути, если есть расхождения в ответах — прямо укажи на них и добавь на против ответа количество голосов за вариант."
        f"Если голос None то не учитывай его.\n"
        f"Подсчитывай количество голосов за каждый из отдельных ответов, если они расходятся.\n"
        f"Ответ gemini: {res_gemini}\n"
        f"Ответ deepseek: {res_deepseek}\n"
        f"Ответ gpt: {res_gpt}"
    )
    gemma_ret = await gemma_work(prompt)
    bot.edit_message_text(chat_id=id_chat, message_id=msg.message_id, text=f"Модуль-2: 100%...")
    return gemma_ret

#Модуль 3
async def module_3(request_user):
    iterations_while = 0
    history_outputs = []
    while iterations_while < 3:
        if iterations_switch.state == False:
            iterations_while += 3
        response_gemma_1, response_gemma_2 = await asyncio.gather(
            module_1(request_user),
            module_2(request_user)
        )

        prompt = (
            f"Твоя задача подытожить эти ответы."
            f"Если есть расхождения в них, вынеси их отдельно и суммируй голоса обоих вариантов."
            f"Подсчитывай количество голосов за каждый из отдельных ответов, если они расходятся.\n"
            f"Примерный трафорет ответа(то что в скобках не учитывай, это для тебя):"
            f"\nИтоговый ответ(если есть расхождения в ответе, то ответ не вносится в этот блок):..."
            f"-кол-во голосов:...(количество голосов за предоставленный ответ)"
            f"\nРасхождения в ответах:..."
            f"-кол-во голосов:...(количество голосов за предоставленный ответ)"
            f"Ответ 1: {response_gemma_1}\n"
            f"Ответ 2: {response_gemma_2}"
        )

        final_output = await gemma_work(prompt)
        bot.send_message(chat_id=id_chat, text=f"Модуль-3...")

        if iterations_switch.state == False:
            history_outputs.append(f"*Без итераций.**\n{final_output}")
        else:
            history_outputs.append(f"*Итерация №{iterations_while}**\n{final_output}")

#Модуль 4
        if iterations_switch.state == True:
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

    btn1 = InlineKeyboardButton(text='🥵Итерации ON/OFF', callback_data='button_1')
    btn2 = InlineKeyboardButton(text='🔥Ограничение токенов ON/OFF', callback_data='button_2')
    btn3 = InlineKeyboardButton(text='‼️Информация', callback_data='button_3')
    btn4 = InlineKeyboardButton(text='📖Подробный/Краткий ответ', callback_data='button_4')
    btn5 = InlineKeyboardButton(text='Сhecks servers', callback_data='button_5')
    btn6 = InlineKeyboardButton(text='Смена в Fallbacks', callback_data='button_6')

    markup.add(btn1, btn2)
    markup.add(btn4)
    markup.add(btn5, btn6)
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
        bot.send_message(call.message.chat.id, iterations_switch.btn_switch())

    elif call.data == 'button_2':
        bot.send_message(call.message.chat.id, limit_tokens_switch.btn_switch())

    elif call.data == 'button_3':
        bot.send_message(call.message.chat.id, info())

    elif call.data == 'button_4':
        bot.send_message(call.message.chat.id, long_request_switch.btn_switch())

    elif call.data == 'button_5':
        asyncio.run(ping_servers())

    elif call.data == 'button_6':
        bot.send_message(call.message.chat.id, swap_fallbacks.btn_switch())

#функции кнопок:
def info():
    text = (
        f"\n🥵Итерации - {iterations_switch.state}"
        f"\n🔥Ограничение токенов - {limit_tokens_switch.state}"
        f"\n📖Длинный ответ - {long_request_switch.state} - Функция в beta версии!"
        f"\nСпав в Fallbacks - {swap_fallbacks.state} - Функция в beta версии!"
        "\n-------------------"
        "\n--🥵Итерации это режим при котором Сиера делает 3 круга. Увеличивает охват на n%"
        "\n⚠️ Увеличивает кол-во используемых токенов в ⁓3 раза."
        "\n⚠️ Кратно увеличивает время ответа."
        "\n⚠️ НЕ рекомендуется включать на тестовых заданиях т.к это МОЖЕТ привести к повышению вероятности ошибок в финальных ответах."
        "\n-------------------"
        "\n--🔥Ограничение токенов это режим при котором лимит токенов отключается (по умолчанию 6к токенов)."
        "\n⚠️ Расход токенов может стать безумным. Включать на свой страх и риск!"
        "\n-------------------"
        "\n--📖Подробный/Краткий(beta) ответ это режим при котором модель начинает давать более развернутые ответы."
        "\n⚠️ Функция работет не стабильно!"
        "\n-------------------"
        "\n--Смена в Fallbacks(beta) - включает возможность пайплайну переключиться на рабочую модель автоматически если модель не доступна."
        "\n-------------------"
        "\n--👀 OСR(beta) даёт возможность распознавать текст с фото."
        "\n⚠️ При использовании фото писать ничего нельзя вместе с фото!"
        "\n-------------------"
        "\n--❇️Sierra (0.9.0 pre) это узкоспециализированный, продвинутый, безошибочный  мульти-агент."
        )
    
    return text

async def ping_servers():
    urls = ["https://web.telegram.org","https://openrouter.ai","https://aistudio.google.com"]

    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                req = await client.get(url, timeout=5)

                if req.status_code == 200 or req.status_code == 302:
                    print(f"{url} - Статус: {req.status_code} - OK 🟢")
                    bot.send_message(chat_id=id_chat, disable_web_page_preview=True, text=f"{url} - Статус: {req.status_code} - OK 🟢")
                
                else:
                    print(f"{url} - Статус: {req.status_code} - Ошибка 🔴")
                    bot.send_message(chat_id=id_chat, disable_web_page_preview=True, text=f"{url} - Статус: {req.status_code} - Ошибка 🔴")

            except Exception as e:
                print(f"Ошибка выполнения: {e}")
                bot.send_message(chat_id=id_chat, text=f"Ошибка выполнения: {e}")

#Принятие сообщений(текст)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id

    request_user = message.text
    print(request_user)
    
    bot.send_message(chat_id=chat_id, text="Запрос принят в обработку...")
    
    try:
        final_answer = asyncio.run(module_3(request_user))
        bot.send_message(chat_id=chat_id, text=final_answer)

    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")

#Принятие сообщений(фото)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        file_bytes = bot.download_file(file_info.file_path)

        bot.send_message(chat_id=chat_id, text="Запрос(фото) принят в обработку...")

    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")


    try:
        out_text = asyncio.run(osr_work(file_bytes))
        print(f"Текст с фото: {out_text}")

        final_answer = asyncio.run(module_3(out_text))
        bot.send_message(chat_id=chat_id, text=final_answer)

    except Exception as e:
        print(f"Ошибка выполнения: {e}")
        bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")


print(f"""\033[36m{sample}\033[0m""")
bot.send_message(chat_id=id_chat, text=f"""```{sample}```""", parse_mode='MarkdownV2')
bot.infinity_polling()