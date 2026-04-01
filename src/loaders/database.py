from tortoise import Tortoise, connections, run_async
from .config import config
from .logging import get_logger


logger = get_logger("DATABASE")

TORTOISE_CONFIG = {
    "connections": {"default": config.DATABASE_URL},
    "apps": {
        "src": {
            "models": ["src.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "UTC",
}


async def generate_db_schemas():
    logger.debug("Running migrations")
    await Tortoise.generate_schemas()


async def close_db_conn():
    logger.info("Closing database connection")
    await Tortoise.close_connections()
