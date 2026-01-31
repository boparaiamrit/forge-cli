"""
Server Hardening Module — Security Best Practices
Based on CIS Benchmarks and Laravel Forge security standards
"""

from utils.shell import run_command
from utils.ui import print_success, print_error, print_info, print_warning

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY HARDENING SCRIPTS
# ═══════════════════════════════════════════════════════════════════════════════

def harden_ssh() -> bool:
    """
    Harden SSH configuration.
    - Disable root login
    - Disable password authentication (key-only)
    - Change default port (optional)
    - Limit authentication attempts
    """
    print_info("Hardening SSH configuration...")

    sshd_config = "/etc/ssh/sshd_config"

    commands = [
        # Disable root login
        f'sed -i "s/#PermitRootLogin.*/PermitRootLogin no/" {sshd_config}',
        f'sed -i "s/PermitRootLogin.*/PermitRootLogin no/" {sshd_config}',

        # Disable password authentication
        f'sed -i "s/#PasswordAuthentication.*/PasswordAuthentication no/" {sshd_config}',
        f'sed -i "s/PasswordAuthentication.*/PasswordAuthentication no/" {sshd_config}',

        # Disable empty passwords
        f'sed -i "s/#PermitEmptyPasswords.*/PermitEmptyPasswords no/" {sshd_config}',

        # Limit authentication attempts
        f'sed -i "s/#MaxAuthTries.*/MaxAuthTries 3/" {sshd_config}',

        # Disable X11 forwarding
        f'sed -i "s/#X11Forwarding.*/X11Forwarding no/" {sshd_config}',
        f'sed -i "s/X11Forwarding.*/X11Forwarding no/" {sshd_config}',

        # Set login grace time
        f'sed -i "s/#LoginGraceTime.*/LoginGraceTime 60/" {sshd_config}',

        # Use only SSH protocol 2
        f'echo "Protocol 2" >> {sshd_config}',

        # Restart SSH
        "systemctl restart sshd",
    ]

    for cmd in commands:
        code, _, stderr = run_command(f"sudo {cmd}", check=False)
        if code != 0 and "No such file" not in stderr:
            print_error(f"SSH hardening failed: {stderr}")
            return False

    print_success("SSH hardened successfully!")
    return True


def setup_firewall() -> bool:
    """
    Configure UFW firewall with sensible defaults.
    - Allow SSH (22)
    - Allow HTTP (80)
    - Allow HTTPS (443)
    - Deny all other incoming
    - Allow all outgoing
    """
    print_info("Configuring UFW firewall...")

    commands = [
        # Reset to defaults
        "ufw --force reset",

        # Set default policies
        "ufw default deny incoming",
        "ufw default allow outgoing",

        # Allow SSH
        "ufw allow OpenSSH",
        "ufw allow 22/tcp",

        # Allow HTTP/HTTPS
        "ufw allow 80/tcp",
        "ufw allow 443/tcp",

        # Enable firewall
        "ufw --force enable",
    ]

    for cmd in commands:
        code, _, stderr = run_command(f"sudo {cmd}", check=False)
        if code != 0:
            print_error(f"Firewall setup failed: {stderr}")
            return False

    print_success("UFW firewall configured!")
    return True


def setup_fail2ban() -> bool:
    """
    Install and configure Fail2Ban for brute-force protection.
    """
    print_info("Setting up Fail2Ban...")

    # Install fail2ban
    code, _, stderr = run_command("sudo apt-get install -y fail2ban", check=False)
    if code != 0:
        print_error(f"Failed to install fail2ban: {stderr}")
        return False

    # Create local jail configuration
    jail_local = """
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
"""

    # Write jail configuration
    with open("/tmp/jail.local", "w") as f:
        f.write(jail_local)

    run_command("sudo mv /tmp/jail.local /etc/fail2ban/jail.local", check=False)
    run_command("sudo systemctl enable fail2ban", check=False)
    run_command("sudo systemctl restart fail2ban", check=False)

    print_success("Fail2Ban configured!")
    return True


def disable_unused_services() -> bool:
    """
    Disable unnecessary services to reduce attack surface.
    """
    print_info("Disabling unused services...")

    services_to_disable = [
        "cups",           # Printing
        "avahi-daemon",   # mDNS
        "bluetooth",      # Bluetooth
        "ModemManager",   # Modem
    ]

    for service in services_to_disable:
        run_command(f"sudo systemctl stop {service}", check=False)
        run_command(f"sudo systemctl disable {service}", check=False)

    print_success("Unused services disabled!")
    return True


