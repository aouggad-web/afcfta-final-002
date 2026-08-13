import pytest
from pydantic import ValidationError

from routes.user_auth import LoginPayload, RegisterPayload


def test_register_payload_normalizes_name_and_email():
    payload = RegisterPayload(
        name="  Alice   Test  ",
        email="  ALICE@EXAMPLE.COM  ",
        password="SecurePass123",
    )

    assert payload.name == "Alice Test"
    assert str(payload.email) == "alice@example.com"


def test_register_payload_rejects_blank_name():
    with pytest.raises(ValidationError):
        RegisterPayload(
            name="   ",
            email="alice@example.com",
            password="SecurePass123",
        )


def test_login_payload_normalizes_email():
    payload = LoginPayload(email="  USER@EXAMPLE.COM  ", password="SecurePass123")

    assert str(payload.email) == "user@example.com"
