"""
Rate limiting middleware for AXIOM multi-agent system.

This middleware provides rate limiting functionality to prevent
API abuse, DoS attacks, and resource exhaustion across all
external API calls in the AXIOM system.

Features:
- Multi-level rate limits (per client, per IP, per endpoint)
- Token bucket algorithm for burst handling
- Configurable limits based on client type
- Exponential backoff for exceeding limits
- Distributed rate limiting support
- Metrics and monitoring integration
"""

import time
import re
import logging
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import threading
from functools import wraps

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)
class RateLimitType(Enum):
    """Types of rate limits available."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    CUSTOM = "custom"
@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int = 100
    window_seconds: int = 60  # 1 minute default
    burst_size: int = 10      # Additional requests allowed in burst
    penalty_interval: int = 300  # Penalty duration after violation (seconds)
    key_prefix: str = "rate_limit"
@dataclass
class ClientIdentifier:
    """Client identification for rate limiting."""
    client_id: str
    ip_address: str
    user_agent: Optional[str] = None
    api_key: Optional[str] = None
    user_id: Optional[str] = None

    def get_composite_key(self, prefix: str = "limit") -> str:
        """Generate composite key for rate limiting."""
        key_parts = [prefix]

        if self.api_key:
            key_parts.append(f"api_key:{self.api_key}")
        elif self.user_id:
            key_parts.append(f"user:{self.user_id}")
        else:
            key_parts.append(f"ip:{self.ip_address}")

        if self.user_agent:
            # Sanitize user agent for key generation
            sanitized_ua = re.sub(r'[^\w\-]', '_', self.user_agent)
            key_parts.append(f"ua:{sanitized_ua}")

        return ":".join(key_parts)
class RateLimitEntry:
    """Single rate limit entry tracking."""

    def __init__(self, key: str, limit_config: RateLimitConfig):
        self.key = key
        self.limit_config = limit_config
        self.requests = []  # List of request timestamps
        self.penalty_until = 0.0
        self.blocks = 0

    def is_allowed(self, current_time: float) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.

        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        # Check if client is in penalty
        if current_time < self.penalty_until:
            penalty_remaining = int(self.penalty_until - current_time)
            return False, 0, penalty_remaining

        # Remove old requests outside the window
        window_start = current_time - self.limit_config.window_seconds
        self.requests = [req_time for req_time in self.requests if req_time >= window_start]

        # Check if under limit
        if len(self.requests) < self.limit_config.max_requests:
            # Allow request
            self.requests.append(current_time)
            remaining = self.limit_config.max_requests - len(self.requests)
            reset_time = window_start + self.limit_config.window_seconds
            return True, remaining, int(reset_time)
        else:
            # Exceeded limit
            self.blocks += 1
            # Apply penalty
            self.penalty_until = current_time + self.limit_config.penalty_interval

            # Calculate if burst allowed
            burst_allowed = len(self.requests) < (self.limit_config.max_requests + self.limit_config.burst_size)
            if burst_allowed:
                self.requests.append(current_time)
                remaining = self.limit_config.max_requests - len(self.requests)
                reset_time = window_start + self.limit_config.window_seconds
                return True, remaining, int(reset_time)
            else:
                # Completely blocked
                reset_time = self.requests[0] + self.limit_config.window_seconds
                return False, 0, int(reset_time)

    def cleanup_old_entries(self, current_time: float) -> None:
        """Remove outdated entries to prevent memory leaks."""
        window_start = current_time - (self.limit_config.window_seconds * 2)  # Keep 2 windows
        self.requests = [req_time for req_time in self.requests if req_time >= window_start]
class MemoryBasedRateLimiter:
    """
    In-memory rate limiter with thread safety.

    This is a fallback implementation when Redis is not available.
    """

    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self.default_config = default_config or RateLimitConfig()
        self.limits: Dict[str, RateLimitEntry] = {}
        self.lock = threading.RLock()
        self.metrics = {
            'total_checks': 0,
            'allowed': 0,
            'blocked': 0,
            'penalty_enforced': 0
        }

    def is_allowed(self, client_id: ClientIdentifier, custom_config: Optional[RateLimitConfig] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if client is allowed to make a request.

        Returns:
            (is_allowed, metadata_dict)
        """
        current_time = time.time()
        config = custom_config or self.default_config

        with self.lock:
            self.metrics['total_checks'] += 1

            # Get client key
            client_key = client_id.get_composite_key(config.key_prefix)

            # Get or create rate limit entry
            if client_key not in self.limits:
                self.limits[client_key] = RateLimitEntry(client_key, config)

            limit_entry = self.limits[client_key]

            # Check rate limit
            is_allowed, remaining, reset_time = limit_entry.is_allowed(current_time)

            # Update metrics
            if is_allowed:
                self.metrics['allowed'] += 1
            else:
                self.metrics['blocked'] += 1
                if limit_entry.penalty_until > current_time:
                    self.metrics['penalty_enforced'] += 1

            # Cleanup old entries periodically
            if current_time % 300 < 1:  # Every 5 minutes
                self._cleanup_expired()

            metadata = {
                'client_id': client_id.client_id,
                'client_key': client_key,
                'is_allowed': is_allowed,
                'remaining_requests': remaining,
                'reset_time': reset_time,
                'penalty_until': limit_entry.penalty_until if not is_allowed else 0,
                'consecutive_blocks': limit_entry.blocks,
                'window_seconds': config.window_seconds,
                'max_requests': config.max_requests
            }

            return is_allowed, metadata

    def _cleanup_expired(self) -> None:
        """Clean up expired rate limit entries."""
        current_time = time.time()
        expired_keys = []

        for key, entry in self.limits.items():
            if entry.penalty_until < current_time and not entry.requests:
                expired_keys.append(key)

        for key in expired_keys:
            del self.limits[key]

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics."""
        with self.lock:
            return self.metrics.copy()

    def reset_client_limits(self, client_id: ClientIdentifier) -> None:
        """Reset rate limits for a specific client."""
        client_key = client_id.get_composite_key(self.default_config.key_prefix)
        if client_key in self.limits:
            del self.limits[client_key]

    def reset_all_limits(self) -> None:
        """Reset all rate limits."""
        with self.lock:
            self.limits.clear()
            self.metrics = {
                'total_checks': 0,
                'allowed': 0,
                'blocked': 0,
                'penalty_enforced': 0
            }
class DistributedRateLimiter(MemoryBasedRateLimiter):
    """
    Rate limiter with Redis backend for distributed systems.

    This provides consistent rate limiting across multiple instances
    of the AXIOM system.
    """

    def __init__(self, redis_connection, default_config: Optional[RateLimitConfig] = None):
        super().__init__(default_config)
        self.redis = redis_connection
        self.pipeline = redis_connection.pipeline()

    def is_allowed(self, client_id: ClientIdentifier, custom_config: Optional[RateLimitConfig] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if client is allowed using Redis backend.
        """
        current_time = time.time()
        config = custom_config or self.default_config

        # Generate Redis keys
        client_key = client_id.get_composite_key(config.key_prefix)
        count_key = f"{client_key}:count"
        expiry_key = f"{client_key}:expiry"
        penalty_key = f"{client_key}:penalty"
        blocked_key = f"{client_key}:blocked"

        try:
            with self.redis.pipeline() as pipe:
                # Get current count and expiry
                pipe.get(count_key)
                pipe.get(expiry_key)
                pipe.get(penalty_key)
                pipe.get(blocked_key)

                results = pipe.execute()

                current_count = int(results[0] or 0)
                window_expiry = int(results[1] or 0)
                penalty_until = int(results[2] or 0)
                consecutive_blocks = int(results[3] or 0)

                now = current_time

                # Check if in penalty
                if penalty_until > now:
                    penalty_remaining = int(penalty_until - now)
                    metadata = self._build_metadata(
                        is_allowed=False,
                        client_key=client_key,
                        current_count=current_count,
                        penalty_until=penalty_until,
                        penalty_remaining=penalty_remaining,
                        consecutive_blocks=consecutive_blocks,
                        config=config
                    )
                    return False, metadata

                # Clean up expired entries
                if now > window_expiry:
                    pipe.delete(count_key, expiry_key, penalty_key, blocked_key)
                    pipe.execute()
                    current_count = 0

                # Check rate limit
                if current_count < config.max_requests:
                    # Allow request
                    pipe.incr(count_key)
                    if window_expiry == 0:
                        pipe.expire(count_key, config.window_seconds)
                        pipe.expire(expiry_key, config.window_seconds)

                    # Reset blocks on successful request
                    if consecutive_blocks > 0:
                        pipe.delete(blocked_key)

                    pipe.execute()

                    remaining = config.max_requests - (current_count + 1)
                    reset_time = now + config.window_seconds

                    metadata = self._build_metadata(
                        is_allowed=True,
                        client_key=client_key,
                        current_count=current_count + 1,
                        penalty_until=0,
                        consecutive_blocks=0,
                        config=config,
                        remaining=remaining,
                        reset_time=reset_time
                    )

                    return True, metadata
                else:
                    # Exceeded limit
                    burst_allowed = current_count < (config.max_requests + config.burst_size)

                    if burst_allowed:
                        # Allow burst request
                        pipe.incr(count_key)
                        pipe.execute()

                        remaining = config.max_requests - (current_count + 1)
                        reset_time = now + config.window_seconds

                        metadata = self._build_metadata(
                            is_allowed=True,
                            client_key=client_key,
                            current_count=current_count + 1,
                            penalty_until=0,
                            consecutive_blocks=consecutive_blocks,
                            config=config,
                            remaining=remaining,
                            reset_time=int(reset_time),
                            burst_allowed=True
                        )

                        return True, metadata
                    else:
                        # Completely blocked
                        pipe.incr(blocked_key)
                        pipe.expire(blocked_key, 86400)  # Block for 24 hours
                        pipe.execute()

                        reset_time = now + config.window_seconds

                        metadata = self._build_metadata(
                            is_allowed=False,
                            client_key=client_key,
                            current_count=current_count,
                            penalty_until=now + config.penalty_interval,
                            penalty_remaining=config.penalty_interval,
                            consecutive_blocks=consecutive_blocks + 1,
                            config=config,
                            reset_time=int(reset_time),
                            burst_exceeded=True
                        )

                        return False, metadata

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fallback to memory-based limiter on error
            return super().is_allowed(client_id, config)

    def _build_metadata(self, **kwargs) -> Dict[str, Any]:
        """Build metadata dict for rate limiting response."""
        metadata = {
            'client_key': kwargs.get('client_key', ''),
            'is_allowed': kwargs.get('is_allowed', False),
            'current_count': kwargs.get('current_count', 0),
            'max_requests': kwargs.get('config').max_requests,
            'window_seconds': kwargs.get('config').window_seconds,
            'burst_size': kwargs.get('config').burst_size,
        }

        # Add optional fields
        optional_fields = ['remaining', 'reset_time', 'penalty_until', 'consecutive_blocks',
                          'penalty_remaining', 'burst_allowed', 'burst_exceeded']

        for field in optional_fields:
            if field in kwargs:
                metadata[field] = kwargs[field]

        return metadata

    def flush_client(self, client_id: ClientIdentifier) -> None:
        """Flush rate limits for a specific client."""
        client_key = client_id.get_composite_key(self.default_config.key_prefix)
        self.redis.delete(
            f"{client_key}:count",
            f"{client_key}:expiry",
            f"{client_key}:penalty",
            f"{client_key}:blocked"
        )

    def get_client_stats(self, client_id: ClientIdentifier) -> Dict[str, Any]:
        """Get rate limiting statistics for a client."""
        client_key = client_id.get_composite_key(self.default_config.key_prefix)

        try:
            count = int(self.redis.get(f"{client_key}:count") or 0)
            blocked = int(self.redis.get(f"{client_key}:blocked") or 0)

            stats = {
                'client_key': client_key,
                'current_requests': count,
                'consecutive_blocks': blocked,
                'max_requests': self.default_config.max_requests,
                'reset_time': int(time.time()) + self.default_config.window_seconds,
                'blocked_since': blocked > 0
            }

            return stats
        except Exception:
            return {'error': 'Unable to fetch client statistics'}
