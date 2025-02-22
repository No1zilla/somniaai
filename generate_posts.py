import os
import random
import pandas as pd
from datetime import datetime
import openai
import telebot
import vk_api
from transliterate import translit
import re

# 🔹 API-ключи
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VK_TOKEN = os.getenv("VK_TOKEN")
CHANNEL_ID = "@somnia_ai"  # Telegram-канал
VK_GROUP_ID = "-229159722"  # ID группы VK (со знаком "-")

# 🔹 Пути к файлам
CSV_FILE = "content_plan.csv"
BLOG_FOLDER = "blog"
BLOG_INDEX = "blog.html"

# 🔹 Подключаем API
# 🔹 Создаем экземпляр клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# 🔹 SEO-ключевые слова
SEO_KEYWORDS = [
    "сонник", "толкование снов", "к чему снится", "приснилось что", "осознанные сновидения",
    "сон", "значение снов", "во сне", "видеть во сне", "сонник онлайн", "Somnia AI",
    "сонник нейросеть", "кошмар", "сонник толкование"
]

# 🔹 Рекламные блоки
ADVERTISEMENTS = [
    "🔮 Расшифруйте ваши сны с помощью Нейросети → Somnia AI https://t.me/SomniaAI_bot",
    "📢 Подписывайтесь на наш канал Психология сновидений → telegram somnia_ai https://t.me/somnia_ai",
    "🌐 Интересные статьи о снах читайте в блоге на нашем сайте → somnia-ai.com https://somnia-ai.com/",
    "📲 Спросите Нейросеть Somnia AI про ваш сон в приложении → RuStore https://www.rustore.ru/catalog/app/com.somniaai.app"
]

# 🔹 📌 Функция получения темы
def get_today_topic():
    try:
        df = pd.read_csv(CSV_FILE)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d").dt.date
        today = datetime.now().date()
        topic_row = df[df["date"] == today]
        return topic_row.iloc[0]["topic"] if not topic_row.empty else None
    except Exception as e:
        print(f"❌ Ошибка чтения CSV-файла: {e}")
        return None
    
# 🔹 📌 Функция автоматического подбора ключевых слов через OpenAI
def generate_seo_keywords(topic):
    """OpenAI подбирает 3-5 дополнительных SEO-ключей для темы"""
    try:
        prompt = f"""
        Ты лучший в мире SEO-специалист. Подбери 3-5 популярных ключевых слов для статьи на тему: "{topic}".
        Выбирай слова, которые люди ищут в поиске Яндекс.
        Отдай список ключевых слов через запятую, без лишнего текста.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )

        return response.choices[0].message.content.split(", ") if response.choices else []
    except Exception as e:
        print(f"❌ Ошибка OpenAI (SEO-ключи): {e}")
        return []

# 🔹 📌 Генерация поста
def generate_post(topic, platform, length, style):
    try:
        # SEO-ключи 
        selected_keywords = random.sample(SEO_KEYWORDS, k=2)
        additional_keywords = generate_seo_keywords(topic)
        all_keywords = selected_keywords + additional_keywords[:2]  # Ограничиваем до 4 ключей


        # 🔹 📌 Выводим SEO-ключи в консоль для проверки
        print(f"📌 SEO-ключи ({platform}): {all_keywords}")

        prompt = f"""
        Вы эксперт по аналитической психологии снов и пишете пост для {platform.upper()} на тему "{topic}".
        Стиль текста: {style}. Пост должен быть профессиональным, но понятным и вдохновляющим, с примерами.
        Используйте ключевые слова {' и '.join(all_keywords)} 2-3 раза в тексте.
        Формат текста: {"краткий пост c структурой с подзаголовками и эмодзи до 500 символов" if length == "short" else "лонгрид, в 4-5 абзацев с заголовками и примерами"}.
        Избегайте повторений и формулировок "Сны - это". В конце добавьте 1-2 вопроса для обсуждения, используйте большое количество эмодзи.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800 if length == "long" else 500,
            temperature=0.7
        )
        post_text = response.choices[0].message.content if response.choices else None
        return post_text, all_keywords  # Обновленный return, возвращающий текст и ключевые слова
    except Exception as e:
        print(f"❌ Ошибка OpenAI ({platform}): {e}")
        return None

