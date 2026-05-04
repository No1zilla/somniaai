import os
import json
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

# 🔹 📌 Генерация поста для блога (JSON: body + seo_title + description + faq)
def generate_blog_post(topic):
    try:
        selected_dream_type = random.choice(DREAM_TYPES)
        selected_keywords = random.sample(SEO_KEYWORDS, k=2)
        additional_keywords = generate_seo_keywords(topic)
        all_keywords = selected_keywords + additional_keywords[:2]
        print(f"📌 SEO-ключи (blog): {all_keywords}")

        prompt = f"""
Ты профессиональный юнгианский аналитик и SEO-копирайтер.
Тема статьи: "{topic}"
Тип сна для иллюстрации: {selected_dream_type}
Ключевые слова, которые нужно органично вплести в body:
{", ".join(all_keywords)}

Сформируй ответ СТРОГО в формате JSON со следующими полями:

{{
  "seo_title": "SEO-оптимизированный заголовок до 60 символов, по паттерну «К чему снится X: толкование по Юнгу» или «X во сне — значение и смысл». ВАЖНО: должен содержать поисковый интент (что человек гуглит), без «Somnia AI» (мы добавим сами).",
  "description": "Meta description 140–160 символов: чёткое описание о чём статья + причина прочитать. Без «в этой статье», без «мы расскажем».",
  "body": "Markdown-текст 4–5 абзацев глубокого лонгрида. Структура: 1) короткий пример сна (~30%), 2) интерпретация по Юнгу с архетипами (~40%), 3) практический инсайт + 1–2 вопроса (~30%). Без заголовков (без #). Эмодзи запрещены. Никаких «каждому знакомо». Конкретные неожиданные детали. Никакого эзотерического пафоса.",
  "faq": [
    {{"question": "Точный вопрос, который люди гуглят про эту тему", "answer": "Ёмкий ответ 2–3 предложения, прямой и психологически точный"}},
    {{"question": "...", "answer": "..."}},
    {{"question": "...", "answer": "..."}}
  ]
}}

Ответ — ТОЛЬКО валидный JSON, без обёрток и комментариев.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты юнгианский аналитик и SEO-копирайтер. Отвечаешь строго JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1800,
            temperature=0.7,
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "seo_title": (data.get("seo_title") or topic).strip(),
            "description": (data.get("description") or "").strip(),
            "body": (data.get("body") or "").strip(),
            "faq": [
                {"question": (q.get("question") or "").strip(), "answer": (q.get("answer") or "").strip()}
                for q in (data.get("faq") or [])
                if q.get("question") and q.get("answer")
            ][:5],
            "keywords": all_keywords,
        }
    except Exception as e:
        print(f"❌ Ошибка OpenAI (blog JSON): {e}")
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

def _parse_keywords_str(s):
    if not s:
        return set()
    return {p.strip().lower() for p in re.split(r"[,;|]", s) if p.strip()}


def _abs_date_diff(a, b):
    from datetime import date as _date
    try:
        return abs((_date.fromisoformat(a) - _date.fromisoformat(b)).days)
    except Exception:
        return 10**9


def find_related_articles(target_filename, target_title, target_keywords, n=5):
    """Сканируем blog/, возвращаем n ближайших статей для блока «Похожие»."""
    target_date = extract_date_from_filename(target_filename) or ""
    target_kw = _parse_keywords_str(target_keywords) if isinstance(target_keywords, str) else set(
        k.lower() for k in (target_keywords or [])
    )

    candidates = []
    for name in os.listdir(BLOG_FOLDER):
        if not name.endswith(".html") or name == BLOG_INDEX or name == target_filename:
            continue
        date = extract_date_from_filename(name)
        if not date:
            continue
        try:
            with open(os.path.join(BLOG_FOLDER, name), "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        title = extract_title_from_html(os.path.join(BLOG_FOLDER, name)) or name
        m = re.search(
            r'<meta\s+name=["\']keywords["\']\s+content=["\']([^"\']*)["\']',
            content,
            re.IGNORECASE,
        )
        kw = _parse_keywords_str(m.group(1) if m else "")
        candidates.append({"filename": name, "title": title, "keywords": kw, "date": date})

    if target_kw:
        scored = []
        for a in candidates:
            overlap = len(target_kw & a["keywords"])
            if overlap > 0:
                scored.append((overlap, a))
        scored.sort(key=lambda x: (-x[0], _abs_date_diff(x[1]["date"], target_date)))
        related = [a for _, a in scored[:n]]
    else:
        related = []

    if len(related) < n:
        seen = {a["filename"] for a in related}
        fallback = sorted(
            [a for a in candidates if a["filename"] not in seen],
            key=lambda a: _abs_date_diff(a["date"], target_date),
        )
        related.extend(fallback[: n - len(related)])
    return related


def build_related_block_html(related):
    if not related:
        return ""
    items = "\n".join(
        f'    <li><a href="{quote(a["filename"])}">{html.escape(a["title"])}</a></li>'
        for a in related
    )
    return f"""<aside class="related" aria-label="Похожие статьи">
  <h2>Похожие статьи</h2>
  <ul>
{items}
  </ul>
