import datetime
import requests
from .models import Author, Tag, Article
from django.utils import timezone
from bs4 import BeautifulSoup


def parse_habr_articles():
    print("Начало парсинга статей...")
    url = 'https://habr.com/ru/articles/'
    response = requests.get(url).text
    data = BeautifulSoup(response, 'html.parser')

    for article in data.find_all('h2', class_='tm-title tm-title_h2')[:5]:
        title = article.a.span.text
        link = 'https://habr.com' + article.a['href']
        print("Сохранение статьи:")
        print("Заголовок:", title)
        print("Ссылка:", link)

        # Получаем содержимое каждой статьи по ссылке
        article_response = requests.get(link).text
        article_data = BeautifulSoup(article_response, 'html.parser')

        # Извлекаем автора и время публикации
        author_element = article_data.find('a', class_='tm-user-info__username')
        if author_element:
            author_name = author_element.get_text(strip=True)
        else:
            author_name = "No author available"
        print("Автор:", author_name)

        time_element = article_data.find('time')
        if time_element:
            time_published = time_element['title']
        else:
            time_published = "Unknown"
        print("Время публикации:", time_published)

        # Извлекаем содержание статьи
        content = (article_data.find('div', class_='tm-article-body').text.strip())[:500]
        print("Содержание:", content)

        # Извлекаем теги
        tags_element = article_data.find('div', class_='tm-article-presenter__meta-list')
        if tags_element:
            tags = [tag.text.strip() for tag in tags_element.find_all('a', class_='tm-tags-list__link')]
        else:
            tags = []

        print("Теги:", tags)

        # Поиск блока с изображением
        image_block = article_data.find('div', class_='tm-article-snippet__cover')
        if image_block:
            # Поиск тега img внутри блока
            image_tag = image_block.find('img')
            if image_tag:
                image_url = image_tag['src']
            else:
                image_url = None
        else:
            image_url = None

        print("Ссылка на изображение:", image_url)

        # Сохраняем данные в базе данных
        try:
            # Проверяем, существует ли уже статья с таким заголовком
            existing_article = Article.objects.filter(title=title).first()
            if existing_article:
                print(f"Статья с заголовком '{title}' уже существует в базе данных, пропускаем")
                continue

            # Проверяем, существует ли уже автор в базе данных
            author, created = Author.objects.get_or_create(name=author_name)

            # Сохраняем статью в базе данных
            new_article = Article.objects.create(
                title=title,
                link=link,
                date=timezone.now() if time_published == "Unknown" else timezone.make_aware(
                    datetime.datetime.strptime(time_published, "%Y-%m-%d, %H:%M")),
                author=author,
                image_url=image_url,
                content=content,
            )

            # Пытаемся получить теги и связать их со статьей
            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if tag:
                    new_article.tags.add(tag)
                else:
                    print(f"Тег {tag_name} не найден")
        except Exception as e:
            print(f"Ошибка сохранения статьи в базе данных: {e}")