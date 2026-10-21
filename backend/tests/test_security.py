from cryptography.fernet import Fernet

from app.core.security import TokenCipher, hash_oauth_state


def test_token_cipher_round_trip_and_does_not_store_plaintext() -> None:
    cipher = TokenCipher(Fernet.generate_key().decode())
    encrypted = cipher.encrypt("secret-access-token")

    assert encrypted != "secret-access-token"
    assert cipher.decrypt(encrypted) == "secret-access-token"


def test_oauth_state_is_hashed_deterministically() -> None:
    assert hash_oauth_state("state") == hash_oauth_state("state")
    assert hash_oauth_state("state") != "state"
