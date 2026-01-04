"""
Add Product Wizard - Step-by-step conversation handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters
)

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.formatters import format_currency, escape_md
from utils.logger import get_logger

logger = get_logger("admin.wizard.product")

# Conversation states
INPUT_CODE, INPUT_NAME, INPUT_DESCRIPTION, INPUT_PRICE, CONFIRM = range(5)


class ProductWizard:
    """Add product wizard with conversation flow."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Entry point: Start add product wizard.
        Can be triggered by:
        - Inline button: admin:product:add
        - Command: /addproduct (redirects here if no args)
        """
        query = update.callback_query
        if query:
            await query.answer()
        
        user = update.effective_user
        db: Database = context.bot_data["db"]
        
        # Check admin
        if not await db.is_admin(user.id):
            text = "⛔ Access denied\\."
            if query:
                await query.edit_message_text(text, parse_mode="MarkdownV2")
            else:
                await update.message.reply_text(text, parse_mode="MarkdownV2")
            return ConversationHandler.END
        
        # Clear any existing wizard data
        ProductWizard.clear_context(context)
        
        text = (
            "*🛍️ Add Product Wizard* \\(Step 1/5\\)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Enter product code:*\n\n"
            "_Use lowercase, underscore allowed\\._\n"
            "_Example: `github_student_fresh`_\n\n"
            "Type `/cancel` to abort\\."
        )
        
        if query:
            await query.edit_message_text(text, parse_mode="MarkdownV2")
        else:
            await update.message.reply_text(text, parse_mode="MarkdownV2")
        
        return INPUT_CODE
    
    @staticmethod
    async def receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate product code."""
        code = update.message.text.strip().lower().replace(" ", "_")
        
        # Validate code
        if not code or len(code) < 3:
            await update.message.reply_text(
                "❌ Product code minimal 3 karakter\\.\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_CODE
        
        if not code.replace("_", "").isalnum():
            await update.message.reply_text(
                "❌ Code hanya boleh huruf, angka, dan underscore\\.\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_CODE
        
        # Check if already exists
        db: Database = context.bot_data["db"]
        existing = await db.get_product(code)
        
        if existing:
            await update.message.reply_text(
                f"❌ Product code `{escape_md(code)}` sudah ada\\!\n\nGunakan code lain:",
                parse_mode="MarkdownV2"
            )
            return INPUT_CODE
        
        # Store code
        context.user_data["product_wizard_code"] = code
        
        text = (
            f"✅ Product code: `{escape_md(code)}`\n\n"
            "*Step 2/5:* Masukkan nama produk:\n\n"
            "_Contoh: GitHub Student Developer Pack_"
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        
        return INPUT_NAME
    
    @staticmethod
    async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive product name."""
        name = update.message.text.strip()
        
        if not name or len(name) < 3:
            await update.message.reply_text(
                "❌ Nama produk minimal 3 karakter\\.\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_NAME
        
        if len(name) > 100:
            await update.message.reply_text(
                "❌ Nama produk maksimal 100 karakter\\.\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_NAME
        
        # Store name
        context.user_data["product_wizard_name"] = name
        
        text = (
            f"✅ Nama: *{escape_md(name)}*\n\n"
            "*Step 3/5:* Masukkan deskripsi produk:\n\n"
            "_Contoh: Akun GitHub Student dengan akses ke berbagai tools premium\\._"
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        
        return INPUT_DESCRIPTION
    
    @staticmethod
    async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive product description."""
        description = update.message.text.strip()
        
        if not description or len(description) < 10:
            await update.message.reply_text(
                "❌ Deskripsi minimal 10 karakter\\.\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_DESCRIPTION
        
        # Store description
        context.user_data["product_wizard_desc"] = description
        
        text = (
            f"✅ Deskripsi: _{escape_md(description[:50])}\\.\\.\\._\n\n"
            "*Step 4/5:* Masukkan harga \\(Rupiah\\):\n\n"
            "_Contoh: `50000` atau `50.000`_"
        )
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        
        return INPUT_PRICE
    
    @staticmethod
    async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate price."""
        price_text = update.message.text.strip().replace(".", "").replace(",", "")
        
        try:
            price = int(price_text)
            if price < 1000:
                raise ValueError("Price too low")
            if price > 100000000:
                raise ValueError("Price too high")
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ Harga tidak valid\\. Masukkan angka antara 1\\.000 \\- 100\\.000\\.000\n\nCoba lagi:",
                parse_mode="MarkdownV2"
            )
            return INPUT_PRICE
        
        # Store price
        context.user_data["product_wizard_price"] = price
        
        # Show confirmation
        code = context.user_data.get("product_wizard_code")
        name = context.user_data.get("product_wizard_name")
        desc = context.user_data.get("product_wizard_desc")
        
        text = (
            "*📦 Confirm New Product*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Code:* `{escape_md(code)}`\n"
            f"*Name:* {escape_md(name)}\n"
            f"*Price:* `{escape_md(format_currency(price))}`\n\n"
            f"*Description:*\n_{escape_md(desc)}_\n\n"
            "*Confirm to add this product?*"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="admin:product:wizard:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin:product:wizard:cancel")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CONFIRM
    
    @staticmethod
    async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Confirm and save product."""
        query = update.callback_query
        await query.answer()
        
        code = context.user_data.get("product_wizard_code")
        name = context.user_data.get("product_wizard_name")
        desc = context.user_data.get("product_wizard_desc")
        price = context.user_data.get("product_wizard_price")
        
        if not all([code, name, desc, price]):
            await query.edit_message_text(
                "❌ Session expired\\. Please start again\\.",
                parse_mode="MarkdownV2"
            )
            return ConversationHandler.END
        
        db: Database = context.bot_data["db"]
        
        try:
            # Add product to database
            await db.add_product(
                product_code=code,
                name=name,
                description=desc,
                price=price
            )
            
            text = (
                "*✅ Product Added Successfully\\!*\n\n"
                f"📦 *Code:* `{escape_md(code)}`\n"
                f"🏷️ *Name:* {escape_md(name)}\n"
                f"💰 *Price:* `{escape_md(format_currency(price))}`\n\n"
                "_Add stock or return to menu?_"
            )
            
            keyboard = AdminKeyboards.after_product_added(code)
            
            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
            
            # Clear context
            ProductWizard.clear_context(context)
            
            logger.info(f"Product added: code={code}, name={name}, price={price}, by={update.effective_user.id}")
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Failed to add product: {e}")
            await query.edit_message_text(
                f"❌ Error adding product: {escape_md(str(e))}",
                parse_mode="MarkdownV2"
            )
            return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel wizard."""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ Add product cancelled\\.",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.product_management_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Add product cancelled\\.",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.product_management_menu()
            )
        
        # Clear context
        ProductWizard.clear_context(context)
        
        return ConversationHandler.END
    
    @staticmethod
    def clear_context(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear wizard context data."""
        context.user_data.pop("product_wizard_code", None)
        context.user_data.pop("product_wizard_name", None)
        context.user_data.pop("product_wizard_desc", None)
        context.user_data.pop("product_wizard_price", None)
    
    @classmethod
    def get_handler(cls) -> ConversationHandler:
        """Build conversation handler."""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(cls.start, pattern=r"^admin:product:add$"),
            ],
            states={
                INPUT_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_code)
                ],
                INPUT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_name)
                ],
                INPUT_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_description)
                ],
                INPUT_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_price)
                ],
                CONFIRM: [
                    CallbackQueryHandler(cls.confirm, pattern=r"^admin:product:wizard:confirm$"),
                    CallbackQueryHandler(cls.cancel, pattern=r"^admin:product:wizard:cancel$"),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cls.cancel),
                CallbackQueryHandler(cls.cancel, pattern=r"^admin:product:wizard:cancel$"),
            ],
            name="product_wizard",
            persistent=False,
            per_message=False
        )


# Handler export
product_wizard_handler = ProductWizard.get_handler()
