from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def system_status():
    return {
        "модуль": "API Core",
        "статус": "працює",
        "опис": "API Core об'єднує всі модулі FHOS через єдину точку доступу.",
    }
