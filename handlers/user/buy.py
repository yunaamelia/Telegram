"""
Purchase flow handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import config
from database.db import Database
from services.payment import PaymentService
from utils.keyboards import Keyboards
from utils.formatters import (
    format_product_list_header,
    format_product_detail,
    format_payment_created
)
from utils.messages import safe_edit_or_send
from utils.rate_limiter import rate_limiter, purchase_limiter
from utils.logger import get_logger

logger = get_logger("bot")


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product list."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    db: Database = context.bot_data["db"]

    # Get active products
    products = await db.get_active_products()

    if not products:
        await safe_edit_or_send(
            query, context, user.id,
            text="😔 Maaf, tidak ada produk yang tersedia saat ini.\n\n"
            "Cek kembali nanti!",
            reply_markup=Keyboards.navigation(back_target="main")
        )
        return

    await safe_edit_or_send(
        query, context, user.id,
        text=format_product_list_header(),
        parse_mode="Markdown",
        reply_markup=Keyboards.product_list(products)
    )


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product detail."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    # Extract product code
    product_code = query.data.split(":")[1]

    db: Database = context.bot_data["db"]

    # Get product
    product = await db.get_product(product_code)
    if not product:
        await safe_edit_or_send(
            query, context, user.id,
            text="❌ Produk tidak ditemukan.",
            reply_markup=Keyboards.navigation(back_target="products")
        )
        return

    # Get stock count
    stock_count = await db.get_available_stock_count(product_code)

    await safe_edit_or_send(
        query, context, user.id,
        text=format_product_detail(product, stock_count),
        parse_mode="Markdown",
        reply_markup=Keyboards.product_detail(
            product_code=product_code,
            has_stock=stock_count > 0,
            price=product["price"]
        )
    )


async def initiate_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiate purchase and create payment."""
    query = update.callback_query
    user = update.effective_user

    # Extract product code
    product_code = query.data.split(":")[1]

    db: Database = context.bot_data["db"]

    # Check rate limit
    is_limited, wait_time = rate_limiter.check_rate_limit(user.id)
    if is_limited:
        await query.answer(f"⏳ Tunggu {wait_time} detik", show_alert=True)
        return

    # Check purchase limits
    can_buy, error_msg = purchase_limiter.can_purchase(user.id, product_code)
    if not can_buy:
        await query.answer(error_msg, show_alert=True)
        return

    await query.answer("⏳ Membuat transaksi...")

    # Get product
    product = await db.get_product(product_code)
    if not product:
        await safe_edit_or_send(
            query, context, user.id,
            text="❌ Produk tidak ditemukan.",
            reply_markup=Keyboards.navigation(back_target="products")
        )
        return

    # Create payment
    payment_service = PaymentService(db)
    success, message, qris_tx = await payment_service.create_payment(
        user_id=user.id,
        product_code=product_code,
        customer_name=user.first_name or "Customer"
    )

    if not success:
        await safe_edit_or_send(
            query, context, user.id,
            text=f"❌ {message}",
            reply_markup=Keyboards.navigation(back_target="products")
        )
        return

    # Record purchase in limiter
    purchase_limiter.record_purchase_start(user.id, product_code)

    # Calculate expiry
    from datetime import datetime, timedelta
    expired_at = datetime.now() + timedelta(minutes=config.transaction.expiry_minutes)

    # Send QRIS image if available
    if qris_tx.qris_url and qris_tx.qris_url.startswith("http"):
        try:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=user.id,
                photo=qris_tx.qris_url,
                caption=format_payment_created(
                    transaction_id=qris_tx.order_id,
                    product_name=product["name"],
                    amount=product["price"],
                    expired_at=expired_at
                ),
                parse_mode="Markdown",
                reply_markup=Keyboards.payment_pending(qris_tx.transaction_id)
            )
            return
        except Exception as e:
            logger.warning(f"Failed to send QRIS image: {e}")

    # Fallback to text
    await safe_edit_or_send(
        query, context, user.id,
        text=format_payment_created(
            transaction_id=qris_tx.order_id,
            product_name=product["name"],
            amount=product["price"],
            expired_at=expired_at
        ),
        parse_mode="Markdown",
        reply_markup=Keyboards.payment_pending(qris_tx.transaction_id)
    )


async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check payment status."""
    query = update.callback_query
    user = update.effective_user

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]
    payment_service = PaymentService(db)

    await query.answer("⏳ Mengecek status...")

    status, tx_data = await payment_service.check_payment_status(transaction_id)

    if status == "PAID":
        # Payment successful - deliver account
        from utils.formatters import format_payment_success

        stock_item = tx_data.get("stock_item", {})
        product = tx_data.get("product", {})

        await safe_edit_or_send(
            query, context, user.id,
            text=format_payment_success(
                transaction_id=tx_data["transaction"]["merchant_ref"],
                product_name=product.get("name", ""),
                amount=tx_data["transaction"]["amount"],
                paid_at=tx_data.get("paid_at"),
                stock_item=stock_item or {}
            ),
            parse_mode="Markdown",
            reply_markup=Keyboards.navigation(back_target="main")
        )

        # Update limiter
        purchase_limiter.record_purchase_complete(user.id)

    elif status == "EXPIRED":
        from utils.formatters import format_payment_expired

        tx = tx_data if isinstance(tx_data, dict) else {}
        product = await db.get_product(tx.get("product_code", ""))

        await safe_edit_or_send(
            query, context, user.id,
            text=format_payment_expired(
                transaction_id=tx.get("merchant_ref", ""),
                product_name=product.get("name", "") if product else "",
                amount=tx.get("amount", 0)
            ),
            parse_mode="Markdown",
            reply_markup=Keyboards.navigation(back_target="main")
        )

        purchase_limiter.record_purchase_complete(user.id)

    elif status == "NOT_FOUND":
        await safe_edit_or_send(
            query, context, user.id,
            text="❌ Transaksi tidak ditemukan.",
            reply_markup=Keyboards.navigation(back_target="main")
        )

    else:
        await query.answer("⏳ Pembayaran belum diterima. Silakan scan QRIS.", show_alert=True)


async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel pending payment."""
    query = update.callback_query
    user = update.effective_user

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]
    payment_service = PaymentService(db)

    success, message = await payment_service.cancel_payment(transaction_id, user.id)

    if success:
        purchase_limiter.record_purchase_complete(user.id)
        await query.answer("✅ Transaksi dibatalkan")
        await safe_edit_or_send(
            query, context, user.id,
            text="❌ Transaksi telah dibatalkan.\n\n"
            "Gunakan /start untuk kembali ke menu.",
            reply_markup=Keyboards.navigation(back_target="main")
        )
    else:
        await query.answer(f"❌ {message}", show_alert=True)


# Handler exports
buy_handlers = [
    CallbackQueryHandler(show_products, pattern=r"^nav:products$"),
    CallbackQueryHandler(show_product_detail, pattern=r"^product:"),
    CallbackQueryHandler(initiate_purchase, pattern=r"^buy:"),
    CallbackQueryHandler(check_payment_status, pattern=r"^pay:check:"),
    CallbackQueryHandler(cancel_payment, pattern=r"^pay:cancel:"),
]
