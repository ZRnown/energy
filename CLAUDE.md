# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot for TRON energy rental services (能量租赁机器人). The bot automates energy rental transactions on the TRON blockchain, monitors wallet transactions, processes orders through multiple energy platforms, and sends notifications to users.

**Primary Language:** Python 3
**Framework:** python-telegram-bot (v20+)
**Database:** MySQL
**Blockchain:** TRON (TRX/USDT)

## Development Commands

### Setup and Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
mysql -u root -p < database_schema.sql

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Running the Bot

```bash
# Start the bot (production)
python run_bot.py

# Test mode (validates configuration without starting)
python run_bot.py --test

# Verbose output
python run_bot.py --verbose
```

### Environment Variables

Required variables in `.env`:
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - MySQL database credentials
- `TRON_API_KEY_1/2/3` - TronScan API keys for transaction monitoring
- `GRID_API_KEY_1/2/3` - TronGrid API keys for USDT transactions
- `TELEGRAM_ADMIN_UID` - Admin user ID for management features (optional)

## Architecture Overview

### Core Components

The bot follows a layered architecture with clear separation of concerns:

**1. Bot Layer** (`energy_rental_bot/bot/`)
- `energy_bot.py` - Main bot class (`EnergyRentalBot`)
- Handles Telegram interactions, command routing, and callback queries
- Manages user state for multi-step interactions
- Runs background task scheduler loop

**2. Controllers** (`energy_rental_bot/controllers/`)
- `energy_controller.py` - HTTP callback handlers (e.g., `TrongasIoController`)
- Processes webhook notifications from external energy platforms
- Handles energy delivery confirmations

**3. Services** (`energy_rental_bot/services/`)
- `energy_services.py` - Business logic for wallet and transaction management
- `EnergyWalletServices` - Manages wallet configurations
- `EnergyWalletTradeTrxServices` - Fetches TRX transactions from TronScan
- `EnergyWalletTradeUsdtServices` - Fetches USDT transactions from TronGrid

**4. Models** (`energy_rental_bot/models/`)
- `base_model.py` - Base database model with common CRUD operations
- `energy_models.py` - Domain models for all database tables:
  - `EnergyAiBishuModel` - Per-transaction package management
  - `EnergyAiTrusteeshipModel` - AI-managed energy托管
  - `EnergyWalletTradeListModel` - Transaction records
  - `EnergyPlatformModel` - Energy platform configurations
  - Platform bot and order models

**5. Tasks** (`energy_rental_bot/tasks/`)
Background tasks executed on schedule:
- `get_energy_wallet_trx_trade_task.py` - Polls TRX/USDT transactions (every minute)
- `handle_energy_order_task.py` - Processes pending energy orders (every minute)
- `handle_ai_energy_order_task.py` - Handles AI托管 orders (every 10 minutes)
- `send_energy_tg_message_task.py` - Sends Telegram notifications (every minute)
- `get_ai_trusteeship_wallet_resource_task.py` - Monitors wallet energy levels

**6. Configuration** (`energy_rental_bot/config/`)
- `config.py` - Centralized configuration loaded from environment variables
- Defines `TELEGRAM_CONFIG`, `TRON_CONFIG`, `TASK_CONFIG`, `ENERGY_RENT_CONFIG`, `BISHA_CONFIG`

**7. Utilities** (`energy_rental_bot/utils/`)
- `energy_utils.py` - Helper functions for logging, HTTP requests, address formatting, time conversions

### Data Flow

1. **Transaction Monitoring**: Background tasks poll TronScan/TronGrid APIs for incoming TRX/USDT transfers to monitored wallets
2. **Order Processing**: Detected transactions are matched to user configurations (笔数套餐 or 托管模式)
3. **Energy Purchase**: Orders are submitted to energy platforms (nee.cc, RentEnergysBot, trongas.io, or self-staking)
4. **Notification**: Users receive Telegram messages when energy is delivered
5. **User Interaction**: Users interact via Telegram commands and inline keyboards to configure services

### Background Task Scheduling

The bot uses a custom async scheduler loop (not APScheduler due to timezone issues):
- **Every 5 seconds**: Check if minute/10-minute tasks should run
- **Every minute**: Transaction polling, order processing, notifications
- **Every 10 minutes**: AI托管 resource checks and order handling

Tasks run in thread pool executors to avoid blocking the Telegram bot's event loop.

## Database Schema

Key tables (see `database_schema.sql` for full schema):

