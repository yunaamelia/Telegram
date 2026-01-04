"""
Message formatters for FRIENDS Store Telegram Bot.
Rich MarkdownV2 styling with underline, bold, code, dividers.
"""

from datetime import datetime
from typing import Dict, Optional, List
import pytz
import math
import re


# Indonesia Western Time
WIB = pytz.timezone("Asia/Jakarta")

# Divider line
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"

# Characters that need escaping in MarkdownV2
ESCAPE_CHARS = r'_*[]()~`>#+-=|{}.!'


def escape_md(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    if not text:
        return ""
    return re.sub(f'([{re.escape(ESCAPE_CHARS)}])', r'\\\1', str(text))


def format_currency(amount: int) -> str:
    """Format amount as Indonesian Rupiah."""
    return f"Rp {amount:,}".replace(",", ".")



def format_datetime(dt: Optional[datetime], include_time: bool = True) -> str:
    """Format datetime to Indonesian format (WIB)."""
    if not dt:
        return "-"

    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)

    # Convert to WIB if not already
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    dt = dt.astimezone(WIB)

    if include_time:
        return dt.strftime("%d %b %Y, %H:%M WIB")
    return dt.strftime("%d %b %Y")


def format_welcome(store_name: str, user_first_name: str) -> str:
    """Format welcome message."""
    name = escape_md(user_first_name)
    store = escape_md(store_name)
    return (
        f"*🛍️ {store}* 🛍️\n"
        f"{DIVIDER}\n\n"
        f"Halo, *{name}*\\! 👋\n\n"
        f"Selamat datang di _{store}_\\!\n"
        f"Butuh akun premium\\? Kamu di tempat yang tepat\\!\n\n"
        f"{DIVIDER}\n"
        f"_Pilih menu di bawah untuk mulai berbelanja_"
    )


def format_product_list(products: List[Dict], page: int = 1, items_per_page: int = 6) -> str:
    """Format product list with numbered items - MarkdownV2 style."""
    total_pages = max(1, math.ceil(len(products) / items_per_page))
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    
    lines = [
        f"*📦 Product List* \\(Page {page}/{total_pages}\\)",
        "",
    ]
    
    for idx, product in enumerate(page_products, start=1):
        name = escape_md(product.get('name', 'Unknown'))
        price = escape_md(format_currency(product.get('price', 0)))
        stock = product.get('stock', 0)
        
        stock_text = f"*Stock: {stock}*" if stock > 0 else "*Stock: 0* ❌"
        
        lines.append(f"*{idx}\\.*  __{name}__")
        lines.append(f"   💰 `{price}` \\| 📊 {stock_text}")
        lines.append("")
    
    return "\n".join(lines)


def format_product_list_header() -> str:
    """Format product list header."""
    return """*📦 Daftar Produk*

_Pilih nomor produk yang ingin kamu beli:_
"""


def format_product_detail(product: Dict, stock_count: int) -> str:
    """Format product detail message - MarkdownV2 style."""
    name = escape_md(product.get('name', 'Unknown'))
    price = escape_md(format_currency(product.get('price', 0)))
    description = escape_md(product.get('description', 'Tidak ada deskripsi.'))
    
    if stock_count > 0:
        stock_text = f"`{stock_count} available` ✅"
    else:
        stock_text = "`0 available` ❌"

    return f"""*📦 {name}*
{DIVIDER}

💰 *Price:* `{price}`
📊 *Stock:* {stock_text}

{DIVIDER}
📝 *Description:*
_{description}_
"""


def format_payment_created(
    transaction_id: str,
    product_name: str,
    amount: int,
    expired_at: datetime
) -> str:
    """Format payment created message - MarkdownV2 style."""
    return f"""*💳 QRIS Payment*
{DIVIDER}

*📦 Product:* __{product_name}__
*💰 Total:* `{format_currency(amount)}`
*🆔 Order ID:* `{transaction_id}`

{DIVIDER}

⏰ *Deadline:* `{format_datetime(expired_at)}`

_Scan QRIS above using your favorite e-wallet app_
"""


def format_payment_success(
    transaction_id: str,
    product_name: str,
    amount: int,
    paid_at: datetime,
    stock_item: Dict
) -> str:
    """Format payment success - MarkdownV2 style."""
    two_fa = f"\n🔐 *2FA Secret:* `{stock_item['two_fa_secret']}`" if stock_item.get('two_fa_secret') else ""
    notes = f"\n📝 *Notes:* _{stock_item['notes']}_" if stock_item.get('notes') else ""

    return f"""*✅ Pembayaran Berhasil!*
{DIVIDER}

*📦 Produk:* __{product_name}__
*💰 Total:* `{format_currency(amount)}`
*🆔 Order ID:* `{transaction_id}`
*📅 Tanggal:* `{format_datetime(paid_at)}`

{DIVIDER}

*🔑 Detail Akun:*
📧 *Email:* `{stock_item['email']}`
🔒 *Password:* `{stock_item['password']}`{two_fa}{notes}

{DIVIDER}

⚠️ *Penting:*
• Simpan data akun dengan baik
• Jangan bagikan kepada siapapun
• Segera ganti password setelah login

_Terima kasih telah berbelanja!_ 🙏
"""