</aside>"""


def make_meta_description(raw_text, max_len=160):
    """Делаем meta description из первых max_len символов чистого текста."""
    text = re.sub(r"```.*?```", " ", raw_text, flags=re.DOTALL)  # код-блоки
    text = re.sub(r"<[^>]+>", " ", text)  # HTML-теги
    text = re.sub(r"[#*_`>]+", " ", text)  # markdown
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:—–-") + "…"


# 🔹 📌 Функция сохранения статьи
def save_blog_post(title, content, all_keywords, seo_title=None, description=None, faq=None):
    raw_content = content
    content_html = markdown_to_html(content)

    slug = generate_slug(title)
    filename = f"{datetime.now().date()}-{slug}.html"
    filepath = os.path.join(BLOG_FOLDER, filename)

    if not description:
        description = make_meta_description(raw_content)
    page_title = (seo_title or title).strip()
    keywords_str = ", ".join(all_keywords)
    page_url = f"{SITE_URL}/blog/{quote(filename)}"
    publish_date = datetime.now().strftime("%Y-%m-%d")
    iso_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    escaped_h1 = html.escape(title)
    escaped_page_title = html.escape(page_title)
    escaped_description = html.escape(description)
    escaped_keywords = html.escape(keywords_str)

    article_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page_title,
        "alternativeHeadline": title,
        "description": description,
        "datePublished": iso_date,
        "dateModified": iso_date,
        "author": {"@type": "Organization", "name": "Somnia AI"},
        "publisher": {
            "@type": "Organization",
            "name": "Somnia AI",
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/favicon.ico"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
        "keywords": keywords_str,
        "inLanguage": "ru",
        "image": f"{SITE_URL}/night-landscape.webp",
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Блог", "item": f"{SITE_URL}/blog/blog.html"},
            {"@type": "ListItem", "position": 3, "name": title, "item": page_url},
        ],
    }
    schemas = [article_ld, breadcrumb_ld]

    faq_block = ""
    if faq:
        faq_ld = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": q["answer"]},
                }
                for q in faq
            ],
        }
        schemas.append(faq_ld)
        faq_items_html = "\n".join(
            f"  <details>\n    <summary>{html.escape(q['question'])}</summary>\n    <p>{html.escape(q['answer'])}</p>\n  </details>"
            for q in faq
        )
        faq_block = f"""<section class="faq" aria-label="Частые вопросы">
  <h2>Частые вопросы</h2>
{faq_items_html}
</section>"""

    json_ld_str = "\n".join(
        f'<script type="application/ld+json">\n{json.dumps(s, ensure_ascii=False, indent=2)}\n</script>'
        for s in schemas
    )

    breadcrumbs_html = f"""<nav class="breadcrumbs" aria-label="Хлебные крошки">
  <a href="../index.html">Главная</a> ›
  <a href="blog.html">Блог</a> ›
  <span>{escaped_h1}</span>
