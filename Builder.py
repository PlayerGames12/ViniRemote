import configparser

def get_and_write_credentials():
    """Запрашивает у пользователя Bot_token и password и записывает их в config.ini."""
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
    except FileNotFoundError:
        print("Файл config.ini не найден. Создается новый.")

    bot_token = input("Введите Bot_token: ")
    password = input("Введите password: ")


    if 'BOT' not in config:
        config['BOT'] = {}
    config['BOT']['Bot_token'] = bot_token

    if 'AUTH' not in config:
        config['AUTH'] = {}
    config['AUTH']['password'] = password

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    print("Данные успешно записаны в config.ini")

if __name__ == "__main__":
    get_and_write_credentials()