def setup_automatic_updates() -> bool:
    """
    Configure unattended-upgrades for automatic security updates.
    """
    print_info("Configuring automatic security updates...")

    commands = [
        "apt-get install -y unattended-upgrades apt-listchanges",
        'echo unattended-upgrades unattended-upgrades/enable_auto_updates boolean true | debconf-set-selections',
        "dpkg-reconfigure -f noninteractive unattended-upgrades",
    ]

    for cmd in commands:
        code, _, stderr = run_command(f"sudo {cmd}", check=False)
        if code != 0:
            print_warning(f"Auto-updates setup warning: {stderr}")

    print_success("Automatic security updates configured!")
    return True


def secure_shared_memory() -> bool:
    """
    Secure shared memory to prevent certain attacks.
    """
    print_info("Securing shared memory...")

    fstab_entry = "tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0"

    # Check if already configured
    code, stdout, _ = run_command("grep '/run/shm' /etc/fstab", check=False)
    if code != 0:
        run_command(f'echo "{fstab_entry}" | sudo tee -a /etc/fstab', check=False)

    print_success("Shared memory secured!")
    return True


def setup_sysctl_hardening() -> bool:
    """
    Apply kernel-level security hardening via sysctl.
    """
    print_info("Applying kernel hardening...")

    sysctl_config = """
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcast requests
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Block SYN attacks
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Disable IPv6 if not needed
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# Restrict core dumps
fs.suid_dumpable = 0

# Randomize virtual address space
kernel.randomize_va_space = 2
"""

    with open("/tmp/99-forge-hardening.conf", "w") as f:
        f.write(sysctl_config)

    run_command("sudo mv /tmp/99-forge-hardening.conf /etc/sysctl.d/99-forge-hardening.conf", check=False)
    run_command("sudo sysctl --system", check=False)

    print_success("Kernel hardening applied!")
    return True


def setup_logwatch() -> bool:
    """
    Install and configure Logwatch for log monitoring.
    """
    print_info("Setting up Logwatch...")

    code, _, stderr = run_command("sudo apt-get install -y logwatch", check=False)
    if code != 0:
        print_warning(f"Logwatch installation warning: {stderr}")
        return False

    print_success("Logwatch installed!")
    return True


def create_deploy_user(username: str = "forge") -> bool:
    """
    Create a non-root deploy user with sudo access.
    """
    print_info(f"Creating deploy user '{username}'...")

    commands = [
        f"useradd -m -s /bin/bash {username}",
        f"usermod -aG sudo {username}",
        f"usermod -aG www-data {username}",
        f'echo "{username} ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/{username}',
        f"chmod 440 /etc/sudoers.d/{username}",
        f"mkdir -p /home/{username}/.ssh",
        f"chmod 700 /home/{username}/.ssh",
        f"touch /home/{username}/.ssh/authorized_keys",
        f"chmod 600 /home/{username}/.ssh/authorized_keys",
        f"chown -R {username}:{username} /home/{username}/.ssh",
    ]

    for cmd in commands:
        code, _, stderr = run_command(f"sudo {cmd}", check=False)
        if code != 0 and "already exists" not in stderr:
            print_warning(f"User setup warning: {stderr}")

    print_success(f"Deploy user '{username}' created!")
    return True


def run_full_hardening():
    """
    Run all security hardening steps.
    """
    steps = [
        ("Creating deploy user", lambda: create_deploy_user("forge")),
        ("Hardening SSH", harden_ssh),
        ("Setting up firewall", setup_firewall),
        ("Installing Fail2Ban", setup_fail2ban),
        ("Disabling unused services", disable_unused_services),
        ("Configuring automatic updates", setup_automatic_updates),
        ("Securing shared memory", secure_shared_memory),
        ("Applying kernel hardening", setup_sysctl_hardening),
        ("Setting up Logwatch", setup_logwatch),
    ]

    results = []
    for name, func in steps:
        print_info(f"\n{'='*60}")
        print_info(f"Step: {name}")
        print_info(f"{'='*60}")
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            print_error(f"Step failed: {e}")
            results.append((name, False))

    return results
