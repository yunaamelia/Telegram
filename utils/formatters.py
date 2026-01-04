"""
Message formatters for FRIENDS Store Telegram Bot.
"""

from datetime import datetime
from typing import Dict, Optional, List
import pytz


# Indonesia Western Time
WIB = pytz.timezone("Asia/Jakarta")


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
    return f"""
🛍️ **{store_name}** 🛍️

Halo, {user_first_name}! 👋

Selamat datang di {store_name}!
Butuh akun premium? Kamu di tempat yang tepat!

Pilih menu di bawah untuk mulai berbelanja:
"""


def format_product_list_header() -> str:
    """Format product list header."""
    return """
📦 **Daftar Produk**

Pilih produk yang ingin kamu beli:
"""


def format_product_detail(
    product: Dict,
    stock_count: int
) -> str:
    """Format product detail message."""
    status = f"✅ Tersedia ({stock_count} stok)" if stock_count > 0 else "❌ Stok Habis"

    return f"""
📦 **{product['name']}**

{product.get('description', 'Tidak ada deskripsi.')}

💰 **Harga:** {format_currency(product['price'])}
📊 **Status:** {status}
"""


def format_payment_created(
    transaction_id: str,
    product_name: str,
    amount: int,
    expired_at: datetime
) -> str:
    """Format payment created message with QRIS."""
    return f"""
💳 **Pembayaran QRIS**

📦 **Produk:** {product_name}
💰 **Total:** {format_currency(amount)}
🆔 **Order ID:** `{transaction_id}`

⏰ **Batas Waktu:** {format_datetime(expired_at)}

Scan QRIS di atas menggunakan aplikasi e-wallet favorit kamu:
• GoPay, OVO, Dana, ShopeePay, LinkAja, dll

⚠️ Pembayaran akan otomatis dibatalkan jika melewati batas waktu.
"""


def format_payment_success(
    transaction_id: str,
    product_name: str,
    amount: int,
    paid_at: datetime,
    stock_item: Dict
) -> str:
    """Format payment success with account details."""
    two_fa = f"\n🔐 **2FA Secret:** `{stock_item['two_fa_secret']}`" if stock_item.get('two_fa_secret') else ""
    notes = f"\n📝 **Notes:** {stock_item['notes']}" if stock_item.get('notes') else ""

    return f"""
✅ **Pembayaran Berhasil!**

━━━━━━━━━━━━━━━━━━━━━
📦 **Produk:** {product_name}
💰 **Total:** {format_currency(amount)}
🆔 **Order ID:** `{transaction_id}`
📅 **Tanggal:** {format_datetime(paid_at)}
━━━━━━━━━━━━━━━━━━━━━

🔑 **Detail Akun:**
📧 **Email:** `{stock_item['email']}`
🔒 **Password:** `{stock_item['password']}`{two_fa}{notes}

━━━━━━━━━━━━━━━━━━━━━

⚠️ **Penting:**
• Simpan data akun dengan baik
• Jangan bagikan kepada siapapun
• Segera ganti password setelah login

Terima kasih telah berbelanja! 🙏
"""


def format_payment_expired(
    transaction_id: str,
    product_name: str,
    amount: int
) -> str:
    """Format payment expired message."""
    return f"""
⏰ **Transaksi Kadaluarsa**

📦 **Produk:** {product_name}
💰 **Total:** {format_currency(amount)}
🆔 **Order ID:** `{transaction_id}`

Waktu pembayaran telah habis. Silakan buat pesanan baru jika masih berminat.
"""


def format_transaction_list(transactions: List[Dict]) -> str:
    """Format transaction list for history."""
    if not transactions:
        return "📜 Belum ada riwayat transaksi."

    lines = ["📜 **Riwayat Transaksi**\n"]

    for tx in transactions:
        status_emoji = {
            "PAID": "✅",
            "UNPAID": "⏳",
            "EXPIRED": "❌",
            "CANCELLED": "🚫",
            "REFUND_REQUESTED": "💰",
            "REFUNDED": "💸"
        }.get(tx["status"], "❓")

        lines.append(
            f"{status_emoji} `{tx['transaction_id'][:12]}...`\n"
            f"   📦 {tx.get('product_name', tx['product_code'])}\n"
            f"   💰 {format_currency(tx['amount'])} | {format_datetime(tx['created_at'], False)}\n"
        )

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

    return f"""
📋 **Detail Transaksi**

🆔 **Order ID:** `{tx['transaction_id']}`
📦 **Produk:** {tx.get('product_name', tx['product_code'])}
💰 **Total:** {format_currency(tx['amount'])}
📊 **Status:** {status_text}
📅 **Dibuat:** {format_datetime(tx['created_at'])}
"""


