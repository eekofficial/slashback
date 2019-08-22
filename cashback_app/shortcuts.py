import difflib
from time import time
from random import randint, choice
from string import ascii_lowercase, digits

import telebot

from django.conf import settings

from cashback_app.models import User, Operation, Link


def handle_exceptions(function):
    def wrapper(data):
        try:
            function(data)

        except BaseException as error:
            chat = data.from_user

            bot = telebot.TeleBot(settings.TOKEN, threaded=False)
            bot.send_message(chat.id,
                type(error).__name__ + ': ' + str(error)
            )

    return wrapper


def handle_user(function):
    def wrapper(data):
        chat = data.from_user

        try:
            user = User.objects.get(user_id=chat.id)
            user.username = chat.username
            user.first_name = chat.first_name
            user.last_name = chat.last_name

        except User.DoesNotExist:
            user = User(
                user_id=chat.id,
                username=chat.username,
                first_name=chat.first_name,
                last_name=chat.last_name,
                first_referral_id=randint(0, 2 ** 32 - 1),
                second_referral_id=randint(0, 2 ** 32 - 1)
            )

        finally:
            user.save()

        last_actions = [float(action) for action in (user.last_actions or '').split()]
        last_actions.append(time())
        last_actions = last_actions[-5:]
        user.last_actions = ' '.join(str(action) for action in last_actions)
        user.save()

        if len(last_actions) == 5:
            delta = last_actions[-1] - last_actions[0]
            if delta >= 2.5:
                function(data, user)
        else:
            function(data, user)

    return wrapper


def handle_action(action, action_str, printable=True):
    def decorator(function):
        def wrapper(data, user):
            function(data, user)

            operation = Operation(
                user=user,
                action=action,
                action_str=action_str,
                printable=printable
            )
            operation.save()

            if printable:
                user.last_printable_action = operation
                user.save()

        return wrapper

    return decorator


def compare(query, sample):
    matcher = difflib.SequenceMatcher()
    matcher.set_seq1(query)
    matcher.set_seq2(sample)

    result = matcher.ratio()

    return result


def shorten_link(base):
    length = 6
    symbols = ascii_lowercase + digits

    code = ''

    for index in range(length):
        code += choice(symbols)

    link = Link(
        BASE=base,
        CODE=code
    )
    link.save()

    url = 'https://' + settings.ALLOWED_HOSTS[0] + '/' + code

    return url
