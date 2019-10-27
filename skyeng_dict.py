#!/usr/bin/env python3
import requests
import re
import json
import pickle
import os
from playsound import playsound

from random import choice

filename = "settings"


def load_settings(file):
    try:
        with open(file, "rb") as file:
            return pickle.load(file)
    except Exception:
        print("Failed load settings...")
        return {}


def save_settings(file, settings):
    with open(file, "wb") as file:
        pickle.dump(settings, file)


def skyeng_login(uname, password, client_id="13_1r4a5jsqugasksk8sg08g8wcw4gwokg4k4408sww0c444s48c4", verify=True):
    # Get login page
    response = requests.get(
        'https://id.skyeng.ru/ru/frame/login', verify=verify
    )

    # Get csrf token and session cookie
    csrf = re.findall(r"name=\"csrfToken\" value=\"([^\"]+)\"", response.content.decode())[0]
    sess_reg = re.compile(r"session_global=([\w]+);")
    session_global = sess_reg.findall(response.headers["Set-Cookie"])[0]

    # Send user data and get authorized session
    response = requests.post(
        'https://id.skyeng.ru/ru/frame/login-submit', cookies={"session_global": session_global},
        data={"csrfToken": csrf, "username": uname, "password": password},
        verify=verify)
    # Getting authorization token
    cookies = {"session_global": sess_reg.findall(response.headers["Set-Cookie"])[0]}
    response = requests.get(
        f'https://id.skyeng.ru/oauth2-server/auth?client_id={client_id}&'
        f'redirect_uri=https%3A%2F%2Fext.skyeng.tv%2Fauth%2FsaveToken&'
        f'response_type=code&'
        f'skin=skyeng',
        cookies=cookies,
        verify=verify)
    data = re.findall(r"fos_oauth_server_authorize_form\[(\w+)\]\" value=\"([^\"]+)", response.content.decode())
    data = {f"fos_oauth_server_authorize_form[{name}]": data for name, data in data}
    data["accepted"] = ""
    response = requests.post('https://id.skyeng.ru/oauth2-server/auth',
                             data=data,
                             cookies=cookies,
                             verify=verify, allow_redirects=False)
    response = requests.get(response.headers["Location"],
                            cookies=cookies,
                            verify=verify, allow_redirects=False)

    token = re.findall(r"access_token=([^;]+)&", response.content.decode())[0]
    # refresh = re.findall(r"refresh_token=([^;]+)&", response.content.decode())[0]
    return cookies, token


def get_dict_from_site(session, verify=True):
    authorization = {"Authorization": f"Bearer {session[1]}"}
    response = requests.get('https://api.words.skyeng.ru/api/provider/wordsets.json?withWords=1&',
                            cookies=session[0],
                            headers=authorization,
                            verify=verify)
    word_sets_data = json.loads(response.content.decode())
    if isinstance(word_sets_data, dict):
        return None
    words_sets = {}
    total_words = []
    for set_info in word_sets_data:
        if set_info["wordsNum"] > 2:
            words_id = [word["meaningId"] for word in set_info['words']]
            words_sets[set_info["title"]] = words_id
            total_words += words_id
    response = requests.get(f'https://dictionary.skyeng.ru/api/for-services/v1/meanings'
                            f'?ids={",".join(str(i) for i in total_words)}',
                            cookies=session[0],
                            headers=authorization,
                            verify=verify)
    words_data = json.loads(response.content.decode())
    counter = 0
    for _, word_set in words_sets.items():
        for i in range(len(word_set)):
            wdata = words_data[counter]
            word_set[i] = {"word": wdata["text"],
                           "translation": wdata["translation"]["text"],
                           "transcription": wdata["transcription"],
                           "sound": wdata["soundUrl"],
                           "difficulty": 0 if wdata["difficultyLevel"] is None else wdata["difficultyLevel"]}
            counter += 1
    return words_sets