def format_stock_summary(stock_list: List[Dict], warning_threshold: float = 0.3) -> str:
    """Format stock summary for admin."""
    lines = ["📦 **Stock Summary**\n"]

    for item in stock_list:
        available = item["available"]
        total = item["total"]

        if total == 0:
            percent = 0
        else:
            percent = available / total

        if available == 0:
            emoji = "❌"
            status = " (HABIS)"
        elif percent <= 0.1:
            emoji = "🚨"
            status = " (KRITIS)"
        elif percent <= 0.3:
            emoji = "⚠️"
            status = ""
        else:
            emoji = "✅"
            status = ""

        active = "🟢" if item["is_active"] else "🔴"

        lines.append(
            f"{emoji} **{item['name']}**{status}\n"
            f"   {active} `{item['product_code']}`\n"
            f"   📊 {available}/{total} tersedia | 💰 {format_currency(item['price'])}\n"
        )

    return "\n".join(lines)


def format_stats(stats: Dict) -> str:
    """Format bot statistics for admin."""
    tx_stats = stats.get("transactions", {})

    return f"""
📊 **FRIENDS Store Statistics**

👥 **Users**
├ Total: {stats.get('total_users', 0):,}
└ Baru Hari Ini: {stats.get('new_users_today', 0):,}

💰 **Revenue**
├ Hari Ini: {format_currency(stats.get('revenue_today', 0))}
└ Total: {format_currency(stats.get('total_revenue', 0))}

📦 **Transaksi**
├ ✅ Paid: {tx_stats.get('PAID', 0):,}
├ ⏳ Pending: {tx_stats.get('UNPAID', 0):,}
├ ❌ Expired: {tx_stats.get('EXPIRED', 0):,}
└ 💸 Refunded: {tx_stats.get('REFUNDED', 0):,}
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
        f"📊 **Update Harian - {date_str}**\n",
        f"✅ Transaksi Berhasil: {paid_count}",
        f"💰 Total Penjualan: {format_currency(total_amount)}\n",
        "🛍️ **Stok Produk:**"
    ]

    low_stock = []
    for item in stock_list:
        available = item["available"]
        total = item["total"]
        percent = available / total if total > 0 else 0

        if available == 0:
            warning = " ❌"
            low_stock.append(f"• {item['name']} HABIS!")
        elif percent <= 0.1:
            warning = " 🚨"
            low_stock.append(f"• {item['name']} tinggal {available}!")
        elif percent <= 0.3:
            warning = " ⚠️"
        else:
            warning = ""

        if item["is_active"]:
            lines.append(f"• {item['name']}: {available} tersedia{warning}")

    if low_stock:
        lines.append("\n⚠️ **Peringatan Stok:**")
        lines.extend(low_stock)

    lines.append("\n🛒 Order sekarang: /start")

    return "\n".join(lines)


def format_help_order() -> str:
    """Format order guide."""
    return """
📖 **Cara Order**

1️⃣ Pilih menu **🛒 Beli Produk**
2️⃣ Pilih produk yang diinginkan
3️⃣ Klik **💳 Bayar Sekarang**
4️⃣ Scan QRIS dengan e-wallet
5️⃣ Setelah bayar, akun akan dikirim otomatis

⏰ Batas waktu pembayaran: **15 menit**

Jika ada kendala, hubungi admin.
"""


def format_help_payment() -> str:
    """Format payment guide."""
    return """
💳 **Cara Pembayaran**

Kami menggunakan **QRIS** untuk pembayaran.

**E-Wallet yang Didukung:**
• GoPay
• OVO
• Dana
• ShopeePay
• LinkAja
• Dan lainnya...

**Langkah Pembayaran:**
1️⃣ Buka aplikasi e-wallet
2️⃣ Pilih menu Scan QR
3️⃣ Scan kode QRIS
4️⃣ Konfirmasi pembayaran

⏰ **Batas Waktu:** 15 menit
⚠️ Pembayaran otomatis dibatalkan jika melewati batas waktu.
"""


def format_help_faq() -> str:
    """Format FAQ."""
    return """
❓ **FAQ Produk**

**Q: Apa yang termasuk dalam akun?**
A: Setiap akun berisi email, password, dan 2FA (jika ada).

**Q: Berapa lama akun aktif?**
A: Tergantung produk. Lihat deskripsi produk untuk info lengkap.

**Q: Bagaimana jika akun tidak bisa login?**
A: Hubungi admin untuk pengecekan dan penggantian.

**Q: Bagaimana cara pakai 2FA?**
A: Gunakan aplikasi authenticator (Google Authenticator, Authy) untuk scan secret key.

**Q: Apakah ada refund?**
A: Ya, dalam waktu 24 jam jika akun tidak sesuai deskripsi.
"""


def format_help_contact(support_username: str) -> str:
    """Format contact info."""
    return f"""
📞 **Contact Admin**

Butuh bantuan? Hubungi admin kami!

👤 **Support:** @{support_username}
⏰ **Waktu Respon:** 1-24 jam

**Saat menghubungi, sertakan:**
• Order ID (jika ada)
• Screenshot masalah
• Deskripsi kendala

Kami akan membantu secepatnya! 🙏
"""
