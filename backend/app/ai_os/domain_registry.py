"""
FHOS AI Operating System
Dynamic Domain Registry
"""


class DomainRegistry:

    def __init__(self):

        self.domains = {
            "Orthopedics": {
                "title": "Ортопедія",
                "role": "Аналізує кістки, суглоби, імпланти, ендопротезування.",
                "priority": "high",
            },
            "Traumatology": {
                "title": "Травматологія",
                "role": "Аналізує травми, ДТП, переломи, ускладнення.",
                "priority": "high",
            },
            "Radiology": {
                "title": "Радіологія",
                "role": "Аналізує рентген, КТ, МРТ, DICOM.",
                "priority": "high",
            },
            "Rehabilitation": {
                "title": "Реабілітація",
                "role": "Аналізує відновлення, навантаження, функцію.",
                "priority": "normal",
            },
            "Evidence": {
                "title": "Доказова медицина",
                "role": "Перевіряє клінічні настанови та рівень доказів.",
                "priority": "high",
            },
            "Devils Advocate": {
                "title": "Критичний експерт",
                "role": "Шукає альтернативні пояснення, помилки та відсутні дані.",
                "priority": "critical",
            },
        }

    def get(self, name: str):

        return self.domains.get(name)

    def list_all(self):

        return self.domains

    def add_domain(self, name: str, title: str, role: str, priority: str = "normal"):

        self.domains[name] = {
            "title": title,
            "role": role,
            "priority": priority,
        }

        return self.domains[name]


domain_registry = DomainRegistry()