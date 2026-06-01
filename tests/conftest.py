
import pytest
from fastapi.testclient import TestClient
from main.api import app

@pytest.fixture
def client():
    return TestClient(app)
