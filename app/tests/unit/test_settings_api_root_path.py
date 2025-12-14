from config.config import Settings


def test_api_root_path_strips_wrapping_quotes():
    settings = Settings(API_ROOT_PATH='"/api"')
    assert settings.API_ROOT_PATH == "/api"


def test_api_root_path_strips_trailing_slash():
    settings = Settings(API_ROOT_PATH="/api/")
    assert settings.API_ROOT_PATH == "/api"


def test_api_root_path_adds_leading_slash():
    settings = Settings(API_ROOT_PATH="api")
    assert settings.API_ROOT_PATH == "/api"


def test_api_root_path_allows_empty():
    settings = Settings(API_ROOT_PATH="")
    assert settings.API_ROOT_PATH == ""

