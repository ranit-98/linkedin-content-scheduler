import os

import pytest
from cryptography.fernet import Fernet

# Configuration must exist before application modules create their engines.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["TOKEN_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["LINKEDIN_MOCK_MODE"] = "true"


@pytest.fixture(autouse=True)
def clean_database():  # type: ignore[no-untyped-def]
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