def format_payment_expired(
    transaction_id: str,
    product_name: str,
    amount: int
) -> str:
    """Format payment expired message."""
    return f"""*⏰ Transaksi Kadaluarsa*
{DIVIDER}

*📦 Produk:* __{product_name}__
*💰 Total:* `{format_currency(amount)}`
*🆔 Order ID:* `{transaction_id}`

{DIVIDER}

_Waktu pembayaran telah habis. Silakan buat pesanan baru jika masih berminat._
"""


def format_transaction_list(transactions: List[Dict], page: int = 1, items_per_page: int = 6) -> str:
    """Format transaction list for history - MarkdownV2 style."""
    if not transactions:
        return "*📜 Riwayat Transaksi*\n\n_Belum ada riwayat transaksi._"

    total_pages = max(1, math.ceil(len(transactions) / items_per_page))
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_transactions = transactions[start_idx:end_idx]

    status_emoji = {
        "PAID": "✅",
        "UNPAID": "⏳",
        "EXPIRED": "❌",
        "CANCELLED": "🚫",
        "REFUND_REQUESTED": "💰",
        "REFUNDED": "💸"
    }

    lines = [
        f"*📜 Your Transaction History*",
        DIVIDER,
        ""
    ]

    for idx, tx in enumerate(page_transactions, start=1):
        emoji = status_emoji.get(tx["status"], "❓")
        product_name = tx.get('product_name', tx.get('product_code', 'Unknown'))
        
        lines.append(f"*{idx}.* __{product_name}__")
        lines.append(f"   {emoji} *{tx['status']}* | `{format_currency(tx['amount'])}`")
        lines.append(f"   📅 _{format_datetime(tx['created_at'])}_")
        lines.append("")
        lines.append(DIVIDER)
        lines.append("")

    return "\n".join(lines)


def format_transaction_detail(tx: Dict) -> str:
    """Format single transaction detail."""
    status_text = {
        "PAID": "✅ Berhasil",
        "UNPAID": "⏳ Menunggu Pembayaran",
        "EXPIRED": "❌ Kadaluarsa",
        "CANCELLED": "🚫 Dibatalkan",
        "REFUND_REQUESTED": "💰 Menunggu Refund",
        "REFUNDED": "💸 Sudah Refund"
    }.get(tx["status"], tx["status"])

    return f"""*📋 Detail Transaksi*
{DIVIDER}

*🆔 Order ID:* `{tx['transaction_id']}`
*📦 Produk:* __{tx.get('product_name', tx['product_code'])}__
*💰 Total:* `{format_currency(tx['amount'])}`
*📊 Status:* {status_text}
*📅 Dibuat:* `{format_datetime(tx['created_at'])}`

{DIVIDER}
"""


def format_stock_summary(stock_list: List[Dict], page: int = 1, items_per_page: int = 6) -> str:
    """Format stock summary for admin - MarkdownV2 style."""
    total_products = len(stock_list)
    low_stock_count = sum(1 for item in stock_list if item.get("available", 0) < 5)
    
    total_pages = max(1, math.ceil(total_products / items_per_page))
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = stock_list[start_idx:end_idx]

    lines = [
        f"*📊 Stock Summary*",
        DIVIDER,
        "",
        f"📦 *Total Products:* `{total_products}`",
        f"⚠️ *Low Stock Warning:* `{low_stock_count} products`",
        "",
        DIVIDER,
        ""
    ]

    for idx, item in enumerate(page_items, start=1):
        available = item.get("available", 0)
        price = format_currency(item.get('price', 0))
        name = item.get('name', 'Unknown')
        
        warning = " ⚠️" if available < 5 and available > 0 else ""
        if available == 0:
            warning = " ❌"
        
        lines.append(f"*{idx}.* __{name}__")
        lines.append(f"   📊 Stock: *{available}*{warning} | 💰 `{price}`")
        lines.append("")

    return "\n".join(lines)


