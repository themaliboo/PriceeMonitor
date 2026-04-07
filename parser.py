import requests
from bs4 import BeautifulSoup
import re
import random
import time

# ========== НАСТРОЙКИ ПРОКСИ (пока отключены) ==========
USE_PROXY = False  # Для Aliexpress, Avito, Ozon прокси не нужны

# Список прокси (оставлен для Wildberries на будущее)
PROXY_LIST = []


class CompetitorParser:
    def __init__(self):
        self.current_proxy_index = 0
        self.failed_proxies = set()

    def _get_proxy(self):
        if not USE_PROXY or not PROXY_LIST:
            return None
        available = [i for i in range(len(PROXY_LIST)) if i not in self.failed_proxies]
        if not available:
            self.failed_proxies.clear()
            available = list(range(len(PROXY_LIST)))
        self.current_proxy_index = random.choice(available)
        proxy_url = PROXY_LIST[self.current_proxy_index]
        return {'http': proxy_url, 'https': proxy_url}

    def _mark_proxy_failed(self):
        self.failed_proxies.add(self.current_proxy_index)

    def _get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    # ========== ALIEXPRESS (НОВЫЙ! БЕЗ ПРОКСИ) ==========
    def parse_aliexpress(self, url):
        """Парсинг Aliexpress - работает без прокси"""
        try:
            headers = self._get_headers()
            print(f"Парсинг Aliexpress: {url}")
            time.sleep(random.uniform(1, 2))

            response = requests.get(url, headers=headers, timeout=15)
            print(f"Статус ответа: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Способ 1: JSON в скриптах
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'price' in script.string.lower():
                        # Поиск цены в JSON
                        match = re.search(r'"priceValue":\s*"?([\d.]+)"?', script.string)
                        if not match:
                            match = re.search(r'"price":\s*"?([\d.]+)"?', script.string)
                        if match:
                            price = float(match.group(1))
                            print(f"✅ Цена Aliexpress: {price}")
                            return {'price': price, 'platform': 'aliexpress', 'status': 'success'}

                # Способ 2: HTML элементы
                price_elem = soup.select_one('.product-price-value')
                if not price_elem:
                    price_elem = soup.select_one('[data-price]')
                if not price_elem:
                    price_elem = soup.select_one('.price')

                if price_elem:
                    price_text = price_elem.get_text().strip()
                    # Извлекаем число
                    match = re.search(r'([\d.]+)', price_text)
                    if match:
                        price = float(match.group(1))
                        print(f"✅ Цена Aliexpress: {price}")
                        return {'price': price, 'platform': 'aliexpress', 'status': 'success'}

                print("Цена не найдена")
                return None
            else:
                print(f"Ошибка HTTP: {response.status_code}")
                return None

        except Exception as e:
            print(f"Aliexpress ошибка: {e}")
            return None

    # ========== AVITO ==========
    def parse_avito(self, url):
        """Парсинг Avito - без прокси"""
        try:
            headers = self._get_headers()
            print(f"Парсинг Avito: {url}")
            time.sleep(random.uniform(1, 2))

            response = requests.get(url, headers=headers, timeout=15)
            print(f"Статус ответа: {response.status_code}")

            if response.status_code == 200:
                match = re.search(r'"price":\s*"?(\d+)"?', response.text)
                if match:
                    price = float(match.group(1))
                    print(f"✅ Цена Avito: {price}")
                    return {'price': price, 'platform': 'avito', 'status': 'success'}
            return None
        except Exception as e:
            print(f"Avito ошибка: {e}")
            return None

    # ========== OZON ==========
    def parse_ozon(self, url):
        """Парсинг Ozon - без прокси"""
        try:
            headers = self._get_headers()
            print(f"Парсинг Ozon: {url}")
            time.sleep(random.uniform(1, 2))

            response = requests.get(url, headers=headers, timeout=15)
            print(f"Статус ответа: {response.status_code}")

            if response.status_code == 200:
                match = re.search(r'"price":"?(\d+)"?', response.text)
                if not match:
                    match = re.search(r'"final_price":(\d+)', response.text)
                if not match:
                    match = re.search(r'"current_price":(\d+)', response.text)

                if match:
                    price = int(match.group(1))
                    if price > 10000:
                        price = price / 100
                    print(f"✅ Цена Ozon: {price}")
                    return {'price': price, 'platform': 'ozon', 'status': 'success'}
            return None
        except Exception as e:
            print(f"Ozon ошибка: {e}")
            return None

    # ========== WILDBERRIES (требует прокси) ==========
    def parse_wildberries(self, url):
        """Парсинг Wildberries - требует хорошие резидентные прокси"""
        print("⚠️ Wildberries требует прокси. Пока используйте Avito, Ozon или Aliexpress.")
        return None

    # ========== УНИВЕРСАЛЬНЫЙ МЕТОД ==========
    def parse(self, platform, url):
        if platform == 'avito':
            return self.parse_avito(url)
        elif platform == 'ozon':
            return self.parse_ozon(url)
        elif platform == 'aliexpress':
            return self.parse_aliexpress(url)
        elif platform == 'wildberries':
            return self.parse_wildberries(url)
        else:
            return None