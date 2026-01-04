"""
Database seeding script for FRIENDS Store Telegram Bot.
Seeds initial products and super admin.
"""

import asyncio
from typing import List, Dict

from database.db import Database
from config import config
from utils.logger import get_logger

logger = get_logger("database")

# Initial products to seed
INITIAL_PRODUCTS: List[Dict] = [
    {
        "product_code": "github_student_fresh",
        "name": "GitHub Student Fresh",
        "description": "Akun GitHub Student Developer Pack baru. Termasuk berbagai benefit seperti GitHub Pro, Azure credits, dan banyak lagi.",
        "price": 50000
    },
    {
        "product_code": "github_student_old",
        "name": "GitHub Student Used/Old",
        "description": "Akun GitHub Student Developer Pack bekas (masih aktif). Harga lebih murah dengan benefit yang sama.",
        "price": 15000
    },
    {
        "product_code": "digitalocean_200_3",
        "name": "Digital Ocean $200 (3 Droplets)",
        "description": "Akun DigitalOcean dengan kredit $200, maksimum 3 droplets. Berlaku 60 hari.",
        "price": 70000
    },
    {
        "product_code": "digitalocean_200_10",
        "name": "Digital Ocean $200 (10 Droplets)",
        "description": "Akun DigitalOcean dengan kredit $200, maksimum 10 droplets. Berlaku 60 hari.",
        "price": 100000
    }
]


async def seed_database(db: Database) -> None:
    """Seed the database with initial data."""
    logger.info("Starting database seeding...")

    # Seed products
    for product in INITIAL_PRODUCTS:
        existing = await db.get_product(product["product_code"])
        if not existing:
            await db.add_product(
                product_code=product["product_code"],
                name=product["name"],
                description=product["description"],
                price=product["price"]
            )
            logger.info(f"Added product: {product['name']}")
        else:
            logger.info(f"Product already exists: {product['name']}")

    # Seed super admin
    if config.bot.super_admin_id:
        existing_admin = await db.get_admin(config.bot.super_admin_id)
        if not existing_admin:
            await db.add_admin(
                user_id=config.bot.super_admin_id,
                role="super_admin",
                added_by=config.bot.super_admin_id
            )
            logger.info(f"Added super admin: {config.bot.super_admin_id}")
        else:
            logger.info(f"Super admin already exists: {config.bot.super_admin_id}")

    logger.info("Database seeding completed!")


async def main():
    """Run seed script standalone."""
    db = Database(config.database.path)
    await db.init()
    await seed_database(db)
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
