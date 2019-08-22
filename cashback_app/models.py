import random
from decimal import Decimal
from string import ascii_lowercase
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from preferences.models import Preferences


class Photo(models.ImageField):
    max_size_mb = 5

    def __init__(self, *args, **kwargs):
        kwargs['upload_to'] = self.get_path
        kwargs['validators'] = [self.validate_image]

        return super().__init__(*args, **kwargs)

    def get_path(self, instance, filename, length=10):
        file_format = filename.split('.')[-1].lower()

        filename = ''
        for index in range(length):
            filename += random.choice(ascii_lowercase)

        return f'{filename}.{file_format}'

    def validate_image(self, image):
        image_size_bytes = image.file.size
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if image_size_bytes > max_size_bytes:
            raise ValidationError(f'Максимальный размер файла - {self.max_size_mb}МБ')


class Operation(models.Model):
    user = models.ForeignKey(
        to='User',
        related_name='actions',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(
        auto_now_add=True
    )
    action_str = models.CharField(
        max_length=64
    )
    action = models.CharField(
        max_length=64
    )
    printable = models.BooleanField()


class Search(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    text = models.BooleanField(default=False)
    inline = models.BooleanField(default=False)


class Shop(models.Model):
    offer_id = models.BigIntegerField('ID на admitad')
    command = models.CharField('Команда',
        max_length=64
    )
    name = models.CharField('Название',
        max_length=64
    )
    name_rus = models.CharField('Альтернативное название (на другом языке)',
        max_length=64
    )
    description = models.TextField('Описание')
    categories = models.ManyToManyField(
        to='Category',
        related_name='shops',
        verbose_name='Категории'
    )

    client_percent = models.DecimalField('Выплачиваемая доля, %',
        max_digits=5,
        decimal_places=2
    )

    done = models.BooleanField('Доступен', default=False)
    photo = models.URLField(blank=True, null=True)
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True, null=True
    )
    site = models.URLField(blank=True, null=True)
    psite = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'магазин'
        verbose_name_plural = 'магазины'


class Order(models.Model):
    user = models.ForeignKey(verbose_name='Пользователь',
        to='User',
        related_name='orders',
        on_delete=models.SET_NULL,
        blank=True, null=True
    )
    site = models.URLField('Сайт'
    )
    date = models.DateTimeField('Дата',
                    auto_now_add=True
    )
    total_sum = models.DecimalField('Сумма',
                    max_digits=5,
                    decimal_places=2
    )
    status = models.CharField('Статус',
                choices=[
                    ('processing', 'В обработке'),
                    ('confirmed', 'подтверждено')
                ],
                max_length=256
    )
    friends_order = models.BooleanField(default=False
    )
    name = models.ForeignKey(verbose_name='Магазин',
        to='Shop',
        related_name='orders',
        on_delete=models.SET_NULL,
        blank=True, null=True
    )
    action_id = models.BigIntegerField()
    def __str__(self):
        return 'Заказы'

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class Texts(Preferences):
    start_message_0 = models.TextField('Сообщение #1',
                            blank=True, null=True
    )
    start_photo_0 = Photo('Фото #1',
                        blank=True, null=True
    )
    start_message_1 = models.TextField('Сообщение #2',
                            blank=True, null=True
    )
    start_photo_1 = Photo('Фото #2',
                        blank=True, null=True
    )
    start_message_2 = models.TextField('Сообщение #3',
                            blank=True, null=True
    )
    start_photo_2 = Photo('Фото #3',
                        blank=True, null=True
    )
    start_message_3 = models.TextField('Сообщение #4',
                            blank=True, null=True
    )
    start_photo_3 = Photo('Фото #4',
                        blank=True, null=True
    )
    help_message = models.TextField('Cообщение',
                            default='-'
    )
    search_message = models.TextField('Сообщение',
                            default='-'
    )
    search_button = models.CharField('Надпись на кнопке',
                            default='-', max_length=256
    )
    search_title = models.CharField('Заголовок результатов поиска',
                            default='-', max_length=256
    )
    shops_title = models.CharField('Заголовок',
                            default='-', max_length=256
    )
    add_to_favorites = models.CharField('Кнопка добавления в избранное', default='-', max_length=256)
    remove_from_favorites = models.CharField('Кнопка удаления из избранного', default='-', max_length=256)
    shop_url = models.CharField('Кнопка перехода в магазин', default='-', max_length=256)
    display_categories = models.CharField('Заголовок',
                            default='-', max_length=256
    )
    my_title = models.CharField('Заголовок списка избранных магазинов',
                            default='-', max_length=256
    )
    no_my = models.CharField('Список избранных магазинов пуст',
                            default='-', max_length=256
    )
    referral_message = models.TextField('Сообщение',
                                default='-'
    )
    referral_button_telegram = models.CharField('Приглашение в Telegram',
                            default='-', max_length=256
    )
    referral_invite_telegram_message = models.TextField('Текст приглашения в Telegram',
                                default='-'
    )
    referral_invite_telegram_button = models.CharField('Кнопка запуска бота',
                                default='-', max_length=256,
    )
    referral_button_vkontakte = models.CharField('Приглашение Вконтакте',
                            default='-', max_length=256
    )
    referral_url_vkontakte = models.URLField('Ссылка Вконтакте'
    )
    referral_button_odnoklassniki = models.CharField('Приглашение в Одноклассники',
                            default='-', max_length=256
    )
    referral_url_odnoklassniki = models.URLField('Ссылка Одноклассники'
    )
    referral_button_facebook = models.CharField('Приглашение в Facebook',
                            default='-', max_length=256
    )
    referral_url_facebook = models.URLField('Ссылка Facebook'
    )
    message_ad = models.TextField('Сообщение',
                    default='-'
    )
    ad_withdraw_button = models.CharField('Кнопка вывода', default='-', max_length=256)
    basic_message = models.TextField('Информационное сообщение', default='-'
    )
    acception_message = models.TextField('Сообщение о принятии', default='-'
    )
    message_cabinet_1 = models.TextField('Сообщение (стандартный кэшбэк)', default='-'
    )
    message_cabinet_2 = models.TextField('Сообщение (повышенный кэшбэк)', default='-'
    )
    message_balance = models.TextField('Сообщение', default='-')
    withdraw_button = models.CharField('Кнопка вывода', default='-', max_length=256)
    choose_payment_system = models.TextField('Сообщение выбора платежной системы', default='-')
    p_qiwi = models.CharField('Кнопка выбора QIWI', default='-', max_length=256)
    p_yandex = models.CharField('Кнопка выбора Яндекс.Денег', default='-', max_length=256)
    p_card = models.CharField('Кнопка выбора банковской карты', default='-', max_length=256)
    p_phone = models.CharField('Кнопка выбора баланса телефона', default='-', max_length=256)
    m_qiwi = models.CharField('Ввод кошелька QIWI', default='-', max_length=256)
    m_yandex = models.CharField('Ввод кошелька Яндекс.Денег', default='-', max_length=256)
    m_card = models.CharField('Ввод банковской карты', default='-', max_length=256)
    m_phone = models.CharField('Ввод телефона', default='-', max_length=256)
    already = models.TextField('Кошелек уже зарегистрирован', default='-')
    orders_title = models.CharField('Заголовок списка заказов', default='-', max_length=256)
    link_title = models.CharField('Заголовок преобразованной ссылки', default='-', max_length=256)
    no_link = models.TextField('Ошибка поиска по ссылке', default='-')
    no_orders = models.CharField('Список заказов пуст', default='-', max_length=256)
    no_shops = models.TextField('Магазины не найдены', default='-')
    def __str__(self):
        return 'Тексты'

    class Meta:
        verbose_name = 'список'
        verbose_name_plural = 'списки'


class Link(models.Model):
    created = models.DateTimeField(
        auto_now_add=True
    )
    BASE = models.URLField('BASE'
    )
    CODE = models.CharField('CODE', max_length=256
    )


class Financial(Preferences):
    min_withdraw_amount = models.DecimalField('Минимальная сумма вывода, RUB',
                                            max_digits=7,
                                            decimal_places=2,
                                            default=500
    )
    min_withdraw_amount_btb = models.DecimalField('Минимальная сумма вывода btb, RUB',
                                            max_digits=7,
                                            decimal_places=2,
                                            default=500
    )
    percent = models.DecimalField(
                                    max_digits=5,
                                    decimal_places=2,
                                    default=90
    )
    percent_btb = models.DecimalField('Партнерский процент, %',
                                    max_digits=5,
                                    decimal_places=2,
                                    default=75
    )
    admin_percent = models.DecimalField('Процент от привлечения админов, %',
                                    max_digits=5,
                                    decimal_places=2,
                                    default=5
    )
    amount = models.IntegerField('Количество человек для повышенного уровня',
        default=5
    )
    percent_1 = models.DecimalField('Стандартный уровень, %',
                                    max_digits=5,
                                    decimal_places=2,
                                    default=5
    )
    percent_2 = models.DecimalField('Повышенный уровень, %',
                                    max_digits=5,
                                    decimal_places=2,
                                    default=15
    )
    def __str__(self):
        return 'Числа'

    class Meta:
        verbose_name = 'список'
        verbose_name_plural = 'списки'


class Statistics(Preferences):
    def number_of_users(self):
        return User.objects.count()
    number_of_users.short_description = 'Количество пользователей'

    def number_of_active_users(self):
        return User.objects.annotate(
            orders_count=models.Count('orders')
        ).exclude(orders_count=0).count()
    number_of_active_users.short_description = 'Количество активных пользователей'

    def total_searches(self):
        from_day = timezone.now() - timedelta(days=1)
        from_month = timezone.now() - timedelta(days=30)
        from_all = timezone.now() - timedelta(days=365 * 50)
        count_day = Search.objects.filter(created__gt=from_day).count()
        count_month = Search.objects.filter(created__gt=from_month).count()
        count_all = Search.objects.filter(created__gt=from_all).count()
        return f'{count_day}, {count_month}, {count_all}'
    total_searches.short_description = 'Общее число поисков'
    def total_text_searches(self):
        from_day = timezone.now() - timedelta(days=1)
        from_month = timezone.now() - timedelta(days=30)
        from_all = timezone.now() - timedelta(days=365 * 50)
        count_day = Search.objects.filter(text=True, created__gt=from_day).count()
        count_month = Search.objects.filter(text=True, created__gt=from_month).count()
        count_all = Search.objects.filter(text=True, created__gt=from_all).count()
        return f'{count_day}, {count_month}, {count_all}'
    total_text_searches.short_description = 'Число обычных поисков'
    def total_inline_searches(self):
        from_day = timezone.now() - timedelta(days=1)
        from_month = timezone.now() - timedelta(days=30)
        from_all = timezone.now() - timedelta(days=365 * 50)
        count_day = Search.objects.filter(inline=True, created__gt=from_day).count()
        count_month = Search.objects.filter(inline=True, created__gt=from_month).count()
        count_all = Search.objects.filter(inline=True, created__gt=from_all).count()
        return f'{count_day}, {count_month}, {count_all}'
    total_inline_searches.short_description = 'Число inline поисков'

    def short_links(self):
        from_day = timezone.now() - timedelta(days=1)
        from_month = timezone.now() - timedelta(days=30)
        from_all = timezone.now() - timedelta(days=365 * 50)
        count_day = Link.objects.filter(created__gt=from_day).count()
        count_month = Link.objects.filter(created__gt=from_month).count()
        count_all = Link.objects.filter(created__gt=from_all).count()
        return f'{count_day}, {count_month}, {count_all}'
    short_links.short_description = 'Преобразованные ссылки'

    def orders_count(self):
        return '0, 0, 0'
    orders_count.short_description = 'Число заказов'

    def btc_count(self):
        return User.objects.exclude(inviter=None).count()
    btc_count.short_description = 'Количество приглашенных'

    def btb_count(self):
        return 0
    btb_count.short_description = 'Количество приглашенных'

    def command_count(self, command):
        from_day = timezone.now() - timedelta(days=1)
        from_month = timezone.now() - timedelta(days=30)
        from_all = timezone.now() - timedelta(days=365 * 50)
        count_day = Operation.objects.filter(action=command, created__gt=from_day).count()
        count_month = Operation.objects.filter(action=command, created__gt=from_month).count()
        count_all = Operation.objects.filter(action=command, created__gt=from_all).count()
        return f'{count_day}, {count_month}, {count_all}'
    def start_command_count(self):
        return self.command_count('start')
    start_command_count.short_description = '/start'
    def help_command_count(self):
        return self.command_count('help')
    help_command_count.short_description = '/help'
    def search_command_count(self):
        return self.command_count('search')
    search_command_count.short_description = '/search'
    def shops_command_count(self):
        return self.command_count('shops')
    shops_command_count.short_description = '/shops'
    def categories_command_count(self):
        return self.command_count('categories')
    categories_command_count.short_description = '/categories'
    def my_command_count(self):
        return self.command_count('my')
    my_command_count.short_description = '/my'
    def cabinet_command_count(self):
        return self.command_count('cabinet')
    cabinet_command_count.short_description = '/cabinet'
    def balance_command_count(self):
        return self.command_count('balance')
    balance_command_count.short_description = '/balance'
    def orders_command_count(self):
        return self.command_count('orders')
    orders_command_count.short_description = '/orders'
    def affiliate_command_count(self):
        return self.command_count('affiliate')
    affiliate_command_count.short_description = '/affiliate'
    def ad_command_count(self):
        return self.command_count('ad')
    ad_command_count.short_description = '/ad'
    def support_command_count(self):
        return self.command_count('support')
    support_command_count.short_description = '/support'

    def __str__(self):
        return 'Статистика'

    class Meta:
        verbose_name = 'список'
        verbose_name_plural = 'списки'


class Category(models.Model):
    name = models.CharField('Название', max_length=256)
    command = models.CharField('Команда', max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'


class User(models.Model):
    joined = models.DateTimeField('Первый запуск бота, UTC',
        auto_now_add=True
    )

    inviter = models.ForeignKey(verbose_name='Пригласитель',
        to='self',
        related_name='referrals',
        on_delete=models.SET_NULL,
        blank=True, null=True
    )

    user_id = models.BigIntegerField('ID')

    username = models.CharField('Логин',
        max_length=256,
        blank=True, null=True
    )
    first_name = models.CharField('Имя',
        max_length=256,
        blank=True, null=True
    )
    last_name = models.CharField('Фамилия',
        max_length=256,
        blank=True, null=True
    )
    last_printable_action = models.ForeignKey(to='Operation',
                                    on_delete=models.SET_NULL,
                                    blank=True, null=True,
                                    related_name='is_last_printable'
    )
    first_referral_id = models.BigIntegerField()
    second_referral_id = models.BigIntegerField()

    def balance_in_process(self):
        return Decimal(0)
    balance_in_process.short_description = 'Баланс в обработке, RUB'
    balance = models.DecimalField('Текущий баланс, RUB',
        max_digits=10, decimal_places=2, default=0
    )
    earned = models.DecimalField('Заработано, RUB',
        max_digits=10, decimal_places=2, default=0
    )

    favorites = models.ManyToManyField(
        to='Shop',
        related_name='fans',
        blank=True, null=True
    )

    last_actions = models.TextField(default='', blank=True, null=True)

    w_qiwi = models.TextField(blank=True, null=True)
    w_yandex = models.TextField(blank=True, null=True)
    w_card = models.TextField(blank=True, null=True)
    w_phone = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.user_id)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Partner(models.Model):
    class Meta:
        verbose_name = 'партнер'
        verbose_name_plural = 'партнеры'


class Post(models.Model):
    created = models.DateTimeField('Дата создания, UTC',
        auto_now_add=True
    )
    status = models.CharField('Статус',
        max_length=9,
        choices=[
            ('created', 'Создан'),
            ('postponed', 'Отложен'),
            ('queue', 'В очереди'),
            ('process', 'Рассылается'),
            ('done', 'Разослан')
        ],
        default='created'
    )

    photo = Photo('Изображение, до 5МБ',
        blank=True, null=True
    )
    message = models.TextField('Форматированный текст, до 1024 символов',
        max_length=1024
    )
    button_text = models.CharField('Текст кнопки',
        max_length=50, blank=True, null=True
    )
    button_url = models.URLField('Ссылка кнопки',
        blank=True, null=True
    )

    postpone = models.BooleanField('Отложить',
        default=False
    )
    postpone_time = models.DateTimeField('Время публикации, UTC',
        default=datetime(2020, 1, 1)
    )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.postpone:
                self.status = 'postponed'
            else:
                self.status = 'queue'

        elif self.status == 'postponed' and not self.postpone:
            self.status = 'queue'

        if not self.button_text or not self.button_url:
            self.button_text = None
            self.button_url = None

        super().save(*args, **kwargs)

    amount_of_receivers = models.IntegerField('Количество получателей',
        blank=True, null=True
    )

    def __str__(self):
        time_isoformat = self.created.isoformat(sep=' ', timespec='seconds')
        time_isoformat = time_isoformat[:time_isoformat.index('+')]

        return time_isoformat

    class Meta:
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

