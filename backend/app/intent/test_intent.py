"""
Manual Intent Engine Test
"""

from app.intent.engine import IntentEngine


engine = IntentEngine()

requests = [
    "У мене болить голова третій день",
    "Чи можна мені Спазмалгон?",
    "Ось моє МРТ попереку",
    "ТТГ 15, що це означає?",
    "Задуха і втрата свідомості",
]

for item in requests:
    result = engine.analyze(item)

    print("\nREQUEST:", item)
    print(result)