- `energy_ai_bishu` - Per-transaction packages (笔数套餐)
- `energy_ai_trusteeship` - AI-managed托管 configurations
- `energy_wallet_trade_list` - All incoming TRX/USDT transactions
- `energy_platform` - Energy provider platforms
- `energy_platform_bot` - Bot-to-platform mappings
- `energy_platform_package` - Available energy packages per platform
- `energy_platform_order` - Order history

## Key Design Patterns

### User State Management
The bot maintains in-memory user states (`self.user_states`) for multi-step flows like wallet address input. States are cleared after completion or cancellation.

### API Key Rotation
TRON API keys are rotated using `EnergyUtils.get_random_api_key()` to avoid rate limiting across multiple TronScan and TronGrid keys.

### Async/Sync Hybrid
- Telegram handlers are async (`async def`)
- Background tasks are sync but run in thread pool executors via `loop.run_in_executor()`
- Database operations are synchronous (PyMySQL)

### Configuration-Driven
Service parameters (prices, packages, wallets) are defined in `config.py` and referenced throughout the codebase, making it easy to adjust business logic without code changes.

## Important Implementation Notes

### Telegram Bot Initialization
- The bot disables `job_queue` to avoid timezone issues with APScheduler
- Proxy environment variables are explicitly cleared in `initialize()`
- Uses `run_polling()` which handles SIGINT/SIGTERM automatically

### Transaction Processing
- Transactions are deduplicated by `tx_hash` before insertion
- Only successful transactions (`contractRet == 'SUCCESS'`) are processed
- Minimum transaction amount is 1 TRX/USDT

### Error Handling
- Each background task has try-except wrappers to prevent one failure from stopping the scheduler
- Errors are logged but don't crash the bot
- HTTP requests use `EnergyUtils.send_http_request()` with built-in error handling

### Notification System
- Supports both user notifications (`tg_uid`) and group notifications (`tg_notice_obj_send`)
- Uses Telegram Bot API directly via HTTP for notifications (not python-telegram-bot library)
- Inline keyboards provide quick actions in messages

## Common Development Workflows

### Adding a New Command
1. Add command handler in `_register_handlers()` in `energy_bot.py`
2. Implement handler method (e.g., `async def _handle_new_command()`)
3. Update help text in `_handle_help()` if user-facing

### Adding a New Background Task
1. Create task file in `energy_rental_bot/tasks/`
2. Implement `execute()` method (synchronous)
3. Add task execution to `_execute_minute_logic()` or `_execute_ten_minute_logic()` in `energy_bot.py`
4. Update `TASK_CONFIG['intervals']` in `config.py` if needed

### Adding a New Energy Platform
1. Add platform configuration to `PLATFORM_CONFIG` in `config.py`
2. Insert platform record into `energy_platform` table
3. Implement platform-specific API integration in services or tasks
4. Update order processing logic to route to new platform

### Modifying Database Schema
1. Update `database_schema.sql` with ALTER statements
2. Update corresponding model class in `energy_models.py`
3. Test with `python run_bot.py --test` to verify database connectivity

## Testing and Debugging

### Test Mode
```bash
python run_bot.py --test
```
This validates:
- Environment variables are set
- Database connection works
- Bot token is valid
- Bot initializes without errors

### Logging
Logs are written to `/tmp/energy_rental_bot.log` (configurable in `LOG_CONFIG`).

Key loggers:
- `energy_rental_bot.bot.energy_bot` - Bot lifecycle events
- `energy_rental_bot.tasks.*` - Background task execution
- `telegram` - Telegram library logs (set to INFO)
- `httpx` - HTTP client logs (set to WARNING)

### Common Issues

**Bot not receiving updates**: Check that `run_polling()` is called and no proxy issues exist.

**Background tasks not running**: Verify scheduler loop started in `_post_init()`. Check logs for task exceptions.

**Database connection errors**: Ensure MySQL is running and credentials in `.env` are correct.

**API rate limiting**: Add more API keys to `TRON_API_KEY_*` and `GRID_API_KEY_*` in `.env`.

## Security Considerations

- Never commit `.env` file (already in `.gitignore`)
- Bot tokens and API keys are loaded from environment variables only
- Database credentials are not hardcoded
- Admin commands check `TELEGRAM_ADMIN_UID` before execution
- Wallet addresses are validated before processing (34 characters, starts with 'T')

## Code Style and Conventions

- Chinese comments and docstrings are used throughout (original project language)
- Class names use PascalCase (e.g., `EnergyRentalBot`)
- Method names use snake_case (e.g., `_handle_start`)
- Private methods prefixed with underscore
- Database field names use snake_case matching SQL schema
- Configuration constants use UPPER_SNAKE_CASE
