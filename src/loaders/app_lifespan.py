from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

# Load logger
from .database import (
    TORTOISE_CONFIG,
    close_db_conn,
)
from .logging import get_logger

logger = get_logger("app_start_up")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.debug("Initializing db connection")
    try:
        async with RegisterTortoise(
            app=app,
            config=TORTOISE_CONFIG,
            generate_schemas=True,
            add_exception_handlers=True,
        ):
            logger.info("Connected to database")
            logger.info("Listening for API events")
            yield
    except Exception as e:
        logger.error(f"Error starting up API server: {str(e)}")
        raise
    finally:
        await close_db_conn()
        logger.info("Shutting down API server")
