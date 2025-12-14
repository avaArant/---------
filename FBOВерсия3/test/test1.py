# test_validation.py
import logging
from src.middleware.auth import AuthMiddleware


def test_auth_validation():
    """Тест валидации учетных данных"""
    logging.basicConfig(level=logging.INFO)

    test_cases = [
        # (client_id, api_key, expected_result, description)
        ("123456", "valid_api_key_12345", True, "Valid credentials"),
        ("2115535", "53", True, "Valid (your case)"),
        ("", "api_key", False, "Empty client_id"),
        ("123456", "", False, "Empty api_key"),
        ("not_a_number", "api_key", False, "Client-Id not a number"),
        ("-123", "api_key", False, "Negative client_id"),
        ("0", "api_key", False, "Zero client_id"),
        ("123.456", "api_key", False, "Float client_id"),
    ]

    print("Testing AuthMiddleware.validate_credentials()")
    print("=" * 60)

    for client_id, api_key, expected, description in test_cases:
        credentials = {"client_id": client_id, "api_key": api_key}
        result = AuthMiddleware.validate_credentials(credentials)

        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {description}")
        print(f"  Client-Id: '{client_id}', Api-Key: '{api_key[:10]}...'")
        print(f"  Expected: {expected}, Got: {result}")
        print()


if __name__ == "__main__":
    test_auth_validation()