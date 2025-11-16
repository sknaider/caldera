"""
Security tests for configuration validation
"""
import pytest
import os
from app.utility.config_security import (
    substitute_env_vars,
    validate_production_config,
    validate_encryption_keys,
    validate_user_passwords,
    ConfigurationError,
    INSECURE_DEFAULTS
)


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution in config"""

    def test_simple_substitution(self):
        """Test basic ${VAR} substitution"""
        os.environ['TEST_VAR'] = 'test_value'
        result = substitute_env_vars('${TEST_VAR}')
        assert result == 'test_value'
        del os.environ['TEST_VAR']

    def test_substitution_with_default(self):
        """Test ${VAR:-default} substitution with default value"""
        result = substitute_env_vars('${NONEXISTENT_VAR:-default_value}')
        assert result == 'default_value'

    def test_substitution_missing_required_var(self):
        """Test that missing required var raises error"""
        with pytest.raises(ConfigurationError):
            substitute_env_vars('${NONEXISTENT_REQUIRED_VAR}')

    def test_nested_dict_substitution(self):
        """Test substitution in nested dictionaries"""
        os.environ['API_KEY'] = 'secret123'
        config = {
            'level1': {
                'level2': {
                    'api_key': '${API_KEY}'
                }
            }
        }
        result = substitute_env_vars(config)
        assert result['level1']['level2']['api_key'] == 'secret123'
        del os.environ['API_KEY']

    def test_list_substitution(self):
        """Test substitution in lists"""
        os.environ['ITEM1'] = 'value1'
        config = ['${ITEM1}', 'static_value']
        result = substitute_env_vars(config)
        assert result == ['value1', 'static_value']
        del os.environ['ITEM1']


class TestProductionConfigValidation:
    """Test production configuration validation"""

    def test_detects_insecure_api_key(self):
        """Test detection of default API keys"""
        config = {'api_key_red': 'ADMIN123'}
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError) as exc:
            validate_production_config(config)

        assert 'insecure default value' in str(exc.value).lower()
        assert 'api_key_red' in str(exc.value)

        # Cleanup
        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_detects_insecure_password(self):
        """Test detection of default passwords"""
        config = {'app': {'contact': {'ftp': {'pword': 'caldera'}}}}
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError):
            validate_production_config(config)

        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_allows_insecure_in_dev_mode(self):
        """Test that dev mode allows insecure defaults"""
        config = {'api_key_red': 'ADMIN123'}
        os.environ['CALDERA_DEV_MODE'] = 'true'

        # Should not raise
        validate_production_config(config)

        del os.environ['CALDERA_DEV_MODE']

    def test_allows_secure_values_in_production(self):
        """Test that secure values pass in production"""
        config = {'api_key_red': 'randomly_generated_secure_key_123456'}
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        # Should not raise
        validate_production_config(config)

        os.environ.pop('CALDERA_ENVIRONMENT', None)


class TestEncryptionKeyValidation:
    """Test encryption key validation"""

    def test_rejects_short_crypt_salt(self):
        """Test rejection of short crypt_salt"""
        config = {'crypt_salt': 'tooshort', 'encryption_key': 'a' * 32}
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError) as exc:
            validate_encryption_keys(config)

        assert 'at least 32 characters' in str(exc.value)

        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_rejects_short_encryption_key(self):
        """Test rejection of short encryption_key"""
        config = {'crypt_salt': 'a' * 32, 'encryption_key': 'tooshort'}
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError) as exc:
            validate_encryption_keys(config)

        assert 'at least 32 characters' in str(exc.value)

        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_accepts_strong_keys(self):
        """Test acceptance of strong encryption keys"""
        config = {
            'crypt_salt': 'a' * 64,
            'encryption_key': 'b' * 64
        }
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        # Should not raise
        validate_encryption_keys(config)

        os.environ.pop('CALDERA_ENVIRONMENT', None)


class TestUserPasswordValidation:
    """Test user password validation"""

    def test_rejects_short_passwords(self):
        """Test rejection of passwords < 8 chars"""
        config = {
            'users': {
                'red': {
                    'admin': 'short'
                }
            }
        }
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError) as exc:
            validate_user_passwords(config)

        assert 'at least 8 characters' in str(exc.value).lower()

        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_rejects_default_passwords(self):
        """Test rejection of default password values"""
        config = {
            'users': {
                'red': {
                    'admin': 'admin'
                }
            }
        }
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        with pytest.raises(ConfigurationError) as exc:
            validate_user_passwords(config)

        assert 'insecure default' in str(exc.value).lower()

        os.environ.pop('CALDERA_ENVIRONMENT', None)

    def test_accepts_strong_passwords(self):
        """Test acceptance of strong passwords"""
        config = {
            'users': {
                'red': {
                    'admin': 'StrongP@ssw0rd123!'
                },
                'blue': {
                    'blue': 'An0therStr0ngP@ss'
                }
            }
        }
        os.environ['CALDERA_ENVIRONMENT'] = 'production'
        os.environ.pop('CALDERA_DEV_MODE', None)

        # Should not raise
        validate_user_passwords(config)

        os.environ.pop('CALDERA_ENVIRONMENT', None)


class TestInsecureDefaults:
    """Test the INSECURE_DEFAULTS set is comprehensive"""

    def test_contains_common_insecure_values(self):
        """Verify INSECURE_DEFAULTS contains common bad values"""
        assert 'ADMIN123' in INSECURE_DEFAULTS
        assert 'admin' in INSECURE_DEFAULTS
        assert 'REPLACE_WITH_RANDOM_VALUE' in INSECURE_DEFAULTS
        assert 'API_KEY' in INSECURE_DEFAULTS
