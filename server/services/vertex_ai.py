import os
from functools import lru_cache
from typing import Optional

import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "credentials", "vertex_service_account.json")

VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
DEFAULT_TEXT_MODEL = os.getenv("VERTEX_MODEL_NAME", "gemini-1.0-pro")
DEFAULT_VISION_MODEL = os.getenv("VERTEX_VISION_MODEL_NAME", "gemini-1.0-pro-vision")


def _get_credentials_path() -> str:
    """서비스 계정 JSON 파일 경로 반환"""
    return os.getenv("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_CREDENTIALS_PATH)


def _load_credentials():
    credentials_path = _get_credentials_path()
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            "Vertex AI 자격 증명 파일을 찾을 수 없습니다. "
            "GOOGLE_APPLICATION_CREDENTIALS 환경 변수를 설정하거나 "
            f"{credentials_path} 경로에 서비스 계정 JSON 파일을 배치해주세요."
        )
    return service_account.Credentials.from_service_account_file(credentials_path)


@lru_cache(maxsize=1)
def _init_vertex() -> None:
    if not VERTEX_PROJECT_ID:
        raise ValueError("VERTEX_PROJECT_ID 환경 변수가 필요합니다.")
    credentials = _load_credentials()
    vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION, credentials=credentials)


def get_text_model(model_name: Optional[str] = None) -> GenerativeModel:
    """텍스트/멀티모달 생성 모델 반환"""
    _init_vertex()
    return GenerativeModel(model_name or DEFAULT_TEXT_MODEL)


def get_vision_model(model_name: Optional[str] = None) -> GenerativeModel:
    """비전 검증용 모델 반환"""
    _init_vertex()
    return GenerativeModel(model_name or DEFAULT_VISION_MODEL)

