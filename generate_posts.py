import os
import random
import pandas as pd
from datetime import datetime
import openai
import telebot
import vk_api
from transliterate import translit
import re
import html
from urllib.parse import quote

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
SITE_URL = "https://somnia-ai.com"

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

# 🔹 Типы сна (для разнообразия контента)
DREAM_TYPES = [
    "тревожный городской сон",
    "сон с элементами абсурда",
    "минималистичный сон с одним символом",
    "сон с диалогом",
    "повторяющийся сон",
    "сон-лабиринт",
    "сон о встрече с незнакомцем",
    "сон о потере или поиске",
    "сон в замкнутом пространстве",
    "сон с искажением времени"
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
        Подбери 3-5 популярных ключевых слов для статьи на тему: "{topic}".
        Фразы должны быть поисковыми запросами Яндекс.
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
        selected_dream_type = random.choice(DREAM_TYPES)
        
        # SEO-ключи 
        selected_keywords = random.sample(SEO_KEYWORDS, k=2)
        additional_keywords = generate_seo_keywords(topic)
        all_keywords = selected_keywords + additional_keywords[:2]  # Ограничиваем до 4 ключей


        # 🔹 📌 Выводим SEO-ключи в консоль для проверки
        print(f"📌 SEO-ключи ({platform}): {all_keywords}")

        prompt = f"""
        Ты профессиональный юнгианский аналитик и автор интеллектуального Telegram-канала о психологии сновидений.
        
        Создай пост для {platform.upper()} по теме "{topic}" в стиле {style}.
        Тип сна: {selected_dream_type}
        
        Требования к содержанию:
        — текст эмоционально захватывающий, но психологически точный
        — избегай банальных образов (цветы, море, шторм, полёт, лестница)
        — используй конкретные, неожиданные детали
        — сон должен содержать внутренний конфликт или напряжение
        — не используй эзотерический пафос
        — не пиши как учебник
        — не используй обобщения типа «каждому знакомо»
        
        Структура (без заголовков):
        — сначала сон (примерно 40% текста)
        — затем интерпретация в духе Карла Юнга (40%)
        — затем мягкий инсайт и 1–2 вопроса (20%)
        
        Органично вплети ВСЕ ключевые слова, не изменяя их форму:
        {", ".join(all_keywords)}
        
        Формат:
        {"2–3 абзаца с 1–2 эмодзи" if length=="short" else "4–5 абзацев, глубокий лонгрид"}
        
        Тон:
        живой, интеллектуальный, без мистики.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты профессиональный юнгианский аналитик. Пиши глубоко, без эзотерики и без клише."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800 if length == "long" else 500,
            temperature=0.8
        )
        post_text = response.choices[0].message.content if response.choices else None
        return post_text, all_keywords  # Обновленный return, возвращающий текст и ключевые слова
    except Exception as e:
        print(f"❌ Ошибка OpenAI ({platform}): {e}")
        return None, []

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
    
    # Разбиваем на смысловые блоки и оборачиваем в <p>, если это не заголовок
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    html_blocks = []
    for block in blocks:
        if re.match(r"^<h[1-6]>.*</h[1-6]>$", block):
            html_blocks.append(block)
            continue
        html_blocks.append(f"<p>{block.replace(chr(10), '<br>')}</p>")
    return "\n".join(html_blocks)

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
    escaped_title = html.escape(title)
    escaped_keywords = html.escape(keywords_str)
    
    html_template = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{escaped_title} | Somnia AI</title>
            <meta name="description" content="{escaped_title}">
            <meta name="keywords" content="{escaped_keywords}">
            <meta name="robots" content="index,follow,max-image-preview:large">
            
            <!-- Canonical URL -->
            <link rel="canonical" href="{SITE_URL}/blog/{quote(filename)}">     
            
            <!-- Стили -->
            <link rel="stylesheet" href="../css/article.css">       
        </head>
        <body>
            <div class="container">
                <h1>{escaped_title}</h1>
                {content}
    
                <hr>
                
                <!-- 🔥 Блок ссылок на все сервисы Somnia AI -->
                <div class="somnia-links">
                    <p>🔮 Расшифруйте ваши сны с помощью Нейросети
                        <a href="https://t.me/SomniaAI_bot" target="_blank">Перейти в Telegram </a>
                    </p>
    
                    <p>📢 Подписывайтесь на наш канал в tg → 
                        <a href="https://t.me/somnia_ai" target="_blank">@somnia_ai</a>
                    </p>
    
                    <p>📲 Приложение Somnia AI в RuStore → 
                        <a href="https://www.rustore.ru/catalog/app/com.somniaai.app" target="_blank">Скачать</a>
                    </p>
                </div>
    
                <hr>
    
                <a href="blog.html">🔙 Вернуться к блогу</a>
            </div>    
        </body>
        </html>
    """

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_template)

    update_blog_index(title, filename)  # ✅ Теперь передаём filename (slug) в update_blog_index()
    update_sitemap()

    print(f"✅ Статья сохранена: {filepath}")

