"""
Add Stock Wizard - Step-by-step conversation handler.
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

logger = get_logger("admin.wizard.stock")

# Conversation states
SELECT_PRODUCT, INPUT_STOCK_DATA, CONFIRM = range(3)


def validate_stock_entry(entry: str) -> tuple:
    """
    Validate stock entry format.
    Returns: (is_valid, error_msg, data_dict)
    """
    parts = entry.strip().split(":")
    
    if len(parts) < 2:
        return False, "Format harus minimal: email:password", None
    
    email = parts[0].strip()
    password = parts[1].strip()
    
    if not email or "@" not in email:
        return False, "Email tidak valid", None
    
    if not password or len(password) < 3:
        return False, "Password minimal 3 karakter", None
    
    two_fa = parts[2].strip() if len(parts) > 2 else None
    notes = parts[3].strip() if len(parts) > 3 else None
    
    return True, None, {
        "email": email,
        "password": password,
        "two_fa_secret": two_fa if two_fa else None,
        "notes": notes if notes else None
    }


class StockWizard:
    """Add stock wizard with conversation flow."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Entry point: Start add stock wizard.
        Can be triggered by:
        - Inline button: admin:stock:add
        - Reply keyboard: 📦 +Stock
        - Command: /addstock (redirects here if no args)
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
        
        # Get all active products
        products = await db.get_active_products()
        
        if not products:
            text = "❌ No products available\\. Add a product first\\."
            if query:
                await query.edit_message_text(text, parse_mode="MarkdownV2")
            else:
                await update.message.reply_text(text, parse_mode="MarkdownV2")
            return ConversationHandler.END
        
        # Store products for later
        context.user_data["wizard_products"] = products
        
        # Format product list message
        lines = [
            "*📦 Add Stock Wizard* \\(Step 1/3\\)",
            "━━━━━━━━━━━━━━━━━━━━\n",
            "*Select product:*\n"
        ]
        
        for idx, product in enumerate(products[:6], 1):
            stock_count = await db.get_available_stock_count(product["product_code"])
            stock_indicator = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"
            name = escape_md(product['name'])
            
            lines.append(f"*{idx}\\.* __{name}__")
            lines.append(f"   📊 Stock: *{stock_count}* {stock_indicator}\n")
        
        text = "\n".join(lines)
        
        # Build keyboard
        keyboard = AdminKeyboards.product_list(products, page=1, items_per_page=6, context="addstock")
        
        if query:
            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
        
        return SELECT_PRODUCT
    
    @staticmethod
    async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle product selection."""
        query = update.callback_query
        await query.answer()
        
        # Parse callback: admin:product:addstock:<product_code>:<page>
        parts = query.data.split(":")
        product_code = parts[3]
        
        # Store in context
        context.user_data["stock_wizard_product"] = product_code
        
        db: Database = context.bot_data["db"]
        product = await db.get_product(product_code)
        
        if not product:
            await query.edit_message_text("❌ Product not found\\.", parse_mode="MarkdownV2")
            return ConversationHandler.END
        
        name = escape_md(product['name'])
        
        text = (
            f"*📦 Add Stock* \\- {name}\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Step 2/3:* Enter stock data\n\n"
            "*Format:*\n"
            "`email:password:2fa_secret:notes`\n\n"
            "*Example:*\n"
            "`user@mail\\.com:pass123:JBSWY3DP:Valid Dec 2026`\n\n"
            "_2FA and notes are optional\\. Use `:` as separator\\._\n\n"
            "Type `/cancel` to abort\\."
        )
        
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2"
        )
        
        return INPUT_STOCK_DATA
    
    @staticmethod
    async def receive_stock_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate stock data."""
        stock_entry = update.message.text.strip()
        
        # Validate
        is_valid, error_msg, data = validate_stock_entry(stock_entry)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ *Invalid format*\n\n"
                f"{error_msg}\n\n"
                "Please try again:",
                parse_mode="Markdown"
            )
            return INPUT_STOCK_DATA
        
        # Store data
        context.user_data["stock_wizard_data"] = data
        
        product_code = context.user_data.get("stock_wizard_product")
        db: Database = context.bot_data["db"]
        product = await db.get_product(product_code)
        
        if not product:
            await update.message.reply_text("❌ Product not found.")
            return ConversationHandler.END
        
        # Show confirmation
        name = escape_md(product['name'])
        email = escape_md(data['email'])
        password_masked = escape_md(data['password'][:4] + '****')
        
        lines = [
            "*📦 Confirm Stock Entry*",
            "━━━━━━━━━━━━━━━━━━━━\n",
            f"*Product:* {name}",
            f"*Email:* `{email}`",
            f"*Password:* `{password_masked}`"
        ]
        
        if data.get('two_fa_secret'):
            two_fa = escape_md(data['two_fa_secret'][:6] + '...')
            lines.append(f"*2FA:* `{two_fa}`")
        
        if data.get('notes'):
            notes = escape_md(data['notes'])
            lines.append(f"*Notes:* _{notes}_")
        
        lines.append("\n*Confirm this entry?*")
        
        text = "\n".join(lines)
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="admin:stock:wizard:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin:stock:wizard:cancel")
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
        """Confirm and save stock."""
        query = update.callback_query
        await query.answer()
        
        product_code = context.user_data.get("stock_wizard_product")
        data = context.user_data.get("stock_wizard_data")
        
        if not product_code or not data:
            await query.edit_message_text("❌ Session expired\\. Please start again\\.", parse_mode="MarkdownV2")
            return ConversationHandler.END
        
        db: Database = context.bot_data["db"]
        
        try:
            # Add stock to database
            await db.add_stock_item(
                product_code=product_code,
                email=data["email"],
                password=data["password"],
                two_fa_secret=data.get("two_fa_secret"),
                notes=data.get("notes"),
                added_by=update.effective_user.id
            )
            
            # Get updated count
            stock_count = await db.get_available_stock_count(product_code)
            product = await db.get_product(product_code)
            
            name = escape_md(product['name'])
            email_short = escape_md(data['email'][:15] + '...')
            
            text = (
                "*✅ Stock Added Successfully\\!*\n\n"
                f"📦 *Product:* {name}\n"
                f"📧 *Email:* `{email_short}`\n"
                f"📊 *Total Stock:* `{stock_count}`\n\n"
                "_Add more stock or return to menu?_"
            )
            
            keyboard = AdminKeyboards.after_stock_added(product_code)
            
            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
            
            # Clear context
            StockWizard.clear_context(context)
            
            logger.info(f"Stock added: product={product_code}, email={data['email']}, by={update.effective_user.id}")
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Failed to add stock: {e}")
            await query.edit_message_text(
                f"❌ Error adding stock: {escape_md(str(e))}",
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
                "❌ Add stock cancelled\\.",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.stock_management_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Add stock cancelled\\.",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.stock_management_menu()
            )
        
        # Clear context
        StockWizard.clear_context(context)
        
        return ConversationHandler.END
    
    @staticmethod
    def clear_context(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear wizard context data."""
        context.user_data.pop("stock_wizard_product", None)
        context.user_data.pop("stock_wizard_data", None)
        context.user_data.pop("wizard_products", None)
    
    @classmethod
    def get_handler(cls) -> ConversationHandler:
        """Build conversation handler."""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(cls.start, pattern=r"^admin:stock:add$"),
                CallbackQueryHandler(cls.start, pattern=r"^admin:quick:addstock$"),
            ],
            states={
                SELECT_PRODUCT: [
                    CallbackQueryHandler(cls.product_selected, pattern=r"^admin:product:addstock:"),
                ],
                INPUT_STOCK_DATA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_stock_data)
                ],
                CONFIRM: [
                    CallbackQueryHandler(cls.confirm, pattern=r"^admin:stock:wizard:confirm$"),
                    CallbackQueryHandler(cls.cancel, pattern=r"^admin:stock:wizard:cancel$"),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cls.cancel),
                CallbackQueryHandler(cls.cancel, pattern=r"^admin:stock:wizard:cancel$"),
            ],
            name="stock_wizard",
            persistent=False,
            per_message=False
        )


# Handler export
stock_wizard_handler = StockWizard.get_handler()
