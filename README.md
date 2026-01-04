# FRIENDS Store Telegram Bot

A fully automated Telegram bot for selling premium digital accounts with integrated Midtrans QRIS payment system.

## Features

- 🛒 **Automated Sales** - Complete purchase flow with QRIS payment
- 💳 **Midtrans Integration** - Support for all major e-wallets (GoPay, OVO, Dana, etc.)
- 📦 **Stock Management** - Single/bulk stock upload, auto-disable on empty
- 👤 **User Management** - History, refunds, ban system
- 🔔 **Admin Tools** - Dashboard, broadcast, transactions, security
- ⏰ **Scheduled Jobs** - Daily broadcast, auto-backup, expiry checker
- 🔒 **Security** - Rate limiting, signature validation, IP whitelist

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Midtrans Account (sandbox or production)

### Installation

```bash
# Clone repository
cd /home/racoon/telegram

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials

# Run setup
python setup.py

# Start bot
python main.py
```

### Configuration

Edit `.env` with your settings:

```bash
BOT_TOKEN=your-telegram-bot-token
SUPER_ADMIN_ID=your-telegram-user-id
MIDTRANS_SERVER_KEY=your-midtrans-server-key
MIDTRANS_CLIENT_KEY=your-midtrans-client-key
WEBHOOK_URL=https://yourdomain.com/webhook/midtrans
```

## User Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & main menu |
| `/help` | Help center with guides |
| `/history` | Transaction history |
| `/cancel` | Cancel current operation |

## Admin Commands

### Stock Management
- `/addstock <code> <email:pass:2fa:notes>` - Add single stock
- `/checkstock` - View stock summary
- `/stockdetails <code>` - View stock details

### Product Management
- `/addproduct` - Add product wizard
- `/editproduct <code> <field> <value>` - Edit product
- `/deleteproduct <code>` - Disable product
- `/listproducts` - List all products

### Transactions
- `/transactions [status]` - View transactions
- `/refunds` - Pending refund requests
- `/approverefund <id>` - Approve refund
- `/rejectrefund <id> <reason>` - Reject refund

### System (Admin)
- `/stats` - Bot statistics
- `/logs [lines]` - View logs
- `/backupdb` - Manual backup
- `/broadcast` - Send broadcast

### Security
- `/ban <user_id> <reason>` - Ban user
- `/unban <user_id>` - Unban user
- `/banlist` - View banned users
- `/security` - Security dashboard

### Super Admin Only
- `/addadmin <user_id>` - Add admin
- `/removeadmin <user_id>` - Remove admin
- `/listadmin` - List admins

## Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed Debian 13 VPS deployment guide.

```bash
# Quick deploy
sudo cp deployment/systemd/telegram-bot.service /etc/systemd/system/
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

## Project Structure

```
telegram/
├── main.py              # Entry point
├── config.py            # Configuration
├── setup.py             # First-time setup
├── database/            # Database layer
├── handlers/            # Bot handlers
│   ├── user/           # User commands
│   └── admin/          # Admin commands
├── services/            # Business logic
├── webhook/             # Webhook server
├── jobs/               # Scheduled tasks
├── utils/              # Utilities
└── deployment/         # Deploy configs
```

## License

MIT License
