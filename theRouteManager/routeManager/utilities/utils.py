import uuid
import string
import secrets


def generate_username(email: str) -> str:
    """Generate a username from an email address."""
    return email.split("@")[0]


def generate_ssn() -> str:
    """Generate a unique SSN."""
    return str(uuid.uuid4().int)[:9]


def generate_password() -> str:
    """Generate a random 8-digit password."""
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for i in range(8))
    return password


def process_json(data, fields: list[str]):
    return {field: data.get(field) for field in fields}
