from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import reverse

from preferences.admin import PreferencesAdmin

from cashback_app import models

from tickets.models import TicketDialogue
from tickets.admin import TicketDialogueAdmin

admin.site.unregister(Group)
admin.site.unregister(User)


HTML_TAGS = '''
</br>
Доступные html теги:</br>
</br>
&lt;b&gt;bold&lt;/b&gt;, &lt;strong&gt;bold&lt;/strong&gt; - <b>жирный текст</b></br>
&lt;i&gt;italic&lt;/i&gt;, &lt;em&gt;italic&lt;/em&gt; - <b>курсив</b></br>
&lt;a href="http://www.example.com/"&gt;inline URL&lt;/a&gt; - <b>ссылка</b></br>
&lt;a href="tg://user?id=123456789"&gt;inline mention of a user&lt;/a&gt; - <b>упоминание пользователя</b></br>
&lt;code&gt;inline fixed-width code&lt;/code&gt; - <b>код</b></br>
&lt;pre&gt;pre-formatted fixed-width code block&lt;/pre&gt; - <b>блок кода</b></br>
</br>
'''

class UserAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'joined', 'username_url','first_name', 'last_name', 'orders_count']
    search_fields = ['user_id', 'username', 'first_name', 'last_name']
    readonly_fields = ['user_id', 'username_url', 'first_name', 'last_name', 'joined',
                        'total_referrals', 'inviter_url', 'operations', 'list_of_orders', 'list_of_favorites', 'balance_in_process', 'earned']

    def orders_count(self, obj):
        return obj.orders.count()
    orders_count.short_description = 'Количество заказов'

    fieldsets = [
        (
            'Telegram',
            {
                'fields': [
                    'user_id',
                    'username_url',
                    'first_name',
                    'last_name'
                ]
            }
        ),
        (
            'Бот',
            {
                'fields': [
                    'joined',
                    'balance_in_process',
                    'balance',
                ]
            }
        ),
        (
            'Действия',
            {
                'description': '<br/>Последнее действие - сверху.<br/>',
                'fields': [
                    'operations'
                ]
            }
        ),
        (
            'Заказы',
            {
                'description': '<br/>Последний заказ - сверху.<br/>',
                'fields': [
                    'list_of_orders'
                ]
            }
        ),
        (
            'Избранные магазины',
            {
                'fields': [
                    'list_of_favorites'
                ]
            }
        ),
        (
            'Реферальная программа',
            {
                'fields': [
                    'inviter_url',
                    'total_referrals',
                    'earned',
                ]
            }
        )
    ]
    def total_referrals(self, obj):
        return obj.referrals.count()
    total_referrals.short_description = 'Количество приглашенных'

    def operations(self, obj):
        return format_html('<div class="bot-actions">\n' +\
            '\n'.join([(('<br/>' if j != 0 else '') + '<div class="bot-action">\n<div class="bot-action-time">\n'+\
            str(i.created)[:-13] +' по UTC\n</div>\n<div class="bot-action-title">\n' +\
            i.action_str +'\n</div>\n</div>') for j, i in enumerate(reversed(obj.actions.all()))]) + '\n</div>')
    operations.short_description = 'Действия'

    def list_of_orders(self, obj):
        return format_html('<div class="user-orders"></div>')
        # return '\n'.join([str(i.name) + '\n' + str(i.data)[:-13] + ' по UTC\n' + str(i.sum) + ' RUB' for i in obj.orders.all()])
    list_of_orders.short_description = 'Заказы'

    def list_of_favorites(self, obj):
        return format_html('<div class="user-favorites">\n' +\
            '\n'.join([(('<br/>' if j != 0 else '') + '<div class="user-favorite-shop">\n<div class="user-favorite-shop-title">\n' +\
            i.name + ' - <b>' + i.command +'</b>\n</div>\n</div>') for j, i in enumerate(reversed(obj.favorites.all()))]) + '\n</div>')
    list_of_favorites.short_description = 'Магазины'

    def inviter_url(self, obj):
        if obj.inviter:
            url = reverse('admin:cashback_app_user_change', args=[obj.inviter.pk])
            html = f'<a href="{url}" style="font-weight: bold;">{obj.inviter}</a>'
            return format_html(html)
        else:
            return '-'
    inviter_url.short_description = 'Пригласитель'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def username_url(self, obj):
        if obj.username:
            url = 'https://t.me/' + obj.username
            html = f'<a href="{url}" target="_blank">@{obj.username}</a>'
            return format_html(html)
        else:
            return '-'
    username_url.short_description = 'Логин'

    def has_change_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False


class PartnerAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['command', 'name', 'total_shops']
    list_display_links = None
    list_editable = ['name', 'command']
    readonly_fields = ['total_shops']
    fieldsets = [
        (
            'Информация',
            {
                'fields': [
                    'command',
                    'name',
                    # 'total_shops'
                ]
            }
        ),

    ]
    def total_shops(self, obj):
        return obj.shops.count()
    total_shops.short_description = 'Количество магазинов'

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_delete_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_change_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False

        return super().change_view(request, object_id, form_url, extra_context)

    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False


class StatisticsAdmin(PreferencesAdmin):
    readonly_fields = ['number_of_users']
    fieldsets = [
        (
            'Общая',
            {
                'fields': [
                    'number_of_users',
                    'number_of_active_users',
                ]
            }
        ),
        (
            'Поиск по магазинам (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'total_searches',
                    'total_text_searches',
                    'total_inline_searches',
                ]
            }
        ),
        (
            'Кэшбэчные ссылки (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'short_links',
                ]
            }
        ),
        (
            'Заказы (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'orders_count',
                ]
            }
        ),
        (
            'Реферальная система btc (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'btc_count',
                ]
            }
        ),
        (
            'Реферальная система btb (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'btb_count',
                ]
            }
        ),
        (
            'Нажатия на команды (за 24 часа, месяц, все время)',
            {
                'fields': [
                    'start_command_count',
                    'help_command_count',
                    'search_command_count',
                    'shops_command_count',
                    'categories_command_count',
                    'my_command_count',
                    'cabinet_command_count',
                    'balance_command_count',
                    'orders_command_count',
                    'affiliate_command_count',
                    'ad_command_count',
                    'support_command_count',
                ]
            }
        ),
    ]
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False


class FinancialAdmin(PreferencesAdmin):
    fieldsets = [
        (
            'Баланс',
            {
                'fields': [
                    'min_withdraw_amount',
                    'min_withdraw_amount_btb',
                ]
            }
        ),
        (
            'Реферальная программа',
            {
                'fields': [
                    ('percent_1', 'percent_2'),
                    'amount',
                    ('percent_btb', 'admin_percent'),
                ]
            }
        ),
    ]
    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, request, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False

        return super().change_view(request, object_id, form_url, extra_context)


class ShopAdmin(admin.ModelAdmin):
    list_display = ['offer_id', 'command', 'name', 'done', 'show_percent', 'count_of_orders', 'list_categories']
    list_display_links = ['offer_id']
    search_fields = ['name', 'command']
    list_filter = ['done', 'categories']
    ordering = ('-orders', 'command')
    fieldsets = [
        (
            'Оформление',
            {
                'fields': [
                    'offer_id',
                    'command',
                    ('name', 'name_rus'),
                    'description',
                    'categories',
                ]
            }
        ),
        (
            'Кэшбэк',
            {
                'fields': [
                    'client_percent'
                ]
            }
        ),
    ]
    def count_of_orders(self, obj):
        return obj.orders.count()
    count_of_orders.short_description = 'Количество заказов'

    def show_percent(self, obj):
        if obj.percent:
            return float(obj.percent*obj.client_percent/100)
    show_percent.short_description = 'Кэшбэк, %'

    def list_categories(self, obj):
        if obj.categories.count():
            return ', '.join(category.name for category in obj.categories.all())
    list_categories.short_description = 'Категории'

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_delete_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_change_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False


class PostAdmin(admin.ModelAdmin):
    list_display = ['created', 'status', 'amount_of_receivers', 'photo', 'message', 'html_button']
    list_display_links = ['created']

    search_fields = ['message', 'button_text', 'button_url']
    list_filter = ['status']

    list_per_page = 10

    def html_button(self, obj):
        if obj.button_text and obj.button_url:
            return format_html(f'<a href="{obj.button_url}" target="_blank">{obj.button_text}</a>')
        else:
            return ''
    html_button.short_description = 'Кнопка'

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = [
            (
                'Сообщение',
                {
                    'fields': [
                        'photo',
                        'message',
                        ('button_text', 'button_url'),
                    ],
                    'description': HTML_TAGS
                }
            ),
            (
                'Откладывание поста',
                {
                    'fields': [
                        'postpone',
                        'postpone_time',
                    ]
                }
            ),
        ]

        if not obj:
            return base_fieldsets
        else:
            return [
                (
                    'Общая информация',
                    {
                        'fields': [
                            'created',
                            'status'
                        ] + (
                            ['amount_of_receivers'] if obj.status == 'done' else []
                        )
                    }
                ),
            ] + base_fieldsets
    def get_readonly_fields(self, request, obj=None):
        return ['created', 'status', 'amount_of_receivers']

    def has_view_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return (obj is None) or (obj.status in ['postponed'])
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return (obj is None) or (obj.status in ['postponed', 'queue', 'done'])
        else:
            return False

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False

        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False

        return super().change_view(request, object_id, form_url, extra_context)

    class Media:
        js = ('admin/js/post.js',)


