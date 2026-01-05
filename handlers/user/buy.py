"""
Purchase flow handlers for FRIENDS Store Telegram Bot.
"""

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import config
from database.db import Database
from services.payment import PaymentService
from utils.keyboards import Keyboards
from utils.logger import get_logger
from utils.message_templates import MessageTemplates as msg
from utils.messages import safe_edit_or_send
from utils.rate_limiter import purchase_limiter, rate_limiter
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("bot")


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product list (callback query)."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    db: Database = context.bot_data["db"]
    products = await db.get_active_products()
    page = context.user_data.get("product_page", 1)

    if not products:
        await safe_edit_or_send(
            query, context, user.id,
            text=msg.error("Tidak ada produk tersedia", "Cek kembali nanti!"),
            reply_markup=Keyboards.navigation(back_target="main")
        )
        return

    # Store products for numbered buttons
    context.user_data["products"] = products

    # Convert to template format
    product_list = [
        {
            "name": p["name"],
            "price": p["price"],
            "stock_count": p.get("stock_count", 0),
            "is_bestseller": p.get("is_bestseller", False),
            "is_new": p.get("is_new", False)
        }
        for p in products
    ]

    await safe_edit_or_send(
        query, context, user.id,
        text=msg.product_list(product_list, page),
        reply_markup=Keyboards.product_list(products, page)
    )


async def show_products_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/beli command - show product list."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    products = await db.get_active_products()

    if not products:
        await update.message.reply_text(
            msg.error("Tidak ada produk tersedia", "Cek kembali nanti!")
        )
        return

    # Store products and reset page
    context.user_data["products"] = products
    context.user_data["product_page"] = 1

    # Convert to template format
    product_list = [
        {
            "name": p["name"],
            "price": p["price"],
            "stock_count": p.get("stock_count", 0),
            "is_bestseller": p.get("is_bestseller", False),
            "is_new": p.get("is_new", False)
        }
        for p in products
    ]

    await update.message.reply_text(
        text=msg.product_list(product_list, 1),
        reply_markup=Keyboards.product_list(products, 1)
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
            text=msg.error("Produk tidak ditemukan"),
            reply_markup=Keyboards.navigation(back_target="products")
        )
        return

    # Get stock count
    stock_count = await db.get_available_stock_count(product_code)

    # Use msg.product_card
    text = msg.product_card(product, stock_count)

    await safe_edit_or_send(
        query, context, user.id,
        text=text,
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
            text=msg.error("Produk tidak ditemukan"),
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
            text=msg.error(message),
            reply_markup=Keyboards.navigation(back_target="products")
        )
        return

    # Record purchase in limiter
    purchase_limiter.record_purchase_start(user.id, product_code)

    # Calculate expiry
    expired_at = datetime.now() + timedelta(minutes=config.transaction.expiry_minutes)

    # Payment pending message
    payment_text = msg.payment_pending(
        qris_tx.order_id,
        product["name"],
        product["price"],
        expired_at
    )

    # Send QRIS image if available
    if qris_tx.qris_url and qris_tx.qris_url.startswith("http"):
        try:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=user.id,
                photo=qris_tx.qris_url,
                caption=payment_text,
                reply_markup=Keyboards.payment_pending(qris_tx.transaction_id)
            )
            return
        except Exception as e:
            logger.warning(f"Failed to send QRIS image: {e}")

    # Fallback to text
    await safe_edit_or_send(
        query, context, user.id,
        text=payment_text,
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
        stock_item = tx_data.get("stock_item", {})
        product = tx_data.get("product", {})
        tx = tx_data.get("transaction", {})

        account = {
            "email": stock_item.get("email", "-"),
            "password": stock_item.get("password", "-"),
            "two_fa_secret": stock_item.get("two_fa_secret"),
            "notes": stock_item.get("notes")
        }

        text = msg.payment_success(
            tx.get("merchant_ref", ""),
            product.get("name", ""),
            tx.get("amount", 0),
            account,
            tx_data.get("paid_at")
        )

        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            reply_markup=Keyboards.navigation(back_target="main")
        )

        # Update limiter
        purchase_limiter.record_purchase_complete(user.id)

    elif status == "EXPIRED":
        tx = tx_data if isinstance(tx_data, dict) else {}
        product = await db.get_product(tx.get("product_code", ""))

        text = f"""
{vs.header('Pembayaran Expired', tx.get('merchant_ref', ''), icon='❌')}

{uf.bold('Produk:')} {product.get('name', '-') if product else '-'}
{uf.bold('Harga:')} {uf.monospace(f"Rp {tx.get('amount', 0):,}".replace(',', '.'))}

{vs.alert('Transaksi sudah kadaluarsa', 'error')}

{uf.italic('Silakan buat pesanan baru.')}
"""

        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            reply_markup=Keyboards.navigation(back_target="main")
        )

        purchase_limiter.record_purchase_complete(user.id)

    elif status == "NOT_FOUND":
        await safe_edit_or_send(
            query, context, user.id,
            text=msg.error("Transaksi tidak ditemukan"),
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

        text = f"""
{vs.header('Transaksi Dibatalkan', '', icon='❌')}

Transaksi telah dibatalkan.

{uf.italic('Gunakan /start untuk kembali ke menu.')}
"""
        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            reply_markup=Keyboards.navigation(back_target="main")
        )
    else:
        await query.answer(f"❌ {message}", show_alert=True)


async def cekbayar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cekbayar command - check payment status."""
    user = update.effective_user
    args = context.args

    if not args:
        text = f"""
{vs.header('Cek Status Pembayaran', '', icon='💳')}

{uf.bold('Gunakan:')} /cekbayar <order_id>

{uf.bold('Contoh:')} {uf.monospace('/cekbayar FRIENDS-1234-ABCD')}
"""
        await update.message.reply_text(text)
        return

    order_id = args[0]
    db: Database = context.bot_data["db"]
    payment_service = PaymentService(db)

    status, tx_data = await payment_service.check_payment_status(order_id)

    status_icon = {
        "PAID": "✅", "PENDING": "⏳", "EXPIRED": "❌", "NOT_FOUND": "❓"
    }

    text = f"""
{vs.header('Status Pembayaran', '', icon=status_icon.get(status, '❓'))}

{uf.bold('Status:')} {status_icon.get(status, '❓')} {status}
{uf.bold('Order ID:')} {uf.monospace(order_id)}
"""
    await update.message.reply_text(text)


# Handler exports
buy_handlers = [
    CommandHandler("beli", show_products_command),
    CommandHandler("cekbayar", cekbayar_command),
    CallbackQueryHandler(show_products, pattern=r"^nav:products$"),
    CallbackQueryHandler(show_product_detail, pattern=r"^product:"),
    CallbackQueryHandler(initiate_purchase, pattern=r"^buy:"),
    CallbackQueryHandler(check_payment_status, pattern=r"^pay:check:"),
    CallbackQueryHandler(cancel_payment, pattern=r"^pay:cancel:"),
]
