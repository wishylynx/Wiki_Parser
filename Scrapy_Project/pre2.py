import scrapy
import logging

class MoviesSpider(scrapy.Spider):
    name = "movies"
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = [
        'https://ru.wikipedia.org/wiki/Категория:Фильмы_по_годам'
    ]

    def parse(self, response):
        # Извлечение ссылок на страницы с фильмами по годам
        year_links = response.css('div.CategoryTreeItem a::attr(href)').getall()
        for link in year_links:
            # Переход по извлеченным ссылкам для дальнейшего скрапинга
            yield response.follow(link, self.parse_year_page)

    def parse_year_page(self, response):
        # Извлечение ссылок на страницы отдельных фильмов
        movie_links = response.css('div.mw-category-group a::attr(href)').getall()
        for link in movie_links:
            # Переход на страницу каждого фильма для извлечения детальной информации
            yield response.follow(link, self.parse_movie_details)

    def parse_movie_details(self, response):
        try:
            directors = response.xpath(
                '//th[contains(text(), "Режиссёр")]/following-sibling::td//a/text() | '
                '//th[contains(text(), "Режиссёр")]/following-sibling::td//span[not(a)]/text()'
            ).getall()
            directors = [d.strip() for d in directors if d.strip()]  # Очистка от лишних пробелов
            directors_str = ', '.join(directors)  # Объединение в строку

            title = response.xpath('//th[contains(@class, "infobox-above")]/text()').get()

            if title:
                title = title.strip()
            else:
                # В качестве резервного варианта, попробуйте найти название в <h1>
                title = response.css('h1::text').get().strip()

            # Собираем жанры, которые являются ссылками
            linked_genres = response.css('span[data-wikidata-property-id="P136"] a::text').getall()
            # Собираем жанры, которые указаны просто текстом
            text_genres = response.css('span[data-wikidata-property-id="P136"]::text').getall()
            # Объединяем оба списка и удаляем лишние пробелы
            genres = [g.strip() for g in linked_genres + text_genres if g.strip() and g.strip() != "," and g.strip() != "'"]
            # Убираем дубликаты
            genres = list(set(genres))
            # Преобразуем список в строку
            genre_str = ', '.join(genres)


            country_elements = response.css(
                'th:contains("Страна") + td a::text, th:contains("Страны") + td a::text').getall()
            if not country_elements:
                country_elements = response.css('th:contains("Страна") + td, th:contains("Страны") + td').xpath(
                    './/text()').getall()
            countries = [country.strip() for country in country_elements if country.strip()]
            country_str = ', '.join(countries)


            yield {
                'title': title,


                'director': directors_str if directors_str else None,


                'country': country_str if country_str else None,
                'genre': genre_str if genre_str else None,
                'year': response.xpath('//th[contains(text(), "Год")]/following-sibling::td//text()').re_first(r'\d{4}'),
            }
        except Exception as e:
            logging.error(f"Error processing {response.url}: {str(e)}")