</nav>"""

    related = find_related_articles(filename, title, all_keywords, n=5)
    related_block = build_related_block_html(related)

    html_template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escaped_page_title} | Somnia AI</title>
<meta name="description" content="{escaped_description}">
<meta name="keywords" content="{escaped_keywords}">
<meta name="author" content="Somnia AI">
<meta name="robots" content="index,follow,max-image-preview:large">

<link rel="canonical" href="{page_url}">

<!-- Open Graph -->
<meta property="og:type" content="article">
<meta property="og:title" content="{escaped_page_title}">
<meta property="og:description" content="{escaped_description}">
<meta property="og:url" content="{page_url}">
<meta property="og:site_name" content="Somnia AI">
<meta property="og:locale" content="ru_RU">
<meta property="og:image" content="{SITE_URL}/night-landscape.webp">
<meta property="article:published_time" content="{iso_date}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escaped_page_title}">
<meta name="twitter:description" content="{escaped_description}">
<meta name="twitter:image" content="{SITE_URL}/night-landscape.webp">

<link rel="stylesheet" href="../css/article.css">

{json_ld_str}
</head>
<body>
<div class="container">
{breadcrumbs_html}
<article>
<h1>{escaped_h1}</h1>
<p class="article-meta"><time datetime="{publish_date}">{publish_date}</time> · Somnia AI</p>
{content_html}
</article>

{faq_block}

{related_block}

<hr>

<!-- 🔥 Блок ссылок на все сервисы Somnia AI -->
<div class="somnia-links">
<p>🔮 Расшифруйте ваши сны с помощью Нейросети
<a href="https://t.me/SomniaAI_bot" target="_blank" rel="noopener">Перейти в Telegram</a>
</p>

<p>📢 Подписывайтесь на наш канал в tg →
<a href="https://t.me/somnia_ai" target="_blank" rel="noopener">@somnia_ai</a>
</p>

<p>📲 Приложение Somnia AI в RuStore →
<a href="https://www.rustore.ru/catalog/app/com.somniaai.app" target="_blank" rel="noopener">Скачать</a>
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

    update_blog_index(title, filename)
    update_sitemap()

    print(f"✅ Статья сохранена: {filepath}")

def extract_date_from_filename(filename):
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", filename)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

def build_blog_index_html(articles):
    items = [
        f'<li><a href="{html.escape(quote(article["filename"]), quote=True)}">{html.escape(article["title"])}</a></li>'
        for article in articles
    ]
    items_html = "\n".join(items)

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
{items_html}
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

def extract_title_from_html(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"⚠️ Не удалось прочитать {filepath}: {e}")
        return None

    m = re.search(r"<title>(.*?)</title>", content, re.DOTALL | re.IGNORECASE)
    if m:
        title = html.unescape(m.group(1).strip())
        title = re.sub(r"\s*\|\s*Somnia AI\s*$", "", title)
        if title:
            return title

    m = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL | re.IGNORECASE)
    if m:
        return html.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())

    return None


# 🔹 📌 Обновление индекса блога
def update_blog_index(title, filename):
    """Перестраивает blog/blog.html по реальному содержимому папки blog/."""
    index_path = os.path.join(BLOG_FOLDER, BLOG_INDEX)

    articles = []
    seen = set()
    for name in sorted(os.listdir(BLOG_FOLDER)):
        if not name.endswith(".html") or name == BLOG_INDEX:
            continue
        if not extract_date_from_filename(name):
            continue  # пропускаем файлы без префикса YYYY-MM-DD-
        if name in seen:
            continue
        seen.add(name)

        article_title = extract_title_from_html(os.path.join(BLOG_FOLDER, name)) or name
        articles.append({"filename": name, "title": article_title})

    articles.sort(key=lambda a: a["filename"], reverse=True)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(build_blog_index_html(articles))

    print(f"✅ Блог-индекс перестроен: {len(articles)} статей")

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
    blog_data = generate_blog_post(topic)

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
    if blog_data and blog_data.get("body"):
        save_blog_post(
            title=topic,
            content=blog_data["body"],
            all_keywords=blog_data["keywords"],
            seo_title=blog_data.get("seo_title"),
            description=blog_data.get("description"),
            faq=blog_data.get("faq"),
        )

else:
    print("❌ Сегодня нет темы для публикации.")
