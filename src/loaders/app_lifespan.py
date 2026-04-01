from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

# Load logger
from .database import (
    generate_db_schemas,
    TORTOISE_CONFIG,
    close_db_conn,
)
from .logging import get_logger

logger = get_logger("app_start_up")


async def app_shutdown_event_handler():
    logger.debug("Closing database connection")
    await close_db_conn()
    logger.info("Shutting down API server")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logger.debug("Initialzing db connection")
    try:
        async with RegisterTortoise(
            app=app,
            config=TORTOISE_CONFIG,
            modules={"src": ["src.models"]},
            generate_schemas=True,
            add_exception_handlers=True,
        ):
            await generate_db_schemas()
            logger.info("Connected to database")

            logger.info("Listening for API events")
            # The main yield
            yield
    except Exception as e:
        logger.error(f"Error starting up API server: {str(e)}")
        raise e

    # Clean up
    await app_shutdown_event_handler()