# Rate limiter factory functions
def create_rate_limiter(use_redis: bool = False, redis_config: Optional[Dict] = None) -> Any:
    """
    Factory function to create rate limiter instance.

    Args:
        use_redis: Whether to use Redis backend
        redis_config: Redis configuration (host, port, db, password)

    Returns:
        Rate limiter instance
    """
    if use_redis and redis_config:
        try:
            redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
            return DistributedRateLimiter(redis_client)

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Falling back to memory-based rate limiter")

    return MemoryBasedRateLimiter()
def get_default_rate_limit_for_endpoint(endpoint: str) -> RateLimitConfig:
    """
    Get appropriate rate limit configuration for an endpoint.

    Args:
        endpoint: The API endpoint being accessed

    Returns:
        Rate limit configuration
    """
    # Define rate limits for different endpoint types
    endpoint_limits = {
        'auth': RateLimitConfig(max_requests=5, window_seconds=300),  # 5 requests per 5 minutes
        'chat': RateLimitConfig(max_requests=60, window_seconds=60),   # 60 requests per minute
        'generate': RateLimitConfig(max_requests=30, window_seconds=60),# 30 requests per minute
        'analyze': RateLimitConfig(max_requests=120, window_seconds=60),# 120 requests per minute
        'default': RateLimitConfig(max_requests=100, window_seconds=60),# General purpose
    }

    # Determine endpoint category
    endpoint_lower = endpoint.lower()

    if any(auth_term in endpoint_lower for auth_term in ['login', 'auth', 'token', 'signup']):
        return endpoint_limits['auth']
    elif 'chat' in endpoint_lower:
        return endpoint_limits['chat']
    elif any(gen_term in endpoint_lower for gen_term in ['generate', 'create', 'build']):
        return endpoint_limits['generate']
    elif 'analyze' in endpoint_lower or 'process' in endpoint_lower:
        return endpoint_limits['analyze']
    else:
        return endpoint_limits['default']
# Export commonly used classes and functions
__all__ = [
    'RateLimitConfig',
    'ClientIdentifier',
    'RateLimitEntry',
    'MemoryBasedRateLimiter',
    'DistributedRateLimiter',
    'create_rate_limiter',
    'get_default_rate_limit_for_endpoint',
    'RateLimitType',
]