def format_stats(stats: Dict) -> str:
    """Format bot statistics for admin."""
    tx_stats = stats.get("transactions", {})

    return f"""*📊 FRIENDS Store Statistics*
{DIVIDER}

*👥 Users*
├ Total: `{stats.get('total_users', 0):,}`
└ Baru Hari Ini: `{stats.get('new_users_today', 0):,}`

*💰 Revenue*
├ Hari Ini: `{format_currency(stats.get('revenue_today', 0))}`
└ Total: `{format_currency(stats.get('total_revenue', 0))}`

*📦 Transaksi*
├ ✅ Paid: `{tx_stats.get('PAID', 0):,}`
├ ⏳ Pending: `{tx_stats.get('UNPAID', 0):,}`
├ ❌ Expired: `{tx_stats.get('EXPIRED', 0):,}`
└ 💸 Refunded: `{tx_stats.get('REFUNDED', 0):,}`

{DIVIDER}
"""


def format_daily_broadcast(
    date: datetime,
    paid_count: int,
    total_amount: int,
    stock_list: List[Dict]
) -> str:
    """Format daily auto-broadcast message."""
    date_str = date.strftime("%d %B %Y")

    lines = [
        f"*📊 Update Harian - {date_str}*",
        DIVIDER,
        "",
        f"✅ *Transaksi Berhasil:* `{paid_count}`",
        f"💰 *Total Penjualan:* `{format_currency(total_amount)}`",
        "",
        "*🛍️ Stok Produk:*"
    ]

    low_stock = []
    for item in stock_list:
        available = item.get("available", 0)
        total = item.get("total", 1)
        percent = available / total if total > 0 else 0

        if available == 0:
            warning = " ❌"
            low_stock.append(f"• _{item['name']}_ HABIS!")
        elif percent <= 0.1:
            warning = " 🚨"
            low_stock.append(f"• _{item['name']}_ tinggal {available}!")
        elif percent <= 0.3:
            warning = " ⚠️"
        else:
            warning = ""

        if item.get("is_active", True):
            lines.append(f"• {item['name']}: `{available}` tersedia{warning}")

    if low_stock:
        lines.append("")
        lines.append("*⚠️ Peringatan Stok:*")
        lines.extend(low_stock)

    lines.append("")
    lines.append("_🛒 Order sekarang: /start_")

    return "\n".join(lines)


def format_help_order() -> str:
    """Format order guide."""
    return f"""*📖 Cara Order*
{DIVIDER}

*1️⃣* Pilih menu *🛒 Beli Produk*
*2️⃣* Pilih produk yang diinginkan
*3️⃣* Klik *💳 Bayar Sekarang*
*4️⃣* Scan QRIS dengan e-wallet
*5️⃣* Setelah bayar, akun akan dikirim otomatis

{DIVIDER}

⏰ *Batas waktu pembayaran:* `15 menit`

_Jika ada kendala, hubungi admin._
"""


def format_help_payment() -> str:
    """Format payment guide."""
    return f"""*💳 Cara Pembayaran*
{DIVIDER}

Kami menggunakan *QRIS* untuk pembayaran.

*E-Wallet yang Didukung:*
• GoPay
• OVO
• Dana
• ShopeePay
• LinkAja
• Dan lainnya...

{DIVIDER}

*Langkah Pembayaran:*
*1️⃣* Buka aplikasi e-wallet
*2️⃣* Pilih menu Scan QR
*3️⃣* Scan kode QRIS
*4️⃣* Konfirmasi pembayaran

⏰ *Batas Waktu:* `15 menit`
_⚠️ Pembayaran otomatis dibatalkan jika melewati batas waktu._
"""


def format_help_faq() -> str:
    """Format FAQ."""
    return f"""*❓ FAQ Produk*
{DIVIDER}

*Q: Apa yang termasuk dalam akun?*
_A: Setiap akun berisi email, password, dan 2FA (jika ada)._

*Q: Berapa lama akun aktif?*
_A: Tergantung produk. Lihat deskripsi produk untuk info lengkap._

*Q: Bagaimana jika akun tidak bisa login?*
_A: Hubungi admin untuk pengecekan dan penggantian._

*Q: Bagaimana cara pakai 2FA?*
_A: Gunakan aplikasi authenticator untuk scan secret key._

*Q: Apakah ada refund?*
_A: Ya, dalam waktu 24 jam jika akun tidak sesuai deskripsi._

{DIVIDER}
"""


def format_help_contact(support_username: str) -> str:
    """Format contact info."""
    return f"""*📞 Contact Admin*
{DIVIDER}

Butuh bantuan? Hubungi admin kami!

👤 *Support:* @{support_username}
⏰ *Waktu Respon:* `1-24 jam`

{DIVIDER}

*Saat menghubungi, sertakan:*
• Order ID \\(jika ada\\)
• Screenshot masalah
• Deskripsi kendala

_Kami akan membantu secepatnya!_ 🙏
"""