def download_file(url):
    url = "http://" + url
    name = url.split("/")[-1]
    if not os.path.exists("temp_voice/"+name):
        response = requests.get(url)
        if not os.path.isdir("temp_voice"):
            os.mkdir("temp_voice")
        with open("temp_voice/"+name, "wb") as file:
            file.write(response.content)
        if settings.get("filetemplist") is None:
            settings["filetemplist"] = []
        if len(settings) >= 100:
            os.remove("temp_voice/"+settings.pop(0))
        settings["filetemplist"].append(name)
    return "temp_voice/" + name


def login(settings=None):
    print("Login to your SkyEng account.")
    while True:
        uname = input("\tLogin: ")
        pwd = input("\tPassword: ")
        sess = skyeng_login(uname, pwd)
        if sess is not None:
            print("Correct.")
            break
        print("Incorrect login or password. Retrying...")
    if settings is not None:
        settings["uname"] = uname
        settings["pwd"] = pwd
        settings["session"] = sess
    else:
        return sess, uname, pwd


def getchar():
    # Returns a single character from standard input
    import os
    if os.name == 'nt':  # how it works on windows
        import msvcrt
        ch = msvcrt.getch()
    else:
        import tty
        import termios
        import sys
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if ord(ch) == 3: quit()  # handle ctrl+C
    return ch


def get_number(message, a=0, b=10):
    while True:
        try:
            d = int(input(message))
            if a <= d <= b:
                return d
            print("Incorrect value.")
        except ValueError:
            print("Must be integer.")


def wordlist():
    os.system('cls')
    print("Word List:")
    for set_name, words in w_sets.items():
        print(f"Set - '{set_name}'")
        for word in words:
            print(f"\t{word['word']} [{word['transcription']}] - {word['translation']}")
    print("0) Back")
    x = get_number("Choise: ", 0, 0)


def train():
    os.system('cls')
    print("Training...")
    print("Select set for training:")
    for i, set_name in enumerate(w_sets):
        print(f"{i + 1}) {set_name}")
    print("0) Back")
    x = get_number("Choose: ", 0, len(w_sets))
    if x == 0:
        return
    train_set = list(w_sets.values())[x - 1]
    print("Keys:\n"
          " a - open one character;\n"
          " f - open full world;\n"
          " v - play voice;\n"
          " n - next word.")
    while len(train_set) != 0:
        w = choice(train_set)
        train_set.remove(w)
        x = 0
        while True:
            print(f"\r{w['word']} [{w['transcription']}] - {w['translation'][0:x]}{'*' * (len(w['translation']) - x)}",
                  end="")
            c = getchar().decode()
            if c == "a":
                x += 1
            elif c == "f":
                x = len(w['translation'])
            elif c == "v":
                playsound(download_file(w['sound'][2:]))
            elif c == "n":
                print()
                break


def main_menu():
    while True:
        os.system('cls')
        print("Main menu\n"
              " 1) Word list\n"
              " 2) Train\n"
              " 3) Quit\n"
              " 4) Logout and quit")
        x = get_number("Choose: ", 1, 4)
        if x == 1:
            wordlist()
        elif x == 2:
            train()
        elif x == 3:
            quit(0)
        else:
            settings["session"] = None
            settings["uname"] = None
            settings["pwd"] = None
            save_settings(filename, settings)
            quit(0)


settings = load_settings(filename)
if settings.get("session") is None:
    login(settings)
    w_sets = get_dict_from_site(settings["session"])
else:
    print("Authorization...")
    w_sets = get_dict_from_site(settings["session"])
    if w_sets is None:
        settings["session"] = skyeng_login(settings["uname"], settings["pwd"])
        if settings["session"] is None:
            print("Authorization filed.")
            login()
        w_sets = get_dict_from_site(settings["session"])

print(f"Loaded {len(w_sets)} set(s).")

save_settings(filename, settings)
main_menu()
