import os
import re
import ipaddress
import socket
import urllib.request
import urllib.parse
import urllib.error
import ssl

try:
    import certifi
    SSL_CA_FILE = certifi.where()
except ImportError:
    SSL_CA_FILE = None


def _validate_safe_url(url: str) -> tuple[bool, str]:
    """Valide qu'une URL est sécurisée et ne cible pas des ressources internes (anti-SSRF)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Protocole non autorisé : {parsed.scheme} (seuls http et https sont acceptés)"

        hostname = parsed.hostname
        if not hostname:
            return False, "Nom d'hôte manquant"

        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False, f"Accès refusé aux adresses de bouclage ({hostname}) (SSRF)"

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip = ipaddress.ip_address(ip_str)
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                ):
                    return False, f"Accès refusé aux adresses IP privées/internes ({ip_str}) (SSRF)"
        except socket.gaierror:
            pass

        return True, ""
    except Exception as e:
        return False, f"URL invalide : {e}"


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        is_safe, error_msg = _validate_safe_url(newurl)
        if not is_safe:
            raise urllib.error.HTTPError(newurl, code, f"Redirection bloquée (SSRF): {error_msg}", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def extract(url: str) -> dict:
    """Extract content from a public URL with SSRF protection and safe redirects"""
    is_safe, error_msg = _validate_safe_url(url)
    if not is_safe:
        return {"error": f"[SÉCURITÉ] {error_msg}", "url": url}

    try:
        handlers = [SafeRedirectHandler]
        if SSL_CA_FILE:
            ctx = ssl.create_default_context(cafile=SSL_CA_FILE)
            handlers.append(urllib.request.HTTPSHandler(context=ctx))

        opener = urllib.request.build_opener(*handlers)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with opener.open(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        # Remove script and style tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

        # Extract text content
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE)
        title = title_match.group(1) if title_match else "No title"

        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html, re.IGNORECASE
        )
        description = desc_match.group(1) if desc_match else ""

        return {
            "title": title,
            "description": description,
            "content": text[:5000],  # Limit content length
            "url": url,
            "length": len(text),
        }
    except Exception as e:
        return {"error": str(e), "url": url}
