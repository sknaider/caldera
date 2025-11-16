"""
Configuration Security Module
Handles secure loading of configuration with environment variable substitution
and validation of production security requirements.
"""
import os
import re
import logging
from typing import Any, Dict, Optional, Set
from pathlib import Path

log = logging.getLogger('config_security')


class ConfigurationError(Exception):
    """Raised when configuration is invalid or insecure"""
    pass


# List of insecure default values that must not be used in production
INSECURE_DEFAULTS: Set[str] = {
    'ADMIN123',
    'BLUEADMIN123',
    'API_KEY',
    'SLACK_TOKEN',
    'SLACK_BOT_ID',
    'SLACK_CHANNEL_ID',
    'REPLACE_WITH_KEY_FILE_PATH',
    'REPLACE_WITH_KEY_FILE_PASSPHRASE',
    's4ndc4t!',
    'caldera',
    'REPLACE_WITH_RANDOM_VALUE',
    'admin',  # as password
}


def is_dev_mode() -> bool:
    """Check if running in development mode"""
    return os.getenv('CALDERA_DEV_MODE', 'false').lower() in ('true', '1', 'yes')


def get_environment() -> str:
    """Get current environment (development, staging, production)"""
    return os.getenv('CALDERA_ENVIRONMENT', 'development').lower()


def substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute environment variables in configuration values.

    Supports:
    - ${VAR_NAME} - Required variable, raises error if not set
    - ${VAR_NAME:-default} - Optional with default value

    Args:
        value: Configuration value (can be str, dict, list, or primitive)

    Returns:
        Value with environment variables substituted

    Raises:
        ConfigurationError: If required environment variable is not set
    """
    if isinstance(value, str):
        # Pattern: ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([^:}]+)(?::(-)?([^}]+))?\}'

        def replacer(match):
            var_name = match.group(1)
            has_default = match.group(2) is not None
            default_value = match.group(3) if has_default else None

            env_value = os.getenv(var_name)

            if env_value is None:
                if has_default:
                    return default_value if default_value else ''
                else:
                    raise ConfigurationError(
                        f"Required environment variable '{var_name}' is not set. "
                        f"Please set it in your environment or .env file."
                    )

            return env_value

        try:
            return re.sub(pattern, replacer, value)
        except ConfigurationError:
            raise

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]
    else:
        return value


def validate_production_config(config: Dict[str, Any], path_prefix: str = '') -> None:
    """
    Validate that production configuration doesn't contain insecure defaults.

    Args:
        config: Configuration dictionary to validate
        path_prefix: Current path in config tree (for error messages)

    Raises:
        ConfigurationError: If insecure values are found in production mode
    """
    if is_dev_mode():
        log.warning("Running in DEV_MODE - skipping security validation")
        return

    env = get_environment()
    if env == 'development':
        return

    for key, value in config.items():
        current_path = f"{path_prefix}.{key}" if path_prefix else key

        if isinstance(value, dict):
            validate_production_config(value, current_path)
        elif isinstance(value, str):
            if value in INSECURE_DEFAULTS:
                raise ConfigurationError(
                    f"Production deployment detected with insecure default value "
                    f"at '{current_path}': '{value}'\n"
                    f"Environment: {env}\n"
                    f"Please set proper environment variables. See .env.example for reference."
                )


def validate_encryption_keys(config: Dict[str, Any]) -> None:
    """
    Validate that encryption keys meet minimum security requirements.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigurationError: If encryption keys are weak or missing
    """
    if is_dev_mode():
        return

    # Check crypt_salt
    crypt_salt = config.get('crypt_salt', '')
    if len(crypt_salt) < 32:
        raise ConfigurationError(
            "crypt_salt must be at least 32 characters long. "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Check encryption_key
    encryption_key = config.get('encryption_key', '')
    if len(encryption_key) < 32:
        raise ConfigurationError(
            "encryption_key must be at least 32 characters long. "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )


def validate_user_passwords(config: Dict[str, Any]) -> None:
    """
    Validate that user passwords meet minimum requirements.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigurationError: If passwords are weak
    """
    if is_dev_mode():
        return

    users = config.get('users', {})
    for group, user_dict in users.items():
        for username, password in user_dict.items():
            if len(password) < 8:
                raise ConfigurationError(
                    f"Password for {group}/{username} must be at least 8 characters long"
                )
            if password in INSECURE_DEFAULTS:
                raise ConfigurationError(
                    f"Password for {group}/{username} is using insecure default value"
                )


def load_secure_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load and validate configuration with security checks.

    This function:
    1. Substitutes environment variables
    2. Validates no insecure defaults in production
    3. Validates encryption keys
    4. Validates user passwords

    Args:
        config: Raw configuration dictionary

    Returns:
        Processed and validated configuration

    Raises:
        ConfigurationError: If configuration is invalid or insecure
    """
    log.info(f"Loading configuration (environment: {get_environment()}, dev_mode: {is_dev_mode()})")

    # Step 1: Substitute environment variables
    try:
        config = substitute_env_vars(config)
    except ConfigurationError as e:
        log.error(f"Configuration error: {e}")
        raise

    # Step 2: Validate security
    try:
        validate_production_config(config)
        validate_encryption_keys(config)
        validate_user_passwords(config)
    except ConfigurationError as e:
        log.error(f"Security validation failed: {e}")
        raise

    log.info("Configuration loaded and validated successfully")
    return config


def generate_secure_key(length: int = 64) -> str:
    """
    Generate a secure random key.

    Args:
        length: Length of hex string (actual bytes will be length/2)

    Returns:
        Hex-encoded random key
    """
    import secrets
    return secrets.token_hex(length // 2)


def load_env_file(env_file: Path = Path('.env')) -> None:
    """
    Load environment variables from .env file if it exists.

    Args:
        env_file: Path to .env file
    """
    if not env_file.exists():
        return

    log.info(f"Loading environment from {env_file}")

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Don't override existing environment variables
                if key not in os.environ:
                    os.environ[key] = value


if __name__ == '__main__':
    # Quick test/demo
    print("Generating secure keys:")
    print(f"CALDERA_CRYPT_SALT={generate_secure_key(64)}")
    print(f"CALDERA_ENCRYPTION_KEY={generate_secure_key(64)}")
    print(f"CALDERA_API_KEY_RED={generate_secure_key(32)}")
    print(f"CALDERA_API_KEY_BLUE={generate_secure_key(32)}")