def extract_date_from_filename(filename):
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", filename)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

def build_blog_index_html(articles):
    items = []
    for article in articles:
        items.append(f'<li><a href="{article["filename"]}">{article["title"]}</a></li>')

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Блог Somnia AI | Анализ снов и психология сновидений</title>
<meta name="description" content="Статьи Somnia AI о психологии сновидений, символах сна и практиках самопонимания. Выбирайте темы, читайте лонгриды и находите полезные инсайты.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{SITE_URL}/blog/blog.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/blog.css">
</head>
<body>
<main class="page">
  <section class="blog-top">
    <h1>Блог Somnia AI</h1>
    <p>Подборка материалов о снах, архетипах и внутренней динамике. Используйте поиск и фильтр по году, чтобы быстро найти нужную статью.</p>
  </section>
  <section class="blog-controls" aria-label="Фильтры статей">
    <input id="blog-search" class="control" type="search" placeholder="Поиск по заголовку статьи">
    <select id="blog-year" class="control">
      <option value="all">Все годы</option>
    </select>
  </section>
  <div class="meta-row">
    <span id="articles-total">{len(articles)} статей</span>
    <span>Обновляется автоматически при публикации новых статей</span>
  </div>
  <ul id="articles-list">
{"".join(items)}
</ul>
  <div id="pagination" class="pagination" aria-label="Навигация по страницам блога"></div>
  <p class="blog-back"><a href="../index.html">На главную Somnia AI</a></p>
</main>
<script src="../js/blog.js"></script>
</body>
</html>
"""

def update_sitemap():
    sitemap_path = "sitemap.xml"

    urls = [
        {"loc": f"{SITE_URL}/", "lastmod": datetime.now().strftime("%Y-%m-%d"), "priority": "1.0"},
        {"loc": f"{SITE_URL}/blog/blog.html", "lastmod": datetime.now().strftime("%Y-%m-%d"), "priority": "0.9"},
    ]

    for name in os.listdir(BLOG_FOLDER):
        if not name.endswith(".html") or name == BLOG_INDEX:
            continue
        date_from_filename = extract_date_from_filename(name)
        lastmod = date_from_filename or datetime.now().strftime("%Y-%m-%d")
        urls.append({
            "loc": f"{SITE_URL}/blog/{quote(name)}",
            "lastmod": lastmod,
            "priority": "0.8",
        })

    url_entries = []
    for url in urls:
        url_entries.append(
            "   <url>\n"
            f"      <loc>{url['loc']}</loc>\n"
            f"      <lastmod>{url['lastmod']}</lastmod>\n"
            "      <changefreq>weekly</changefreq>\n"
            f"      <priority>{url['priority']}</priority>\n"
            "   </url>\n"
        )

    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(url_entries)
        + "</urlset>\n"
    )

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print("✅ Sitemap обновлён!")

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
                    match = re.search(r'href="([^"]+)">([^<]+)<', line)
                    if match:
                        parsed_filename = match.group(1)
                        parsed_title = match.group(2)
                        articles.append({"filename": parsed_filename, "title": parsed_title})
                        existing_filenames.add(parsed_filename)

    # ✅ Проверяем, есть ли уже такая статья в списке
    if filename in existing_filenames:
        print(f"⚠️ Дубликат! Статья с таким filename уже есть: {filename}")
        return  # Не добавляем повторно

    # ✅ Проверяем, содержит ли filename кириллические символы
    if re.search(r'[а-яА-Я]', filename):
        print(f"⚠️ Ошибка! Filename содержит кириллицу и не будет добавлен: {filename}")
        return  # Не добавляем русскую ссылку

    # Создаём новую запись для списка
    articles.insert(0, {"filename": filename, "title": title})  # Добавляем новую статью в начало

    # Сортируем по дате в имени файла по убыванию
    articles.sort(key=lambda article: article["filename"], reverse=True)

    # Перезаписываем индексный файл
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(build_blog_index_html(articles))

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
        save_blog_post(topic, blog_post_text, blog_keywords)

else:
    print("❌ Сегодня нет темы для публикации.")
