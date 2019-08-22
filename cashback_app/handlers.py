import re
from random import randint

import telebot
from admitad import api

from django.conf import settings
from django.db.models import Count

from preferences import preferences

from cashback_app import models
from cashback_app import shortcuts

from tickets.bot import handle_message_from_user

bot = telebot.TeleBot(settings.TOKEN, threaded=False)
bot_username = bot.get_me().username

scope = 'deeplink_generator'
client = api.get_oauth_client_client(
    settings.CLIENT_ID,
    settings.CLIENT_SECRET,
    scope
)

SHOPS_PER_PAGE = 10


@bot.message_handler(commands=['start'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('start', 'Команда /start')
def start(message, user):
    if not user.last_printable_action:
        if len(message.text.split()) > 1:
            code = int(message.text.split()[1])
            inviter = models.User.objects.get(first_referral_id=code)
            user.inviter = inviter
            user.save()

    for index in range(4):
        text = getattr(preferences.Texts, f'start_message_{index}')
        photo = getattr(preferences.Texts, f'start_photo_{index}')

        if photo:
            url = 'https://' + settings.ALLOWED_HOSTS[0] + '/media/' + str(photo)
            bot.send_photo(message.chat.id,
                photo=url,
                caption=text,
                parse_mode='html'
            )

        elif text:
            bot.send_message(message.chat.id,
                text=text,
                parse_mode='html'
            )


@bot.message_handler(commands=['help'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('help', 'Команда /help')
def help(message, user):
    bot.send_message(message.chat.id,
        text=preferences.Texts.help_message,
        parse_mode='html'
    )


@bot.message_handler(commands=['search'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('search', 'Команда /search')
def search(message, user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton(
        text=preferences.Texts.search_button,
        switch_inline_query_current_chat=''
    )
    keyboard.add(button)

    bot.send_message(message.chat.id,
        text=preferences.Texts.search_message,
        parse_mode='html',
        reply_markup=keyboard
    )


def search_by_text(text):
    shops = models.Shop.objects.filter(done=True).order_by('command')

    result = []

    for shop in shops:
        if max(
            shortcuts.compare(text.lower(), shop.name[:len(text)].lower()),
            shortcuts.compare(text.lower(), shop.name_rus[:len(text)].lower())
        ) >= 0.5:
            result.append(shop)

    return result


def generate_page_text(shops):
    text = ''

    for shop in shops:
        text += f'<b>{shop.name}</b>\n'
        text += f'Кэшбэк до {float(shop.percent * shop.client_percent / 100)}%\n'
        text += f'Подробнее: {shop.command}\n'
        text += '\n'

    return text


def generate_page_keyboard(page, length, query):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)

    pages = (length - 1) // SHOPS_PER_PAGE + 1

    if pages != 1:
        buttons = []

        if page > 0:
            buttons.append(
                telebot.types.InlineKeyboardButton(
                    text='<',
                    callback_data=f'page_{page - 1}__{query}'
                )
            )

        buttons.append(
            telebot.types.InlineKeyboardButton(
                text=f'{page + 1} / {pages}',
                callback_data='do_nothing'
            )
        )

        if page + 1 < pages:
            buttons.append(
                telebot.types.InlineKeyboardButton(
                    text='>',
                    callback_data=f'page_{page + 1}__{query}'
                )
            )

        keyboard.add(*buttons)

    return keyboard


@bot.callback_query_handler(lambda call: call.data.startswith('page'))
@shortcuts.handle_exceptions
@shortcuts.handle_user
def page(call, user):
    page = int(call.data.split('_')[1])
    query = call.data[call.data.index('__') + 2:]

    if query == 'all_shops':
        shops = models.Shop.objects.filter(done=True).annotate(
            orders_count=Count('orders')
        ).order_by('-orders_count', 'command')
    elif query == 'my_favorites':
        shops = user.favorites.order_by('command')
    elif query.startswith('category'):
        category = models.Category.objects.get(pk=int(query.split('_')[-1]))
        shops = category.shops.annotate(
            orders_count=Count('orders')
        ).order_by('-orders_count', 'command')
    else:
        shops = search_by_text(query)

    text = generate_page_text(shops[page * SHOPS_PER_PAGE:(page + 1) * SHOPS_PER_PAGE])
    if query == 'all_shops':
        text = preferences.Texts.shops_title + '\n\n' + text
    elif query == 'my_favorites':
        text = preferences.Texts.my_title + '\n\n' + text
    elif query.startswith('category'):
        category = models.Category.objects.get(pk=int(query.split('_')[-1]))
        text = category.name.capitalize() + ':\n\n' + text
    else:
        text = preferences.Texts.search_title + '\n\n' + text
    keyboard = generate_page_keyboard(page, len(shops), query)

    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=text,
        parse_mode='html',
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(lambda call: call.data == 'do_nothing')
@shortcuts.handle_exceptions
@shortcuts.handle_user
def do_nothing(call, user):
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['shops'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('shops', 'Команда /shops')
def shops(message, user):
    shops = models.Shop.objects.filter(done=True).annotate(
        orders_count=Count('orders')
    ).order_by('-orders_count', 'command')

    text = generate_page_text(shops[:SHOPS_PER_PAGE])
    text = preferences.Texts.shops_title + '\n\n' + text
    keyboard = generate_page_keyboard(0, len(shops), 'all_shops')

    bot.send_message(message.chat.id,
        text=text,
        parse_mode='html',
        reply_markup=keyboard
    )


@bot.message_handler(
    func=lambda message: message.text in [
        shop.command for shop in models.Shop.objects.filter(done=True)
    ]
)
@shortcuts.handle_exceptions
@shortcuts.handle_user
def shop(message, user):
    shop = models.Shop.objects.get(command=message.text)

    text = f'<b>{shop.name}</b>\n'
    text += f'Кэшбэк до {float(shop.percent * shop.client_percent / 100)}%\n'
    text += '\n'
    text += shop.description

    keyboard = telebot.types.InlineKeyboardMarkup()
    if shop in user.favorites.all():
        keyboard.row(telebot.types.InlineKeyboardButton(
            text=preferences.Texts.remove_from_favorites,
            callback_data='remove_' + str(shop.pk)
        ))
    else:
        keyboard.row(telebot.types.InlineKeyboardButton(
            text=preferences.Texts.add_to_favorites,
            callback_data='add_' + str(shop.pk)
        ))
    keyboard.row(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.shop_url,
        url=shortcuts.shorten_link(shop.psite + '?subid=' + str(user.user_id))
    ))

    bot.send_message(message.chat.id,
        text=text,
        parse_mode='html',
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('add'))
@shortcuts.handle_exceptions
@shortcuts.handle_user
def add(call, user):
    pk = int(call.data.split('_')[-1])
    shop = models.Shop.objects.get(pk=pk)

    if shop not in user.favorites.all():
        user.favorites.add(shop)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.remove_from_favorites,
        callback_data='remove_' + str(shop.pk)
    ))
    keyboard.row(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.shop_url,
        url=shortcuts.shorten_link(shop.psite + '?subid=' + str(user.user_id))
    ))

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('remove'))
@shortcuts.handle_exceptions
@shortcuts.handle_user
def remove(call, user):
    pk = int(call.data.split('_')[-1])
    shop = models.Shop.objects.get(pk=pk)

    if shop in user.favorites.all():
        user.favorites.remove(shop)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.add_to_favorites,
        callback_data='add_' + str(shop.pk)
    ))
    keyboard.row(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.shop_url,
        url=shortcuts.shorten_link(shop.psite + '?subid=' + str(user.user_id))
    ))

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['categories'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('categories', 'Команда /categories')
def categories(message, user):
    categories = models.Category.objects.reverse()

    if not categories:
        bot.send_message(message.chat.id, 'Список категорий пуст.')

    else:
        text = preferences.Texts.display_categories
        text += '\n\n'
        for category in categories:
            text += category.command + ' - ' + category.name + '\n'

        bot.send_message(message.chat.id,
            text=text,
            parse_mode='html'
        )


@bot.message_handler(
    func=lambda message: message.text in [
        category.command for category in models.Category.objects.all()
    ]
)
@shortcuts.handle_exceptions
@shortcuts.handle_user
def category(message, user):
    category = models.Category.objects.get(command=message.text)
    shops = category.shops.annotate(
        orders_count=Count('orders')
    ).order_by('-orders_count', 'command')

    text = generate_page_text(shops[:SHOPS_PER_PAGE])
    text = category.name.capitalize() + ':\n\n' + text
    keyboard = generate_page_keyboard(0, len(shops), f'category_{category.pk}')

    bot.send_message(message.chat.id,
        text=text,
        parse_mode='html',
        reply_markup=keyboard
    )


@bot.message_handler(commands=['my'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('my', 'Команда /my')
def my(message, user):
    shops = user.favorites.order_by('command')

    if shops:
        text = generate_page_text(shops[:SHOPS_PER_PAGE])
        text = preferences.Texts.my_title + '\n\n' + text
        keyboard = generate_page_keyboard(0, len(shops), 'my_favorites')

        bot.send_message(message.chat.id,
            text=text,
            parse_mode='html',
            reply_markup=keyboard
        )

    else:
        bot.send_message(message.chat.id,
            text=preferences.Texts.no_my,
            parse_mode='html'
        )


@bot.message_handler(commands=['cabinet'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('cabinet', 'Команда /cabinet')
def cabinet(message, user):
    if user.referrals.count() < preferences.Financial.amount:
        bot.send_message(message.chat.id,
            text=preferences.Texts.message_cabinet_1.format(
                delta=float(preferences.Financial.percent_2 - preferences.Financial.percent_1),
                amount=preferences.Financial.amount
            ),
            parse_mode='html'
        )

    else:
        bot.send_message(message.chat.id,
            text=preferences.Texts.message_cabinet_2.format(
                percent=float(preferences.Financial.percent_2)
            ),
            parse_mode='html'
        )

@bot.message_handler(commands=['balance'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('balance', 'Команда /balance')
def balance(message, user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.withdraw_button,
        callback_data='withdraw'
    ))

    bot.send_message(message.chat.id,
        text=preferences.Texts.message_balance.format(
            balance_in_process='{:.2f}'.format(user.balance_in_process()),
            balance='{:.2f}'.format(user.balance),
            min_amount='{:.2f}'.format(preferences.Financial.min_withdraw_amount)
        ),
        parse_mode='html',
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == 'withdraw')
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('withdraw', 'Кнопка вывода средств')
def withdraw(call, user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.p_qiwi,
        callback_data='choose_qiwi'
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.p_yandex,
        callback_data='choose_yandex'
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.p_card,
        callback_data='choose_card'
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.p_phone,
        callback_data='choose_phone'
    ))

    bot.send_message(call.message.chat.id,
        text=preferences.Texts.choose_payment_system,
        parse_mode='html',
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('choose'))
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('choose', 'Кнопка выбора платежной системы')
def choose(call, user):
    choice = call.data.split('_')[-1]

    bot.send_message(call.message.chat.id,
        text=getattr(preferences.Texts, 'm_' + choice),
        parse_mode='html'
    )

    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['orders'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('orders', 'Команда /orders')
def orders(message, user):
    bot.send_message(message.chat.id,
        text=preferences.Texts.no_orders,
        parse_mode='html'
    )


@bot.message_handler(commands=['affiliate'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('affiliate', 'Команда /affiliate')
def affiliate(message, user):
    invite_url = 'https://t.me/' + bot_username + '?start=' + str(user.first_referral_id)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.referral_button_telegram,
        switch_inline_query='invite'
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.referral_button_vkontakte,
        url=preferences.Texts.referral_url_vkontakte
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.referral_button_facebook,
        url=preferences.Texts.referral_url_facebook
    ))
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.referral_button_odnoklassniki,
        url=preferences.Texts.referral_url_odnoklassniki
    ))

    if user.referrals.count() < preferences.Financial.amount:
        percent = preferences.Financial.percent_1
    else:
        percent = preferences.Financial.percent_2

    bot.send_message(message.chat.id,
        text=preferences.Texts.referral_message.format(
            percent=float(percent),
            invited=user.referrals.count(),
            income='{:.2f}'.format(user.earned),
            url=invite_url
        ),
        parse_mode='html',
        reply_markup=keyboard
    )


@bot.inline_handler(func=lambda query: True)
@shortcuts.handle_exceptions
@shortcuts.handle_user
def invite(query, user):
    if query.query == 'invite':
        invite_url = 'https://t.me/' + bot_username + '?start=' + str(user.first_referral_id)

        keyboard = telebot.types.InlineKeyboardMarkup()
        button = telebot.types.InlineKeyboardButton(
            text=preferences.Texts.referral_invite_telegram_button,
            url=invite_url
        )
        keyboard.add(button)

        result_id = randint(0, 2 ** 32 - 1)
        result = telebot.types.InlineQueryResultArticle(id=result_id,
            title='Отправить приглашение',
            input_message_content=telebot.types.InputTextMessageContent(
                message_text=preferences.Texts.referral_invite_telegram_message,
                parse_mode='html'
            ),
            reply_markup=keyboard
        )

        bot.answer_inline_query(query.id,
            is_personal=True,
            cache_time=0,
            next_offset='',

            results=[result]
        )

    else:
        results = []

        if not query.query:
            shops = models.Shop.objects.filter(done=True).annotate(
                orders_count=Count('orders')
            ).order_by('-orders_count')[:50]
            shops = sorted(shops, key=lambda shop: shop.command)
        else:
            shops = search_by_text(query.query)[:50]

        for shop in shops:
            result = telebot.types.InlineQueryResultArticle(id=randint(0, 2 ** 32 - 1),
                title=shop.name,
                description=f'Кэшбэк до {float(shop.percent * shop.client_percent / 100)}%',
                thumb_url=shop.photo,
                input_message_content=telebot.types.InputTextMessageContent(
                    message_text=f'{shop.command}',
                    parse_mode='html'
                )
            )
            results.append(result)

        if shops:
            search = models.Search(inline=True)
            search.save()

        bot.answer_inline_query(query.id,
            is_personal=True,
            cache_time=0,
            next_offset='',

            results=results
        )


@bot.message_handler(commands=['support'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('support', 'Команда /support')
def support(message, user):
    bot.send_message(message.chat.id,
        text=preferences.Texts.basic_message,
        parse_mode='html'
    )


@bot.message_handler(commands=['ad'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
@shortcuts.handle_action('ad', 'Команда /ad')
def ad(message, user):
    invite_url = 'https://t.me/' + bot_username + '?start=' + str(user.second_referral_id)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=preferences.Texts.ad_withdraw_button,
        url='https://payeer.com/'
    ))

    bot.send_message(message.chat.id,
        text=preferences.Texts.message_ad.format(
            percent=float(preferences.Financial.percent_btb),
            admin_percent=float(preferences.Financial.admin_percent),
            first_level_referrals=0,
            second_level_referrals=0,
            url=invite_url,
            min_withdraw_amount=preferences.Financial.min_withdraw_amount
        ),
        parse_mode='html',
        reply_markup=keyboard
    )


@bot.message_handler(content_types=['text', 'photo'])
@shortcuts.handle_exceptions
@shortcuts.handle_user
def unknown(message, user):
    if user.last_printable_action.action == 'support':
        handle_message_from_user(message, user,
            preferences.Texts.acception_message
        )

    elif user.last_printable_action.action == 'choose':
        bot.send_message(message.chat.id,
            text=preferences.Texts.already,
            parse_mode='html'
        )

    elif message.text:
        possible_link = re.search(r'https?://\S+', message.text)

        if possible_link:
            try:
                link = possible_link.group()
                domain = link[link.index('//') + 2:]
                if '/' in domain:
                    domain = domain[:domain.index('/')]

                for shop in models.Shop.objects.filter(done=True):
                    shop_domain = shop.site[shop.site.index('//') + 2:]
                    if '/' in shop_domain:
                        shop_domain = shop_domain[:shop_domain.index('/')]

                    if shop_domain.endswith(domain) or domain.endswith(shop_domain):
                        result = shortcuts.shorten_link(client.DeeplinksManage.create(settings.ID, shop.offer_id, ulp=link, subid=str(user.user_id))[0])
                        bot.send_message(message.chat.id,
                            text=preferences.Texts.link_title + ' ' + result,
                            parse_mode='html',
                            disable_web_page_preview=True
                        )
                        break
                else:
                    raise ValueError(link)
            except:
                bot.send_message(message.chat.id, preferences.Texts.no_link, parse_mode='html')

        else:
            message.text = message.text[:32]

            shops = search_by_text(message.text)

            if shops:
                search = models.Search(text=True)
                search.save()

                text = generate_page_text(shops[:SHOPS_PER_PAGE])
                text = preferences.Texts.search_title + '\n\n' + text
                keyboard = generate_page_keyboard(0, len(shops), message.text)

                bot.send_message(message.chat.id,
                    text=text,
                    parse_mode='html',
                    reply_markup=keyboard
                )

            else:
                bot.send_message(message.chat.id,
                    text=preferences.Texts.no_shops,
                    parse_mode='html'
                )
