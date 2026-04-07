import requests

product_id = "177752258"
api_url = f"https://www.wildberries.ru/catalog/177752258/detail.aspx?targetUrl=MI{product_id}"

print(f"Проверяем ID: {product_id}")
print(f"URL: {api_url}")

try:
    response = requests.get(api_url, timeout=10)
    print(f"Статус: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get('data', {}).get('products'):
            product = data['data']['products'][0]
            price = product.get('salePriceU', 0) / 100
            name = product.get('name', '')
            print(f"\n✅ ТОВАР НАЙДЕН!")
            print(f"Название: {name}")
            print(f"Цена: {price} ₽")
            print(f"ID: {product_id} - РАБОТАЕТ!")
        else:
            print("❌ Товар не найден в ответе API")
    else:
        print(f"❌ Ошибка: {response.status_code}")

except Exception as e:
    print(f"❌ Ошибка: {e}")