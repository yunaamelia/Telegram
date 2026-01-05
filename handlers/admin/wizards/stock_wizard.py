"""
Add Stock Wizard - Step-by-step conversation handler.
"""

from database.db import Database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

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

    return (
        True,
        None,
        {
            "email": email,
            "password": password,
            "two_fa_secret": two_fa if two_fa else None,
            "notes": notes if notes else None,
        },
    )


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
            text = "⛔ Access denied."
            if query:
                await query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return ConversationHandler.END

        # Get all active products
        products = await db.get_active_products()

        if not products:
            text = "❌ No products available. Add a product first."
            if query:
                await query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return ConversationHandler.END

        # Store products for later
        context.user_data["wizard_products"] = products

        # Format product list message
        lines = [
            f"{vs.header('Add Stock Wizard (Step 1/3)', '', icon='📦')}",
            f"\n{uf.bold('Select product:')}\n",
        ]

        for idx, product in enumerate(products[:6], 1):
            stock_count = await db.get_available_stock_count(product["product_code"])
            stock_indicator = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"

            lines.append(f"{uf.bold(f'{idx}.')} {product['name']}")
            lines.append(f"   📊 Stock: {uf.bold(str(stock_count))} {stock_indicator}")

        text = "\n".join(lines)

        # Build keyboard
        keyboard = AdminKeyboards.product_list(products, page=1, items_per_page=6, context="addstock")

        if query:
            await query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)

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
            await query.edit_message_text("❌ Product not found.")
            return ConversationHandler.END

        name = product["name"]

        text = f"{vs.header(f'Add Stock - {name}', '', icon='📦')}\n\n"
        text += f"{uf.bold('Step 2/3:')} Enter stock data\n\n"
        text += f"{uf.bold('Format:')}\n"
        text += f"{uf.monospace('email:password:2fa_secret:notes')}\n\n"
        text += f"{uf.bold('Example:')}\n"
        text += f"{uf.monospace('user@mail.com:pass123:JBSWY3DP:Valid Dec 2026')}\n\n"
        text += f"{uf.italic('2FA and notes are optional. Use : as separator.')}\n\n"
        text += "Type /cancel to abort."

        await query.edit_message_text(text)

        return INPUT_STOCK_DATA

    @staticmethod
    async def receive_stock_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receive and validate stock data."""
        stock_entry = update.message.text.strip()

        # Validate
        is_valid, error_msg, data = validate_stock_entry(stock_entry)

        if not is_valid:
            await update.message.reply_text(f"❌ {uf.bold('Invalid format')}\n\n{error_msg}\n\nPlease try again:")
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
        name = product["name"]
        password_masked = data["password"][:4] + "****"

        lines = [
            f"{vs.header('Confirm Stock Entry', '', icon='📦')}",
            f"\n{uf.bold('Product:')} {name}",
            f"{uf.bold('Email:')} {uf.monospace(data['email'])}",
            f"{uf.bold('Password:')} {uf.monospace(password_masked)}",
        ]

        if data.get("two_fa_secret"):
            two_fa = data["two_fa_secret"][:6] + "..."
            lines.append(f"{uf.bold('2FA:')} {uf.monospace(two_fa)}")

        if data.get("notes"):
            lines.append(f"{uf.bold('Notes:')} {uf.italic(data['notes'])}")

        lines.append(f"\n{uf.bold('Confirm this entry?')}")

        text = "\n".join(lines)

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="admin:stock:wizard:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin:stock:wizard:cancel"),
            ]
        ]

        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

        return CONFIRM

    @staticmethod
    async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Confirm and save stock."""
        query = update.callback_query
        await query.answer()

        product_code = context.user_data.get("stock_wizard_product")
        data = context.user_data.get("stock_wizard_data")

        if not product_code or not data:
            await query.edit_message_text("❌ Session expired. Please start again.")
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
                added_by=update.effective_user.id,
            )

            # Get updated count
            stock_count = await db.get_available_stock_count(product_code)
            product = await db.get_product(product_code)

            name = product["name"]
            email_short = data["email"][:15] + "..."

            text = f"✅ {uf.bold('Stock Added Successfully!')}\n\n"
            text += f"📦 {uf.bold('Product:')} {name}\n"
            text += f"📧 {uf.bold('Email:')} {uf.monospace(email_short)}\n"
            text += f"📊 {uf.bold('Total Stock:')} {uf.monospace(str(stock_count))}\n\n"
            text += f"{uf.italic('Add more stock or return to menu?')}"

            keyboard = AdminKeyboards.after_stock_added(product_code)

            await query.edit_message_text(text, reply_markup=keyboard)

            # Clear context
            StockWizard.clear_context(context)

            logger.info(
                f"Stock added: product={product_code}, " f"email={data['email']}, by={update.effective_user.id}"
            )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Failed to add stock: {e}")
            await query.edit_message_text(f"❌ Error adding stock: {str(e)}")
            return ConversationHandler.END

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel wizard."""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ Add stock cancelled.",
                reply_markup=AdminKeyboards.stock_management_menu(),
            )
        else:
            await update.message.reply_text(
                "❌ Add stock cancelled.",
                reply_markup=AdminKeyboards.stock_management_menu(),
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
                MessageHandler(filters.Regex("^📦 Add Stock$"), cls.start),
            ],
            states={
                SELECT_PRODUCT: [
                    CallbackQueryHandler(cls.product_selected, pattern=r"^admin:product:addstock:"),
                ],
                INPUT_STOCK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.receive_stock_data)],
                CONFIRM: [
                    CallbackQueryHandler(cls.confirm, pattern=r"^admin:stock:wizard:confirm$"),
                    CallbackQueryHandler(cls.cancel, pattern=r"^admin:stock:wizard:cancel$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cls.cancel),
                CallbackQueryHandler(cls.cancel, pattern=r"^admin:stock:wizard:cancel$"),
            ],
            name="stock_wizard",
            persistent=False,
            per_message=False,
        )


# Handler export
stock_wizard_handler = StockWizard.get_handler()
