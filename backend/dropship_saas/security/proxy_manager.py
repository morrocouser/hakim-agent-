"""Proxy manager — rotation and blacklisting."""

from __future__ import annotations
import logging
import random
import time
from typing import Optional, List, Set

logger = logging.getLogger("dropship_saas.security.proxy")


class ProxyManager:
    """Manages proxy pool with rotation and automatic blacklisting."""
    
    def __init__(self):
        self._proxies: List[str] = []
        self._blacklisted: Set[str] = set()
        self._blacklist_timestamps: dict = {}
        self._current_index = 0
        self._blacklist_timeout = 300  # 5 minutes
    
    def add_proxy(self, proxy_url: str) -> None:
        """Add a proxy to the pool."""
        if proxy_url not in self._proxies:
            self._proxies.append(proxy_url)
    
    def add_proxies(self, proxy_urls: List[str]) -> None:
        """Add multiple proxies."""
        for proxy in proxy_urls:
            self.add_proxy(proxy)
    
    def get_active_proxy(self) -> Optional[str]:
        """Get next available (non-blacklisted) proxy."""
        if not self._proxies:
            return None
        
        # Clean expired blacklist entries
        self._clean_blacklist()
        
        # Find first non-blacklisted proxy
        available = [p for p in self._proxies if p not in self._blacklisted]
        if not available:
            return None
        
        proxy = available[self._current_index % len(available)]
        self._current_index += 1
        return proxy
    
    def blacklist_proxy(self, proxy_url: str) -> None:
        """Quarantine a proxy that returned 403/429/captcha."""
        logger.warning(f"Blacklisting proxy: {proxy_url}")
        self._blacklisted.add(proxy_url)
        self._blacklist_timestamps[proxy_url] = time.time()
    
    def is_blacklisted(self, proxy_url: str) -> bool:
        """Check if a proxy is currently blacklisted."""
        self._clean_blacklist()
        return proxy_url in self._blacklisted
    
    def _clean_blacklist(self) -> None:
        """Remove expired blacklist entries."""
        now = time.time()
        expired = [
            proxy for proxy, timestamp in self._blacklist_timestamps.items()
            if now - timestamp > self._blacklist_timeout
        ]
        for proxy in expired:
            self._blacklisted.discard(proxy)
            self._blacklist_timestamps.pop(proxy, None)
            logger.info(f"Proxy removed from blacklist: {proxy}")
    
    def get_status(self) -> dict:
        """Get proxy pool status."""
        self._clean_blacklist()
        return {
            "total": len(self._proxies),
            "active": len([p for p in self._proxies if p not in self._blacklisted]),
            "blacklisted": len(self._blacklisted),
        }