# 🔹 📌 Отправка в Telegram
def post_to_telegram(message, disable_web_page_preview=False):
    try:
        bot.send_message(CHANNEL_ID, message, disable_web_page_preview=disable_web_page_preview)
        print("✅ Сообщение отправлено в Telegram!")
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")

# 🔹 📌 Отправка в VK
def post_to_vk(message, hashtags):
    try:
        message = message + "\n\n" + hashtags
        owner_id = -abs(int(VK_GROUP_ID))
        response = vk.wall.post(owner_id=owner_id, from_group=1, message=message)
        print(f"✅ Сообщение отправлено в VK! ID поста: {response}")
    except Exception as e:
        print(f"❌ Ошибка VK: {e}")

def markdown_to_html(text):
    # Преобразование заголовков Markdown в HTML
    text = re.sub(r'(?m)^(######\s)(.*)$', r'<h6>\2</h6>', text)
    text = re.sub(r'(?m)^(#####\s)(.*)$', r'<h5>\2</h5>', text)
    text = re.sub(r'(?m)^(####\s)(.*)$', r'<h4>\2</h4>', text)
    text = re.sub(r'(?m)^(###\s)(.*)$', r'<h3>\2</h3>', text)
    text = re.sub(r'(?m)^(##\s)(.*)$', r'<h2>\2</h2>', text)
    text = re.sub(r'(?m)^(#\s)(.*)$', r'<h1>\2</h1>', text)
    
    # Преобразование жирного и курсивного текста
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    return text

# 🔹 📌 Функция для генерации slug (латинизированный URL)
def generate_slug(title):
    slug = translit(title, 'ru', reversed=True)  # Транслитерация с русского на латиницу
    slug = re.sub(r'[^a-zA-Z0-9-]', '-', slug.lower())  # Заменяем пробелы и символы на дефисы
    slug = re.sub(r'-+', '-', slug).strip('-')  # Убираем двойные дефисы
    return slug

# 🔹 📌 Функция сохранения статьи
def save_blog_post(title, content, all_keywords):
    content = markdown_to_html(content)  # Преобразование Markdown в HTML
    
    slug = generate_slug(title)  # Генерируем slug для URL
    filename = f"{datetime.now().date()}-{slug}.html"  # Создаём имя файла
    filepath = os.path.join(BLOG_FOLDER, filename)  # Полный путь
    
    keywords_str = ", ".join(all_keywords)  # Преобразуем ключевые слова в строку


    html_template = f"""
    <html>
    <head>
        <title>{title} | Somnia AI</title>
        <meta name="description" content="{title}">
        <meta name="keywords" content="{keywords_str}"> 
        
        <!-- Canonical URL -->
        <link rel="canonical" href="https://somnia-ai.com/blog/{filename}">     
        
        <!-- Стили -->
        <link rel="stylesheet" href="../css/article.css">       
    </head>
    <body>
        <div class="container">
            <p>{content.replace('\n', '<br>')}</p>
            <hr>
            <a href="blog.html">🔙 Вернуться к блогу</a>
        </div>    
    </body>
    </html>
    """

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_template)

    update_blog_index(title, filename)  # ✅ Теперь передаём filename (slug) в update_blog_index()

    print(f"✅ Статья сохранена: {filepath}")

