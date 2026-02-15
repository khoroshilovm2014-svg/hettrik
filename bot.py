import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# Загружаем файл каталога в память при запуске
_catalog_data = None
if os.path.exists(CATALOG_FILE_PATH):
    with open(CATALOG_FILE_PATH, 'rb') as f:
        _catalog_data = f.read()

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
            InlineKeyboardButton("📥 Скачать каталог", callback_data="download_catalog"),
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "download_catalog":
        if _catalog_data:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=_catalog_data,
                filename="Каталог Хет-Трик.pdf",
                caption="📚 *Каталог продукции Хет-Трик*",
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("💬 Менеджер", url=f"https://t.me/{MANAGER_USERNAME}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]
            await query.message.edit_text(
                "📚 Каталог временно недоступен.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == "make_order":
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
            # Сохраняем заявку на звонок
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
    
    # Очищаем данные
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
    
    recent_orders = orders[-5:][::-1]
    orders_text = "📋 *Заявки:*\n\n"
    
    for i, order in enumerate(recent_orders, 1):
        date = order.get('date', 'Не указана')
        order_type = "🛒" if order.get('type') == 'order' else "📞"
        orders_text += f"*{i}. {order_type}* - {date}\n"
        orders_text += f"   👤 {order.get('name')}\n"
        orders_text += f"   📱 {order.get('phone')}\n"
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
            f"🛒 *Заказы:* {len([o for o in orders if o['type'] == 'order'])}\n"
            f"📞 *Звонки:* {len([o for o in orders if o['type'] == 'callback'])}"
        )
    
    await query.message.edit_text(stats_text, parse_mode='Markdown')

async def clear_orders(query, context):
    save_orders([])
    await query.message.edit_text("✅ Заявки очищены.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ *Справка*\n\n"
        "*Функции:*\n"
        "• Скачать каталог\n"
        "• Сделать заказ\n"
        "• Консультация\n"
        "• Обратный звонок\n\n"
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
    if not os.path.exists(ORDERS_FILE):
        save_orders([])
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contacts", contacts_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print("✅ БОТ ХЕТ-ТРИК ЗАПУЩЕН!")
    print(f"👤 Менеджер: @{MANAGER_USERNAME}")
    print(f"👑 Админы: {ADMIN_IDS}")
    print("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()