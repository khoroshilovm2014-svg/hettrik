import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Конфигурация
TOKEN = "8293709673:AAHMu6nuVCmr8mnxMGBUBo7A46KischHkm0"
MANAGER_USERNAME = "khoroshilova_anna"
ADMIN_IDS = [514807956, 7635015201]
CATALOG_FILE_PATH = "Хет-Трик_catalogue.pdf"
ORDERS_FILE = "orders.json"

# URL вашего мини-приложения (нужно задеплоить HTML файл)
# Варианты:
# 1. GitHub Pages: https://yourusername.github.io/hat-trick-catalog/
# 2. Vercel/Netlify: https://your-app.vercel.app
# 3. Локальный сервер: http://localhost:8000 (для теста)
WEBAPP_URL = "https://khoroshilovm2014-svg.github.io/hettrik/"  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ URL

def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_orders(orders):
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except:
        pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"❌ Ошибка: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "😔 Произошла ошибка. Попробуйте позже."
            )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n"
        "⚽ *Хет-Трик | Экипировка и сувениры для спортивных команд*\n\n"
        "Полный цикл брендирования для футбола и не только! Мы создаем стильную "
        "и функциональную продукцию, которая объединяет команду и работает на ее имидж.\n\n"
        "✅ *Экипировка для игроков:* Ветровки, худи, свитшоты, футболки, кепки, гетры.\n"
        "✅ *Аксессуары и сувениры:* Бутылки, шарфы, снуды, сумки, кружки.\n"
        "✅ *Наградная и печатная продукция:* Фотографии, блокноты, календари.\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📖 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL)),
            InlineKeyboardButton("🛒 Заказать", callback_data="make_order")
        ],
        [
            InlineKeyboardButton("❓ Консультация", callback_data="get_consultation"),
            InlineKeyboardButton("📞 Обратный звонок", callback_data="request_call")
        ]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Админ", callback_data="admin_panel")])

    if update.callback_query:
        await update.callback_query.message.edit_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из мини-приложения"""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user = update.effective_user
        
        # Сохраняем заказ
        order = {
            'type': 'webapp_order',
            'product': data.get('product', ''),
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'comment': data.get('comment', ''),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user_id': user.id,
            'username': user.username,
            'processed': False
        }
        
        orders = load_orders()
        orders.append(order)
        save_orders(orders)
        
        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ *Заказ из каталога принят!*\n\n"
            f"📦 *Товар:* {order['product']}\n"
            f"👤 *Имя:* {order['name']}\n"
            f"📱 *Телефон:* {order['phone']}\n\n"
            "Мы свяжемся с вами для подтверждения заказа.",
            parse_mode='Markdown'
        )
        
        # Уведомление админам
        for admin_id in ADMIN_IDS:
            try:
                admin_text = (
                    f"🔔 *НОВЫЙ ЗАКАЗ ИЗ КАТАЛОГА!*\n\n"
                    f"📦 *Товар:* {order['product']}\n"
                    f"👤 *Имя:* {order['name']}\n"
                    f"📱 *Телефон:* {order['phone']}\n"
                    f"💬 *Комментарий:* {order['comment']}\n"
                    f"📅 *Дата:* {order['date']}\n"
                    f"👤 *Пользователь:* @{user.username if user.username else 'нет username'}"
                )
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode='Markdown'
                )
            except:
                pass
    except Exception as e:
        print(f"Ошибка обработки данных веб-приложения: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке заказа. Пожалуйста, попробуйте еще раз."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if query.data == "make_order":
        context.user_data['state'] = 'waiting_name'
        context.user_data['type'] = 'order'
        await query.message.reply_text("🛒 *Оформление заказа*\n\nВведите ваше имя:", parse_mode='Markdown')

    elif query.data == "get_consultation":
        consultation_text = "❓ *Консультация*\n\nДля консультации свяжитесь с менеджером:"
        keyboard = [
            [InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]
        await query.message.edit_text(
            consultation_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif query.data == "request_call":
        context.user_data['state'] = 'waiting_name'
        context.user_data['type'] = 'callback'
        await query.message.reply_text("📞 *Обратный звонок*\n\nВведите ваше имя:", parse_mode='Markdown')

    elif query.data == "admin_panel" and user.id in ADMIN_IDS:
        await admin_panel(query, context)

    elif query.data == "back_to_main":
        await start(update, context)

    elif query.data == "admin_view_orders":
        await view_orders(query, context)

    elif query.data == "admin_stats":
        await show_stats(query, context)

    elif query.data == "admin_clear_orders":
        await clear_orders(query, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    state = user_data.get('state')
    message_text = update.message.text

    if state == 'waiting_name':
        user_data['name'] = message_text
        user_data['state'] = 'waiting_phone'
        await update.message.reply_text(f"👌 Принято, {message_text}!\nТеперь введите ваш номер телефона:")

    elif state == 'waiting_phone':
        user_data['phone'] = message_text
        order_type = user_data.get('type')

        if order_type == 'order':
            user_data['state'] = 'waiting_comment'
            await update.message.reply_text("📝 Опишите, что вы хотите заказать:")
        else:
            await save_request(update, context, user_data)

    elif state == 'waiting_comment':
        user_data['comment'] = message_text
        await save_request(update, context, user_data)

    else:
        await update.message.reply_text("🤖 Используйте кнопки меню.")

async def save_request(update, context, user_data):
    user = update.effective_user

    order = {
        'type': user_data.get('type', 'callback'),
        'name': user_data.get('name', ''),
        'phone': user_data.get('phone', ''),
        'comment': user_data.get('comment', ''),
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_id': user.id,
        'processed': False
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    if order['type'] == 'order':
        message = (
            "✅ *Ваш заказ принят!*\n\n"
            f"👤 *Имя:* {order['name']}\n"
            f"📱 *Телефон:* {order['phone']}\n"
            f"📦 *Заказ:* {order['comment']}\n\n"
            "Мы свяжемся с вами в ближайшее время для уточнения деталей."
        )
    else:
        message = (
            "✅ *Заявка на обратный звонок принята!*\n\n"
            f"👤 *Имя:* {order['name']}\n"
            f"📱 *Телефон:* {order['phone']}\n\n"
            "Мы перезвоним вам в ближайшее время."
        )

    await update.message.reply_text(message, parse_mode='Markdown')

    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            admin_text = (
                f"🔔 *НОВАЯ ЗАЯВКА!*\n\n"
                f"Тип: {'🛒 ЗАКАЗ' if order['type'] == 'order' else '📞 ЗВОНОК'}\n"
                f"Имя: {order['name']}\n"
                f"Телефон: {order['phone']}\n"
                f"Дата: {order['date']}"
            )
            if order['comment']:
                admin_text += f"\nКомментарий: {order['comment']}"

            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode='Markdown'
            )
        except:
            pass

    user_data.clear()
    await start(update, context)

async def admin_panel(query, context):
    orders = load_orders()
    new_orders = len([o for o in orders if not o.get('processed', False)])

    stats_text = (
        "⚙️ *Админ-панель*\n\n"
        f"📊 Всего заявок: {len(orders)}\n"
        f"🆕 Новых: {new_orders}"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Заявки", callback_data="admin_view_orders")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🧹 Очистить", callback_data="admin_clear_orders")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]

    await query.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def view_orders(query, context):
    orders = load_orders()

    if not orders:
        await query.message.edit_text(
            "📭 Нет заявок.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")]])
        )
        return

    recent_orders = orders[-10:][::-1]
    orders_text = "📋 *Последние заявки:*\n\n"

    for i, order in enumerate(recent_orders, 1):
        date = order.get('date', 'Не указана')
        order_type = "🛒" if order.get('type') == 'order' else "📞"
        if order.get('type') == 'webapp_order':
            order_type = "🛍️"
        orders_text += f"*{i}. {order_type}* - {date}\n"
        orders_text += f"   👤 {order.get('name')}\n"
        orders_text += f"   📱 {order.get('phone')}\n"
        if order.get('product'):
            orders_text += f"   📦 {order.get('product')}\n"
        if order.get('comment'):
            orders_text += f"   💬 {order.get('comment')}\n"
        orders_text += "\n"

    await query.message.edit_text(orders_text, parse_mode='Markdown')

async def show_stats(query, context):
    orders = load_orders()

    if not orders:
        stats_text = "📊 *Статистика*\n\nНет данных."
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in orders if o.get('date', '').startswith(today)]

        stats_text = (
            "📊 *Статистика*\n\n"
            f"📅 *Сегодня:* {len(today_orders)}\n"
            f"📈 *Всего:* {len(orders)}\n"
            f"🛒 *Обычных заказов:* {len([o for o in orders if o['type'] == 'order'])}\n"
            f"🛍️ *Из каталога:* {len([o for o in orders if o['type'] == 'webapp_order'])}\n"
            f"📞 *Звонков:* {len([o for o in orders if o['type'] == 'callback'])}"
        )

    await query.message.edit_text(stats_text, parse_mode='Markdown')

async def clear_orders(query, context):
    save_orders([])
    await query.message.edit_text("✅ Заявки очищены.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ *Справка*\n\n"
        "*Функции:*\n"
        "• 📖 Открыть каталог (интерактивный просмотр)\n"
        "• 🛒 Сделать заказ\n"
        "• ❓ Консультация\n"
        "• 📞 Обратный звонок\n\n"
        "*Команды:*\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/contacts - Контакты"
    )

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts_text = (
        "📞 *Контакты*\n\n"
        f"💬 *Менеджер:* @{MANAGER_USERNAME}\n"
        "🔧 *Техподдержка:* @mixan2907"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Менеджер", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton("🔧 Техподдержка", url="https://t.me/mixan2907")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]

    await update.message.reply_text(
        contacts_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMIN_IDS:
        orders = load_orders()
        new_orders = len([o for o in orders if not o.get('processed', False)])

        admin_text = (
            f"⚙️ *Админ-панель*\n\n"
            f"📊 *Заявок:* {len(orders)}\n"
            f"🆕 *Новых:* {new_orders}"
        )

        keyboard = [
            [InlineKeyboardButton("📋 Заявки", callback_data="admin_view_orders")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🧹 Очистить", callback_data="admin_clear_orders")],
            [InlineKeyboardButton("🏠 Назад", callback_data="back_to_main")]
        ]

        await update.message.reply_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("⛔ Нет доступа.")

def main():
    # Создаем файл orders.json если его нет
    if not os.path.exists(ORDERS_FILE):
        save_orders([])

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contacts", contacts_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # Добавляем обработчик веб-приложения (Mini App)
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    # Добавляем обработчик callback-запросов (кнопки)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    print("=" * 60)
    print("✅ БОТ ХЕТ-ТРИК ЗАПУЩЕН!")
    print(f"👤 Менеджер: @{MANAGER_USERNAME}")
    print(f"👑 Админы: {ADMIN_IDS}")
    print("=" * 60)
    print("📱 Mini App каталог активирован!")
    print(f"🔗 URL: {WEBAPP_URL}")
    print("=" * 60)
    print("🔄 Нажмите Ctrl+C для остановки")
    print("=" * 60)

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")