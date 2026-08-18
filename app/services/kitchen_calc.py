from typing import List, Dict

def generate_food_ration(people: int, days: int) -> List[Dict[str, str]]:
    """
    Генерирует сбалансированную раскладку продуктов на поход / рыбалку.
    Нормы рассчитаны на полевые условия (3-разовое горячее питание + перекусы).
    """
    people = max(1, people)
    days = max(1, days)
    person_days = people * days

    items = [
        # Вода и напитки
        {"category": "drinks", "name": "Питьевая вода в канистрах/бутылях", "amount": f"{person_days * 2.5:.1f} л", "assigned_to": "Все"},
        {"category": "drinks", "name": "Чай листовой / пакетированный", "amount": f"{max(1, person_days // 4)} пач", "assigned_to": "Дежурный"},
        {"category": "drinks", "name": "Кофе растворимый / молотый", "amount": f"{max(1, person_days // 6)} пач/бан", "assigned_to": "Дежурный"},
        {"category": "drinks", "name": "Сахар-песок / рафинад", "amount": f"{person_days * 50 / 1000:.1f} кг", "assigned_to": "Дежурный"},
        
        # Мясо, рыба и консервы
        {"category": "meat", "name": "Тушенка говяжья/свиная (ГОСТ)", "amount": f"{person_days * 1} бан", "assigned_to": "Закупщик"},
        {"category": "meat", "name": "Мясо для шашлыка (в 1-й вечер)", "amount": f"{people * 0.4:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "meat", "name": "Колбаса с/к или охотничьи колбаски", "amount": f"{person_days * 60 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "meat", "name": "Сыр твердый", "amount": f"{person_days * 50 / 1000:.1f} кг", "assigned_to": "Закупщик"},

        # Крупы и макароны
        {"category": "grains", "name": "Гречневая крупа / Рис (для гарнира и ухи)", "amount": f"{person_days * 80 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "grains", "name": "Макароны твердых сортов", "amount": f"{person_days * 80 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "grains", "name": "Овсяные хлопья (на завтрак)", "amount": f"{person_days * 50 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "grains", "name": "Хлеб свежий + сухари/хлебцы", "amount": f"{person_days * 0.5:.1f} бух", "assigned_to": "Закупщик"},

        # Овощи и зелень
        {"category": "veggies", "name": "Картофель (для ухи и запекания в углях)", "amount": f"{person_days * 200 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "veggies", "name": "Лук репчатый + морковь", "amount": f"{person_days * 80 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "veggies", "name": "Огурцы и помидоры свежие", "amount": f"{person_days * 150 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "veggies", "name": "Зелень свежая (укроп, петрушка, зеленый лук)", "amount": f"{max(1, person_days // 4)} пуч", "assigned_to": "Закупщик"},

        # Специи и соусы
        {"category": "spices", "name": "Соль крупная пищевая (для готовки и рыбы)", "amount": f"{1.0 if days > 2 else 0.5} кг", "assigned_to": "Дежурный"},
        {"category": "spices", "name": "Черный перец (горошек + молотый) + лавровый лист", "amount": "1 компл", "assigned_to": "Дежурный"},
        {"category": "spices", "name": "Подсолнечное масло для жарки", "amount": f"{1 if days > 2 else 0.5} бут", "assigned_to": "Дежурный"},
        {"category": "spices", "name": "Кетчуп / горчица / майонез", "amount": "2 упак", "assigned_to": "Закупщик"},

        # Перекусы и сладости
        {"category": "snacks", "name": "Печенье, вафли, сгущенное молоко", "amount": f"{person_days * 70 / 1000:.1f} кг", "assigned_to": "Закупщик"},
        {"category": "snacks", "name": "Орехи, сухофрукты, шоколад (быстрые калории)", "amount": f"{person_days * 50 / 1000:.1f} кг", "assigned_to": "Закупщик"},
    ]

    return items