# 🔹 📌 Обновление индекса блога
def update_blog_index(title, filename):
    index_path = os.path.join(BLOG_FOLDER, BLOG_INDEX)

    articles = []
    existing_filenames = set()

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            # Читаем существующий список статей, исключая лишние теги
            for line in f:
                if line.strip().startswith("<li>"):
                    articles.append(line)
                    match = re.search(r'href="([^"]+)"', line)
                    if match:
                        existing_filenames.add(match.group(1))  # Сохраняем уже добавленные ссылки

    # ✅ Проверяем, есть ли уже такая статья в списке
    if filename in existing_filenames:
        print(f"⚠️ Дубликат! Статья с таким filename уже есть: {filename}")
        return  # Не добавляем повторно

    # ✅ Проверяем, содержит ли filename кириллические символы
    if re.search(r'[а-яА-Я]', filename):
        print(f"⚠️ Ошибка! Filename содержит кириллицу и не будет добавлен: {filename}")
        return  # Не добавляем русскую ссылку

    # Создаём новую запись для списка
    new_entry = f'<li><a href="{filename}">{title}</a></li>\n'
    articles.insert(0, new_entry)  # Добавляем новую статью в начало

    # Перезаписываем индексный файл
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("<html>\n<head>\n<title>Блог Somnia AI</title>\n</head>\n<body>\n")
        f.write('<link rel="stylesheet" href="../css/blog.css">\n')  # ✅ Добавляем стили
        f.write("<h1>📚 Блог Somnia AI</h1>\n<ul>\n")
        f.writelines(articles)  # Уникальные записи
        f.write("</ul>\n</body>\n</html>\n")

    print("✅ Блог-индекс обновлён!")

# Генерация рандомной длины поста
def get_random_length():
    length = "short"  # Фиксируем только "short"
    print(f"📌 Выбрана длина поста: {length}")  # Логируем выбранную длину
    return length

# 🔹 📌 Запуск постинга
topic = get_today_topic()

if topic:
    print(f"🎯 Тема на сегодня: {topic}")

    # 🔹 Генерация рандомной длины постов
    tg_length = get_random_length()  # Рандомная длина для Telegram
    vk_length = get_random_length()  # Рандомная длина для ВКонтакте

    # Генерация постов
    tg_post_text, _ = generate_post(topic, "telegram", tg_length, "дружеский")
    vk_post_text, vk_keywords = generate_post(topic, "vk", vk_length, "аналитический")
    blog_post_text, blog_keywords = generate_post(topic, "blog", "long", "экспертный")

    # Рандомная реклама
    ad = random.choice(ADVERTISEMENTS)

    # 📢 Публикация в Telegram
    if tg_post_text:
        cleaned_tg_text = tg_post_text.replace('#', '').replace('*', '')  # Убираем Markdown-синтаксис
        formatted_message = f"{cleaned_tg_text.split('\n', 1)[0]}\n{cleaned_tg_text.split('\n', 1)[1]}" if '\n' in cleaned_tg_text else cleaned_tg_text
        tg_hashtags = " ".join([f"#{word.replace(' ', '_')}" for word in vk_keywords])  # Генерация хэштегов
        # ✅ Добавляем хэштеги в текст перед отправкой
        final_message = f"{formatted_message}\n\n{ad}\n\n{tg_hashtags}"
        post_to_telegram(final_message, disable_web_page_preview=True)  # Теперь аргументы правильные


    # 🔵 Публикация в ВКонтакте
    if vk_post_text:
        clean_vk_text = vk_post_text.replace("#", "").replace("*", "")  # Убираем Markdown-символы
        hashtags = " ".join([f"#{word.replace(' ', '_')}" for word in vk_keywords])  # Генерация хэштегов
        post_to_vk(f"{clean_vk_text}\n\n{ad}", hashtags)  # Отправляем очищенный текст с рекламой и хэштегами


    # 🌍 Публикация в блог
    if blog_post_text:
        blog_post_with_ad = f"{blog_post_text}\n\n<hr>\n<p><strong>{ad}</strong></p>"  # ✅ Добавляем рекламу в блог-статью
        save_blog_post(topic, blog_post_with_ad, blog_keywords)
        update_blog_index(topic, f"{datetime.now().date()}-{topic.lower().replace(' ', '-').replace('?', '')}.html")

else:
    print("❌ Сегодня нет темы для публикации.")
