"""
Network Utilities - IP detection, DNS checks, and connectivity
"""

import socket
import subprocess
from typing import List, Dict, Optional, Tuple
from rich.console import Console

console = Console()


def get_local_ips() -> List[Dict[str, str]]:
    """
    Get all local IP addresses.
    Returns list of dicts with interface, ip, and type (ipv4/ipv6).
    """
    ips = []

    try:
        # Use ip command on Linux
        result = subprocess.run(
            ["ip", "-o", "addr", "show"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                parts = line.split()
                if len(parts) >= 4:
                    interface = parts[1]
                    if "inet6" in line:
                        ip_type = "ipv6"
                        # Extract IPv6 address
                        for i, part in enumerate(parts):
                            if part == "inet6":
                                ip = parts[i + 1].split("/")[0]
                                if not ip.startswith("fe80"):  # Skip link-local
                                    ips.append({"interface": interface, "ip": ip, "type": ip_type})
                                break
                    elif "inet" in line:
                        ip_type = "ipv4"
                        for i, part in enumerate(parts):
                            if part == "inet":
                                ip = parts[i + 1].split("/")[0]
                                if not ip.startswith("127."):  # Skip loopback
                                    ips.append({"interface": interface, "ip": ip, "type": ip_type})
                                break
    except Exception:
        pass

    return ips


def get_public_ip() -> Optional[str]:
    """Get the server's public IP address."""
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]

    for service in services:
        try:
            import urllib.request
            with urllib.request.urlopen(service, timeout=5) as response:
                ip = response.read().decode().strip()
                # Validate it looks like an IP
                socket.inet_aton(ip)
                return ip
        except Exception:
            continue

    return None


def check_dns_resolution(domain: str) -> Dict[str, any]:
    """
    Check DNS resolution for a domain.
    Returns dict with a_records, aaaa_records, and resolved status.
    """
    result = {
        "domain": domain,
        "resolved": False,
        "a_records": [],
        "aaaa_records": [],
        "cname": None,
    }

    try:
        # A records (IPv4)
        try:
            a_records = socket.getaddrinfo(domain, None, socket.AF_INET)
            result["a_records"] = list(set([r[4][0] for r in a_records]))
            if result["a_records"]:
                result["resolved"] = True
        except socket.gaierror:
            pass

        # AAAA records (IPv6)
        try:
            aaaa_records = socket.getaddrinfo(domain, None, socket.AF_INET6)
            result["aaaa_records"] = list(set([r[4][0] for r in aaaa_records]))
            if result["aaaa_records"]:
                result["resolved"] = True
        except socket.gaierror:
            pass

    except Exception as e:
        result["error"] = str(e)

    return result


def verify_domain_points_to_server(domain: str) -> Tuple[bool, str]:
    """
    Verify that a domain's DNS points to this server.
    Returns (matches, message).
    """
    dns = check_dns_resolution(domain)

    if not dns["resolved"]:
        return False, f"Domain {domain} did not resolve"

    public_ip = get_public_ip()
    local_ips = [ip["ip"] for ip in get_local_ips()]

    all_server_ips = set(local_ips)
    if public_ip:
        all_server_ips.add(public_ip)

    domain_ips = set(dns["a_records"] + dns["aaaa_records"])

    matching = domain_ips & all_server_ips

    if matching:
        return True, f"Domain points to this server ({', '.join(matching)})"
    else:
        return False, f"Domain points to {', '.join(domain_ips)} but server IPs are {', '.join(all_server_ips)}"


def check_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is open and listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()


def get_listening_ports() -> List[Dict[str, any]]:
    """Get list of listening ports on the server."""
    ports = []

    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            for line in result.stdout.split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[3]
                    if ":" in local_addr:
                        ip, port = local_addr.rsplit(":", 1)
                        try:
                            ports.append({
                                "ip": ip.strip("[]"),
                                "port": int(port),
                                "raw": line,
                            })
                        except ValueError:
                            pass
    except Exception:
        pass

    return ports


def http_check(url: str, timeout: int = 5) -> Dict[str, any]:
    """
    Perform an HTTP health check on a URL.
    Returns status code, response time, and any errors.
    """
    import time

    result = {
        "url": url,
        "success": False,
        "status_code": None,
        "response_time_ms": None,
        "error": None,
    }

    try:
        import urllib.request
        import urllib.error

        start = time.time()

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ForgeCLI/1.0"}
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            result["status_code"] = response.getcode()
            result["success"] = 200 <= response.getcode() < 400

        result["response_time_ms"] = round((time.time() - start) * 1000)

    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = str(e)
        result["response_time_ms"] = round((time.time() - start) * 1000)
    except urllib.error.URLError as e:
        result["error"] = str(e.reason)
    except Exception as e:
        result["error"] = str(e)

    return result


def check_ssl_certificate(domain: str, port: int = 443) -> Dict[str, any]:
    """
    Check SSL certificate validity and expiration.
    """
    import ssl
    from datetime import datetime

    result = {
        "domain": domain,
        "valid": False,
        "issuer": None,
        "expires": None,
        "days_remaining": None,
        "error": None,
    }

    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Get expiration
                expires_str = cert.get("notAfter", "")
                if expires_str:
                    expires = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z")
                    result["expires"] = expires.isoformat()
                    result["days_remaining"] = (expires - datetime.now()).days
                    result["valid"] = result["days_remaining"] > 0

                # Get issuer
                issuer = cert.get("issuer", [])
                for item in issuer:
                    for key, value in item:
                        if key == "organizationName":
                            result["issuer"] = value
                            break

    except ssl.SSLCertVerificationError as e:
        result["error"] = f"Certificate verification failed: {e}"
    except Exception as e:
        result["error"] = str(e)

    return result
