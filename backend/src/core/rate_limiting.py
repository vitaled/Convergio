"""
Rate Limiting System for API Protection
Implements token bucket algorithm with Redis backend
"""

import time
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from src.agents.utils.config import get_settings

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    burst_size: int = 10
    window_size: int = 60  # seconds
    block_duration: int = 300  # seconds to block after violation

class RateLimiter:
    """Token bucket rate limiter with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.settings = get_settings()
        
    async def _get_bucket_key(self, identifier: str) -> str:
        """Generate Redis key for rate limit bucket"""
        return f"rate_limit:{identifier}"
    
    async def _get_block_key(self, identifier: str) -> str:
        """Generate Redis key for blocked identifiers"""
        return f"rate_limit_blocked:{identifier}"
    
    async def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked"""
        block_key = await self._get_block_key(identifier)
        return await self.redis.exists(block_key)
    
    async def check_rate_limit(self, identifier: str) -> Dict[str, Any]:
        """
        Check rate limit for identifier
        Returns dict with allowed status and remaining tokens
        """
        if await self.is_blocked(identifier):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        bucket_key = await self._get_bucket_key(identifier)
        now = int(time.time())
        
        # Get current bucket state
        bucket_data = await self.redis.hgetall(bucket_key)
        
        if not bucket_data:
            # Initialize bucket
            tokens = self.settings.rate_limit_burst_size
            last_refill = now
        else:
            tokens = int(bucket_data.get(b'tokens', 0))
            last_refill = int(bucket_data.get(b'last_refill', now))
        
        # Calculate tokens to add based on time passed
        time_passed = now - last_refill
        tokens_to_add = (time_passed // self.settings.rate_limit_window_size) * self.settings.rate_limit_requests_per_minute
        
        # Refill bucket
        tokens = min(
            self.settings.rate_limit_burst_size,
            tokens + tokens_to_add
        )
        
        # Update last refill time
        if tokens_to_add > 0:
            last_refill = now - (time_passed % self.settings.rate_limit_window_size)
        
        # Check if request is allowed
        if tokens > 0:
            tokens -= 1
            allowed = True
        else:
            allowed = False
        
        # Update bucket in Redis
        await self.redis.hset(
            bucket_key,
            mapping={
                'tokens': tokens,
                'last_refill': last_refill
            }
        )
        
        # Set expiration for bucket
        await self.redis.expire(bucket_key, self.settings.rate_limit_window_size * 2)
        
        # If rate limit exceeded, block the identifier
        if not allowed:
            await self._block_identifier(identifier)
        
        return {
            'allowed': allowed,
            'remaining_tokens': max(0, tokens),
            'reset_time': last_refill + self.settings.rate_limit_window_size
        }
    
    async def _block_identifier(self, identifier: str):
        """Block identifier for block_duration seconds"""
        block_key = await self._get_block_key(identifier)
        await self.redis.setex(
            block_key,
            self.settings.rate_limit_block_duration,
            'blocked'
        )
    
    async def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for identifier"""
        bucket_key = await self._get_bucket_key(identifier)
        bucket_data = await self.redis.hgetall(bucket_key)
        
        if not bucket_data:
            return {
                'tokens': self.settings.rate_limit_burst_size,
                'max_tokens': self.settings.rate_limit_burst_size,
                'reset_time': int(time.time()) + self.settings.rate_limit_window_size
            }
        
        tokens = int(bucket_data.get(b'tokens', 0))
        last_refill = int(bucket_data.get(b'last_refill', int(time.time())))
        
        return {
            'tokens': tokens,
            'max_tokens': self.settings.rate_limit_burst_size,
            'reset_time': last_refill + self.settings.rate_limit_window_size
        }

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)
        
        # Get identifier (IP address or user ID)
        identifier = self._get_identifier(request)
        
        try:
            # Check rate limit
            result = await self.rate_limiter.check_rate_limit(identifier)
            
            if not result['allowed']:
                return JSONResponse(
                    status_code=429,
                    content={
                        'error': 'Rate limit exceeded',
                        'retry_after': result['reset_time'] - int(time.time()),
                        'detail': 'Too many requests. Please try again later.'
                    }
                )
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers['X-RateLimit-Limit'] = str(self.rate_limiter.settings.rate_limit_requests_per_minute)
            response.headers['X-RateLimit-Remaining'] = str(result['remaining_tokens'])
            response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log error and continue without rate limiting
            print(f"Rate limiting error: {e}")
            return await call_next(request)
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = [
            '/health',
            '/metrics',
            '/docs',
            '/openapi.json'
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP address)"""
        # Get real IP address (considering proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

async def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        # Initialize Redis client
        redis_client = redis.Redis(
            host=get_settings().redis_host,
            port=get_settings().redis_port,
            db=get_settings().redis_db,
            decode_responses=False
        )
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter

async def create_rate_limit_middleware() -> RateLimitMiddleware:
    """Create rate limit middleware instance"""
    rate_limiter = await get_rate_limiter()
    return RateLimitMiddleware(rate_limiter)
