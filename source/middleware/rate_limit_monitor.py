from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime, timedelta
import logging
import time
import asyncio
from typing import Dict, List, Tuple
from source.modules.database import AsyncSessionLocal
from source.modules.models import RateLimitStats
from sqlalchemy.future import select
from sqlalchemy import func

logger = logging.getLogger("rate_limit_monitor")

class RateLimitMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_counters = {
            "per_ip": {},       # ip_address -> list of timestamps
            "global": [],       # list of all timestamps
            "rejected": {
                "per_ip": 0,
                "global": 0
            }
        }
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data())

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Sleduj pouze odpovědi s kódem 429 (Too Many Requests)
        if response.status_code == 429:
            client_ip = request.client.host
            error_detail = ""
            
            # Pokus se získat detail chyby z odpovědi
            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                from json import loads
                error_json = loads(response_body)
                error_detail = error_json.get("error", "")
                
                # Znovu vytvořit response objekt - nezbytné protože jsme již použili body_iterator
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Chyba při čtení odpovědi: {e}")
            
            # Určit typ rate limitu z chybové zprávy
            limit_type = "global" if "přetížena" in error_detail else "per_ip"
            
            if limit_type == "global":
                self.rate_limit_counters["rejected"]["global"] += 1
                logger.warning(f"Globální rate limit překročen: {client_ip} - {request.url.path}")
            else:
                self.rate_limit_counters["rejected"]["per_ip"] += 1
                logger.warning(f"Rate limit pro IP překročen: {client_ip} - {request.url.path}")
            
            # Každých 100 odmítnutí zaloguj statistiky
            total_rejected = sum(self.rate_limit_counters["rejected"].values())
            if total_rejected % 100 == 0:
                self.log_statistics()
            
            # Uložení záznamu do databáze
            try:
                async with AsyncSessionLocal() as db:
                    # Vytvoření nového záznamu
                    stat = RateLimitStats(
                        timestamp=datetime.now(),
                        ip_address=client_ip,
                        path=str(request.url.path),
                        limit_type=limit_type,
                        error_message=error_detail,
                        day=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                    
                    # Uložení do databáze
                    db.add(stat)
                    try:
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Chyba při ukládání statistik do databáze: {e}")
            except Exception as e:
                logger.error(f"Chyba při přístupu k databázi: {e}")
        
        return response
    
    def log_statistics(self):
        """Zaloguje aktuální statistiky rate limitingu"""
        logger.info(
            f"Rate limit statistiky: "
            f"IP odmítnutí: {self.rate_limit_counters['rejected']['per_ip']}, "
            f"Globální odmítnutí: {self.rate_limit_counters['rejected']['global']}"
        )
    
    async def _cleanup_old_data(self):
        """Periodicky čistí staré záznamy a generuje denní přehledy"""
        while True:
            await asyncio.sleep(3600)  # Jednou za hodinu
            self.log_statistics()  # Zaloguje statistiky před vyčištěním

            # Generování denních přehledů do databáze
            try:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday = today - timedelta(days=1)
                
                async with AsyncSessionLocal() as db:
                    # Získání počtu IP limitů za předchozí den
                    ip_rejections = await db.execute(
                        select(func.count()).where(
                            RateLimitStats.day == yesterday,
                            RateLimitStats.limit_type == "per_ip"
                        )
                    )
                    ip_count = ip_rejections.scalar()
                    
                    # Získání počtu globálních limitů za předchozí den
                    global_rejections = await db.execute(
                        select(func.count()).where(
                            RateLimitStats.day == yesterday,
                            RateLimitStats.limit_type == "global"
                        )
                    )
                    global_count = global_rejections.scalar()
                    
                    logger.info(f"Denní statistiky za {yesterday.date()}: "
                               f"IP odmítnutí: {ip_count}, "
                               f"Globální odmítnutí: {global_count}")
                    
            except Exception as e:
                logger.error(f"Chyba při generování denních přehledů: {e}")

            # Reset počítadel každých 24 hodin
            midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if datetime.now() - midnight < timedelta(hours=1):
                logger.info("Resetování denních statistik rate limitingu")
                self.rate_limit_counters["rejected"] = {"per_ip": 0, "global": 0}