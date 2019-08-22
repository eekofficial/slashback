import telebot

from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from cashback_app.models import Link, User
from cashback_app.handlers import bot


def users(request):
    return HttpResponse(str(User.objects.count()))


@csrf_exempt
def update(request):
    update_json = request.body.decode()
    update = telebot.types.Update.de_json(update_json)

    bot.process_new_updates([update])

    return HttpResponse()


def resolve_shorten_link(request, code):
    try:
        short_link = Link.objects.get(CODE=code)
        base = short_link.BASE

        return redirect(base)

    except BaseException:
        return HttpResponseNotFound()
