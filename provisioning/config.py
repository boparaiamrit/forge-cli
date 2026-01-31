"""
Server Provisioning Scripts — Based on Laravel Settler
Complete server setup from scratch with security hardening
"""

# PHP Versions and their extensions
PHP_VERSIONS = ["8.1", "8.2", "8.3"]

PHP_EXTENSIONS = [
    "bcmath", "bz2", "cgi", "cli", "common", "curl", "dba", "dev",
    "enchant", "fpm", "gd", "gmp", "imap", "intl", "ldap",
    "mbstring", "mysql", "odbc", "opcache", "pgsql", "phpdbg", "pspell",
    "readline", "snmp", "soap", "sqlite3", "tidy", "xml", "xsl",
    "zip", "imagick", "memcached", "redis", "xdebug"
]

# PHP Configuration defaults
PHP_CLI_CONFIG = {
    "error_reporting": "E_ALL",
    "display_errors": "On",
    "memory_limit": "512M",
    "date.timezone": "UTC",
}

PHP_FPM_CONFIG = {
    "error_reporting": "E_ALL",
    "display_errors": "On",
    "cgi.fix_pathinfo": "0",
    "memory_limit": "512M",
    "upload_max_filesize": "100M",
    "post_max_size": "100M",
    "date.timezone": "UTC",
}

# Xdebug configuration
XDEBUG_CONFIG = {
    "xdebug.mode": "debug",
    "xdebug.discover_client_host": "true",
    "xdebug.client_port": "9003",
    "xdebug.max_nesting_level": "512",
}

# Node.js LTS versions
NODE_VERSIONS = ["18", "20", "21", "22"]
NODE_DEFAULT = "20"

# Global NPM packages
NPM_GLOBAL_PACKAGES = ["npm", "yarn", "pm2", "gulp-cli", "grunt-cli"]

# Database defaults
MYSQL_DEFAULT_PASSWORD = "secret"
POSTGRES_DEFAULT_PASSWORD = "secret"

# Services to enable
SERVICES_TO_ENABLE = [
    "nginx",
    "redis-server",
    "supervisor",
]


def get_php_install_command(version: str) -> str:
    """Generate apt install command for a PHP version."""
    packages = [f"php{version}-{ext}" for ext in PHP_EXTENSIONS]
    return f"apt-get install -y --allow-change-held-packages {' '.join(packages)}"


def get_php_config_commands(version: str, config_type: str = "cli") -> list[str]:
    """Generate sed commands to configure php.ini."""
    config = PHP_CLI_CONFIG if config_type == "cli" else PHP_FPM_CONFIG
    ini_path = f"/etc/php/{version}/{config_type}/php.ini"

    commands = []
    for key, value in config.items():
        # Handle both commented and uncommented settings
        if key.startswith(";"):
            key = key[1:]
            commands.append(f'sed -i "s/;{key}.*/{key} = {value}/" {ini_path}')
        else:
            commands.append(f'sed -i "s/{key} = .*/{key} = {value}/" {ini_path}')

    return commands


def get_xdebug_config_commands(version: str) -> list[str]:
    """Generate commands to configure Xdebug."""
    ini_path = f"/etc/php/{version}/mods-available/xdebug.ini"
    return [f'echo "{key} = {value}" >> {ini_path}' for key, value in XDEBUG_CONFIG.items()]


def get_fpm_pool_config_commands(version: str, user: str = "www-data") -> list[str]:
    """Generate commands to configure PHP-FPM pool."""
    pool_path = f"/etc/php/{version}/fpm/pool.d/www.conf"
    return [
        f'sed -i "s/user = www-data/user = {user}/" {pool_path}',
        f'sed -i "s/group = www-data/group = {user}/" {pool_path}',
        f'sed -i "s/listen\\.owner.*/listen.owner = {user}/" {pool_path}',
        f'sed -i "s/listen\\.group.*/listen.group = {user}/" {pool_path}',
        f'sed -i "s/;listen\\.mode.*/listen.mode = 0666/" {pool_path}',
    ]
