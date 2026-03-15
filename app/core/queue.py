from arq.connections import ArqRedis, RedisSettings, create_pool

from app.core.config import settings


def get_redis_settings() -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    url = settings.redis_url
    # Expected form: redis://host:port/db
    url = url.replace("redis://", "")
    host_port, _, db_str = url.partition("/")
    host, _, port_str = host_port.partition(":")
    return RedisSettings(
        host=host or "localhost",
        port=int(port_str) if port_str else 6379,
        database=int(db_str) if db_str else 0,
    )


async def get_arq_pool() -> ArqRedis:
    """Create and return an ARQ Redis connection pool."""
    return await create_pool(get_redis_settings())
