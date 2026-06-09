"""
Модуль для работы с интернетом - поиск, сайты, переводчик
"""
import webbrowser
import urllib.parse

#####################################################################################################
                                                                                                    #
KEYWORDS = [                                                                                        #
    "найди в интернете", "загугли", "поищи", "что такое", "кто такой", "wiki", "википедия",         #
    "переведи", "перевод", "translate",                                                             #
    "новости", "почта", "gmail", "mail", "яндекс", "вконтакте", "вк", "telegram", "телеграм",       #
    "instagram", "инстаграм", "twitter", "твиттер", "facebook", "фейсбук",                          #
    "github", "гитхаб", "stackoverflow", "reddit", "twitch", "твич",                                #
    "кинопоиск", "imdb", "netflix", "нетфликс"                                                      #
]                                                                                                   #
                                                                                                    #
SITES = {                                                                                           #
    "вконтакте": "https://vk.com",                                                                  #
    "вк": "https://vk.com",                                                                         #
    "telegram": "https://web.telegram.org",                                                         #
    "телеграм": "https://web.telegram.org",                                                         #
    "instagram": "https://instagram.com",                                                           #
    "инстаграм": "https://instagram.com",                                                           #
    "twitter": "https://twitter.com",                                                               #   Ключеывые слова для активации.
    "твиттер": "https://twitter.com",                                                               #
    "facebook": "https://facebook.com",                                                             #
    "фейсбук": "https://facebook.com",                                                              #
    "github": "https://github.com",                                                                 #
    "гитхаб": "https://github.com",                                                                 #
    "stackoverflow": "https://stackoverflow.com",                                                   #
    "reddit": "https://reddit.com",                                                                 #
    "twitch": "https://twitch.tv",                                                                  #
    "твич": "https://twitch.tv",                                                                    #
    "новости": "https://news.google.com",                                                           #
    "gmail": "https://mail.google.com",                                                             #
    "почта": "https://mail.google.com",                                                             #
    "mail": "https://mail.google.com",                                                              #
    "яндекс": "https://ya.ru",                                                                      #
    "кинопоиск": "https://kinopoisk.ru",                                                            #
    "imdb": "https://imdb.com",                                                                     #
    "netflix": "https://netflix.com",                                                               #
    "нетфликс": "https://netflix.com",                                                              #
    "википедия": "https://ru.wikipedia.org",                                                        #
    "wiki": "https://ru.wikipedia.org"                                                              #
}                                                                                                   #
                                                                                                    #
#####################################################################################################

def handle_command(text, tts, config, **kwargs):        # Инициализация
    text = text.lower().strip()                         #

    #############################################################################################################################################         
                                                                                                                                                #
    qwen_data = config.pop('qwen_context', None)                                                                                                #
    if qwen_data:                                                                                                                               #
        action = qwen_data.get("action", "").lower()                                                                                            #
        target = str(qwen_data.get("target", ""))                                                                                               #
                                                                                                                                                #
        try:                                                                                                                                    #
            if "поиск" in action or "найди" in action or "загугли" in action:                                                                   #
                url = f"https://www.google.com/search?q={urllib.parse.quote(target)}"                                                           #
                webbrowser.open(url)                                                                                                            #
                if tts: tts.speak(f"Ищу {target}")                                                                                              #
            elif "перевод" in action or "переведи" in action:                                                                                   # Блок извлечения Qwen (старый код, сейчас не активен)
                url = f"https://translate.google.com/?sl=auto&tl=en&text={urllib.parse.quote(target)}"                                          # возможно позже верну в цикл, но пока идей нет
                webbrowser.open(url)                                                                                                            #
                if tts: tts.speak("Открываю переводчик")                                                                                        #
            elif "сайт" in action or "открой" in action:                                                                                        #
                url = target if target.startswith("http") else SITES.get(target.lower(), f"https://www.google.com/search?q={target}")           #
                webbrowser.open(url)                                                                                                            #
                if tts: tts.speak("Открываю")                                                                                                   #
        except Exception as e:                                                                                                                  #
            print(f"Ошибка Qwen в web_control: {e}")                                                                                            #
        return True                                                                                                                             #
                                                                                                                                                #
    #############################################################################################################################################

    #####################################################################################################################
    # Поиск информации                                                                                                  #
    if any(phrase in text for phrase in ["что такое", "кто такой", "кто такая"]):         #
        query = text                                                                                                    #
        for phrase in ["что такое", "кто такой", "кто такая"]:                            #
            query = query.replace(phrase, "")                                                                           #
        query = query.strip()                                                                                           #
        if query:                                                                                                       #
            url = f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(query)}"                                          #
            webbrowser.open(url)                                                                                        #
            if tts: tts.speak(f"Ищу информацию о {query}")                                                              #
        return                                                                                                          #
                                                                                                                        #
    # Поиск в интернете                                                                                                 #
    if any(phrase in text for phrase in ["найди в интернете", "загугли", "поищи", "найди"]):                            #
        query = text                                                                                                    #
        for phrase in ["найди в интернете", "загугли", "поищи", "найди"]:                                               #
            query = query.replace(phrase, "")                                                                           #
        query = query.strip()                                                                                           #
        if query:                                                                                                       #
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"                                        #
            webbrowser.open(url)                                                                                        #
            if tts: tts.speak(f"Ищу {query}")                                                                           #
        return                                                                                                          # Блок выбора действия.
                                                                                                                        #
    # Переводчик                                                                                                        #
    if "переведи" in text or "перевод" in text:                                                                         #
        query = text.replace("переведи", "").replace("перевод", "").strip()                                             #
        if query:                                                                                                       #
            url = f"https://translate.google.com/?sl=auto&tl=en&text={urllib.parse.quote(query)}"                       #
            webbrowser.open(url)                                                                                        #
            if tts: tts.speak("Открываю переводчик")                                                                    #
        else:                                                                                                           #
            webbrowser.open("https://translate.google.com")                                                             #
            if tts: tts.speak("Открываю переводчик")                                                                    #
        return                                                                                                          #
                                                                                                                        #
    # Открытие сайтов                                                                                                   #
    for site_name, site_url in SITES.items():                                                                           #
        if site_name in text:                                                                                           #
            webbrowser.open(site_url)                                                                                   #
            if tts: tts.speak(f"Открываю {site_name}")                                                                  #
            return                                                                                                      #
#########################################################################################################################