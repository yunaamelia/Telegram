"""
Help center handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config import config
from utils.keyboards import Keyboards
from utils.messages import safe_edit_or_send
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

# Help content with Unicode fonts
HELP_MAIN = f"""
{vs.header('Pusat Bantuan', 'Pilih kategori bantuan', icon='❓')}

Pilih kategori di bawah untuk melihat panduan.
"""


def get_help_order() -> str:
    """Get order guide with Unicode fonts."""
    return f"""
{vs.header('Cara Order', 'Panduan pemesanan', icon='📖')}

{uf.bold('1.')} Pilih menu {uf.sans('🛒 Beli')}
{uf.bold('2.')} Pilih produk yang diinginkan
{uf.bold('3.')} Klik {uf.sans('💳 Bayar Sekarang')}
{uf.bold('4')} Lakukan pembayaran via QRIS
{uf.bold('5.')} Akun akan dikirim otomatis

{vs.tag('Instant Delivery', 'success')}
"""


def get_help_payment() -> str:
    """Get payment guide with Unicode fonts."""
    return f"""
{vs.header('Cara Pembayaran', 'Panduan pembayaran', icon='💳')}

{uf.bold('Metode Pembayaran:')}
• QRIS (scan dengan e-wallet/m-banking)

{uf.bold('Langkah-langkah:')}
{uf.bold('1.')} Scan QR code yang muncul
{uf.bold('2.')} Bayar sesuai nominal
{uf.bold('3.')} Klik {uf.sans('✅ Sudah Bayar')}
{uf.bold('4.')} Tunggu verifikasi otomatis

{vs.alert('Pembayaran akan expired dalam 30 menit', 'warning')}
"""


def get_help_faq() -> str:
    """Get FAQ with Unicode fonts."""
    return f"""
{vs.header('FAQ', 'Pertanyaan yang sering ditanyakan', icon='❓')}

{uf.bold('Q: Berapa lama akun dikirim?')}
A: Akun dikirim otomatis setelah pembayaran terverifikasi (1-5 menit).

{uf.bold('Q: Bagaimana jika akun bermasalah?')}
A: Hubungi support kami untuk penggantian.

{uf.bold('Q: Apakah bisa refund?')}
A: Ya, dalam 24 jam jika akun tidak sesuai deskripsi.

{uf.bold('Q: Pembayaran sudah tapi belum dapat akun?')}
A: Gunakan menu {uf.sans('💳 Cek Bayar')} atau hubungi support.
"""


def get_help_contact(support_username: str) -> str:
    """Get contact info with Unicode fonts."""
    return f"""
{vs.header('Hubungi Kami', 'Customer Support', icon='📞')}

{uf.bold('Support:')} @{support_username}
{uf.bold('Jam Operasional:')} 09:00 - 22:00 WIB

{vs.alert('Response time: 5-15 menit', 'info')}

{uf.italic('Sertakan ID transaksi saat menghubungi support.')}
"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        text=HELP_MAIN,
        reply_markup=Keyboards.help_categories()
    )


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu (callback)."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=HELP_MAIN,
        reply_markup=Keyboards.help_categories()
    )


async def show_help_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show order guide."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=get_help_order(),
        reply_markup=Keyboards.help_back()
    )


async def show_help_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show payment guide."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=get_help_payment(),
        reply_markup=Keyboards.help_back()
    )


async def show_help_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=get_help_faq(),
        reply_markup=Keyboards.help_back()
    )


async def show_help_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show contact info."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=get_help_contact(config.bot.support_username),
        reply_markup=Keyboards.help_back()
    )


# Handler exports
help_handlers = [
    CommandHandler("help", help_command),
    CallbackQueryHandler(show_help_menu, pattern=r"^nav:help$"),
    CallbackQueryHandler(show_help_order, pattern=r"^help:order$"),
    CallbackQueryHandler(show_help_payment, pattern=r"^help:payment$"),
    CallbackQueryHandler(show_help_faq, pattern=r"^help:faq$"),
    CallbackQueryHandler(show_help_contact, pattern=r"^help:contact$"),
]
