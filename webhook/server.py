"""
aiohttp webhook server for FRIENDS Store Telegram Bot.
"""

import asyncio
from typing import Optional, Callable
from aiohttp import web

from config import config
from utils.logger import get_logger

logger = get_logger("webhook")


class WebhookServer:
    """aiohttp server for handling webhooks."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: Optional[int] = None
    ):
        self.host = host
        self.port = port or config.webhook.port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self._midtrans_handler: Optional[Callable] = None
        self._bot = None
        self._db = None

        self._setup_routes()

    def _setup_routes(self):
        """Set up server routes."""
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_post("/webhook/midtrans", self._midtrans_webhook_handler)

    def set_dependencies(self, bot, db):
        """Set bot and database dependencies."""
        self._bot = bot
        self._db = db

    def set_midtrans_handler(self, handler: Callable):
        """Set the Midtrans callback handler function."""
        self._midtrans_handler = handler

    async def _health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        from datetime import datetime

        health_data = {
            "status": "healthy",
            "bot": "running" if self._bot else "not connected",
            "database": "connected" if self._db else "not connected",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

        return web.json_response(health_data)

    async def _midtrans_webhook_handler(self, request: web.Request) -> web.Response:
        """Handle Midtrans webhook callback."""
        from utils.security import validate_webhook_token, validate_midtrans_signature, is_ip_allowed

        # Check IP whitelist
        client_ip = request.headers.get("X-Forwarded-For", request.remote)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        if not is_ip_allowed(client_ip):
            logger.warning(f"Webhook request from non-whitelisted IP: {client_ip}")
            # Don't block, just log (Midtrans IPs may vary)

        # Check webhook token
        token = request.query.get("token")
        if not validate_webhook_token(token):
            logger.warning("Invalid webhook token")
            return web.json_response({"status": "error", "message": "unauthorized"}, status=401)

        try:
            data = await request.json()
            logger.info(f"Midtrans callback received: {data.get('order_id')}")

            # Validate signature
            order_id = data.get("order_id", "")
            status_code = data.get("status_code", "")
            gross_amount = data.get("gross_amount", "")
            signature = data.get("signature_key", "")

            if not validate_midtrans_signature(order_id, status_code, gross_amount, signature):
                logger.warning(f"Invalid signature for order: {order_id}")
                return web.json_response({"status": "error", "message": "invalid signature"}, status=400)

            # Process callback
            if self._midtrans_handler:
                await self._midtrans_handler(data)

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def start(self):
        """Start the webhook server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        logger.info(f"Webhook server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the webhook server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Webhook server stopped")
