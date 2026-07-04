from datetime import date


def calculate_age(birth_date: date, as_of: date | None = None) -> int:
    """Обчислює повний вік у роках на вказану дату (за замовчуванням — сьогодні).

    Враховує, чи вже минув день народження в поточному році — проста різниця
    років дала б хибний результат 31 грудня напередодні дня народження.
    """
    reference_date = as_of if as_of is not None else date.today()
    age = reference_date.year - birth_date.year
    had_birthday_this_year = (reference_date.month, reference_date.day) >= (
        birth_date.month,
        birth_date.day,
    )
    if not had_birthday_this_year:
        age -= 1
    return age