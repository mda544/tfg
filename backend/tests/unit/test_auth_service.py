import pytest
from app.services.auth_service import _validate_credentials
from app.domain.exceptions import ValidationError


# Username

class TestUsernameValidation:

    def test_username_valido(self):
        """No debe lanzar excepción con un username correcto."""
        _validate_credentials("testUser01", "TestPass1!")

    def test_username_minimo_valido(self):
        """Exactamente 3 caracteres es el mínimo aceptado."""
        _validate_credentials("abc", "TestPass1!")

    def test_username_muy_corto(self):
        """Menos de 3 caracteres debe rechazarse."""
        with pytest.raises(ValidationError, match="al menos 3 caracteres"):
            _validate_credentials("ab", "TestPass1!")

    def test_username_un_caracter(self):
        with pytest.raises(ValidationError, match="al menos 3 caracteres"):
            _validate_credentials("a", "TestPass1!")

    def test_username_vacio(self):
        with pytest.raises(ValidationError, match="al menos 3 caracteres"):
            _validate_credentials("", "TestPass1!")

    def test_username_maximo_valido(self):
        """Exactamente 64 caracteres es el máximo aceptado."""
        username_64 = "a" * 64
        _validate_credentials(username_64, "TestPass1!")

    def test_username_demasiado_largo(self):
        """65 caracteres debe rechazarse."""
        username_65 = "a" * 65
        with pytest.raises(ValidationError, match="64 caracteres"):
            _validate_credentials(username_65, "TestPass1!")

    def test_username_con_espacio_rechazado(self):
        """Los espacios no están permitidos en el username."""
        with pytest.raises(ValidationError, match="letras, números"):
            _validate_credentials("test user", "TestPass1!")

    def test_username_con_caracter_especial_rechazado(self):
        with pytest.raises(ValidationError, match="letras, números"):
            _validate_credentials("test!user", "TestPass1!")

    def test_username_con_guion_permitido(self):
        """Guion y guion bajo están explícitamente permitidos."""
        _validate_credentials("test-user_01", "TestPass1!")

    def test_username_solo_numeros_permitido(self):
        _validate_credentials("12345", "TestPass1!")


# Password

class TestPasswordValidation:

    def test_password_valida(self):
        _validate_credentials("testUser01", "TestPass1!")

    def test_password_minima_valida(self):
        """Exactamente 8 caracteres con todos los requisitos."""
        _validate_credentials("testUser01", "Abcdefg1")

    def test_password_muy_corta(self):
        with pytest.raises(ValidationError, match="al menos 8 caracteres"):
            _validate_credentials("testUser01", "Abc123!")

    def test_password_sin_mayuscula(self):
        with pytest.raises(ValidationError, match="mayúscula"):
            _validate_credentials("testUser01", "testpass1")

    def test_password_sin_minuscula(self):
        with pytest.raises(ValidationError, match="minúscula"):
            _validate_credentials("testUser01", "TESTPASS1")

    def test_password_sin_numero(self):
        with pytest.raises(ValidationError, match="número"):
            _validate_credentials("testUser01", "TestPassword")

    def test_password_solo_mayusculas_y_numeros_falla_por_minuscula(self):
        """Verifica que las tres reglas (mayús/minús/número) se comprueban
        independientemente, no basta con cumplir dos de tres."""
        with pytest.raises(ValidationError, match="minúscula"):
            _validate_credentials("testUser01", "TESTPASS123")


# Orden de validación

class TestValidationOrder:

    def test_username_se_valida_antes_que_password(self):
        """Si ambos son inválidos, el error de username aparece primero
        (orden de las comprobaciones en _validate_credentials)."""
        with pytest.raises(ValidationError, match="nombre de usuario"):
            _validate_credentials("ab", "short")