class TextsAdmin(PreferencesAdmin):
    fieldsets = [
        (
            'Команда /start',
            {
                'description': HTML_TAGS + 'Для отключения сообщения оставь поле пустым.' + '</br></br>',
                'fields': [
                    (
                        'start_photo_0',
                        'start_message_0',

                    ),
                    (
                        'start_photo_1',
                        'start_message_1',

                    ),
                    (
                        'start_photo_2',
                        'start_message_2',

                    ),
                    (
                        'start_photo_3',
                        'start_message_3',

                    ),
                ]
            }
        ),
        (
            'Команда /help',
            {
                'description': HTML_TAGS,
                'fields': [
                    'help_message',
                ]
            }
        ),
        (
            'Команда /search',
            {
                'description': HTML_TAGS,
                'fields': [
                    'search_message',
                    'search_button',
                    'search_title',
                    'no_shops',
                    'link_title',
                    'no_link',
                ]
            }
        ),
        (
            'Команда /shops',
            {
                'description': HTML_TAGS,
                'fields': [
                    'shops_title',
                    ('add_to_favorites', 'remove_from_favorites'),
                    'shop_url',
                ]
            }
        ),
        (
            'Команда /categories',
            {
                'description': HTML_TAGS,
                'fields': [
                    'display_categories',
                ]
            }
        ),
        (
            'Команда /my',
            {
                'description': HTML_TAGS,
                'fields': [
                    'my_title',
                    'no_my',
                ]
            }
        ),
        (
            'Команда /cabinet',
            {
                'description': HTML_TAGS,
                'fields': [
                    'message_cabinet_1',
                    'message_cabinet_2',
                ]
            }
        ),
        (
            'Команда /balance',
            {
                'description': HTML_TAGS,
                'fields': [
                    'message_balance',
                    'withdraw_button',
                    'choose_payment_system',
                    ('p_qiwi', 'm_qiwi'),
                    ('p_yandex', 'm_yandex'),
                    ('p_card', 'm_card'),
                    ('p_phone', 'm_phone'),
                    'already',
                ]
            }
        ),
        (
            'Команда /orders',
            {
                'description': HTML_TAGS,
                'fields': [
                    'orders_title',
                    'no_orders',
                ]
            }
        ),
        (
            'Команда /affiliate',
            {
                'description': HTML_TAGS,
                'fields': [
                    (
                        'referral_message',
                    ),
                    (
                        'referral_button_telegram',
                    ),
                    (
                        'referral_invite_telegram_message',
                        'referral_invite_telegram_button',
                    ),
                    (
                        'referral_button_vkontakte',
                        'referral_url_vkontakte'
                    ),
                    (
                        'referral_button_facebook',
                        'referral_url_facebook',
                    ),
                    (
                        'referral_button_odnoklassniki',
                        'referral_url_odnoklassniki',
                    )
                ]
            }
        ),
        (
            'Команда /ad',
            {
                'description': HTML_TAGS,
                'fields': [
                    'message_ad',
                    'ad_withdraw_button',
                ]
            }
        ),
        (
            'Команда /support',
            {
                'description': HTML_TAGS,
                'fields': [
                    'basic_message',
                    'acception_message'
                ]
            }
        ),
    ]
    def has_view_permission(self, request, obj=None):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        if request.user.username in ['admin']:
            return True
        else:
            return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False

        return super().change_view(request, object_id, form_url, extra_context)


admin.site.register(models.Texts, TextsAdmin)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Shop, ShopAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Financial, FinancialAdmin)
admin.site.register(models.Statistics, StatisticsAdmin)
admin.site.register(TicketDialogue, TicketDialogueAdmin)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Partner, PartnerAdmin)

admin.site.site_header = admin.site.site_title = 'Администрирование бота'
admin.site.site_url = ''