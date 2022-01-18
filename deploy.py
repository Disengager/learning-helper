# -*- coding: utf8 -*-

import telebot
import time
import config
import json
import inspect
from telebot import types
from flask import Flask, render_template, request
from settings import *
import werkzeug
from werkzeug.utils import secure_filename
werkzeug.secure_filename = secure_filename
# from survey import Survey
from flask_admin import Admin
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import Markup

from models import *
from db_manager import app, db, bot
from views import CustomView
from forms import CustomSelectField
from wtforms.fields.core import StringField
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound


app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='Learning assistant', template_mode='bootstrap3')
global_var = dict()


class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/settings.html', temp="12")


class ScreenView(ModelView):
    list_columns = ['name', 'link', 'def_name', 'get_type',  'is_template']
    form_choices = {'type': [(str(Screen.PAGE), 'Страница'), (str(Screen.SURVEY), 'Опрос'), (str(Screen.CAROUSEL), 'Карусель')],
                    'def_name': CustomView().get_methods_no_index()}
    inline_models = [(ScreenButton, dict(form_columns=['id', 'name', 'link', 'sort']))]
    # column_list = ('name', 'link', 'def_name')

    def get_edit_form(self):
        form = super(ScreenView, self).get_edit_form()
        return self.add_template_column(form)

    def get_create_form(self):
        form = super(ScreenView, self).get_create_form()
        return self.add_template_column(form)

    def add_template_column(self, form):
        form.template = CustomSelectField(choices=self.get_screen_choices())
        return form

    def after_model_change(self, form, model, is_created):
        screen_list = Screen().query.filter_by(is_template=True).all()
        select_screen = False
        i = 2
        for screen in screen_list:
            if int(i) == int(form.template.data):
                select_screen = screen
                break
            i = i + 1

        if not select_screen:
            return True

        for button in select_screen.buttons:
            new_button = ScreenButton()
            new_button.name = button.name
            new_button.link = button.link
            new_button.sort = button.sort
            new_button.screen = model.id
            db.session.add(new_button)
        model.text = select_screen.text
        model.type = select_screen.type
        model.def_name = select_screen.def_name
        model.custom_view = select_screen.custom_view
        db.session.add(model)
        db.session.commit()

        # form.buttons.data = select_screen.buttons
        super(ScreenView, self).on_model_change(form, model, is_created)

    def get_screen_choices(self):
        screen_list = Screen().query.filter_by(is_template=True).all()
        choices = [(1, 'No template')]

        i = 2
        for screen in screen_list:
            choices.append((i, screen.name + ' (' + screen.link + ')'))
            i = i + 1

        return choices


class MenuView(ModelView):
    inline_models = [(MenuItem, dict(form_columns=['id', 'name', 'link',  'col', 'row']))]


admin.add_view(ScreenView(Screen, db.session))
admin.add_view(ModelView(Group, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(MenuView(Menu, db.session))
admin.add_view(ModelView(Subject, db.session))
admin.add_view(ModelView(Homework, db.session))
# admin.add_view(ModelView(MenuItem, db.session))
admin.add_view(AnalyticsView(name='Settings', endpoint='settings'))


@bot.message_handler(commands=['home'])
def reactStart(message):
    if not auth_mixin(message):
        return False
    # load_menu(message)


@bot.message_handler(commands=['start'])
def reactStart(message):
    if not auth_mixin(message):
        return False
    # load_menu(message)


@bot.message_handler(content_types=['text'])
def reatNext(message):
    print('-start callback-text-')
    if not auth_mixin(message):
        return False

    print('-after mixin-')

    menu = Menu.query.filter_by(group=global_var['users'][message.chat.id].group, name=message.text).first()
    if menu:
        load_menu(menu, message=message)
        return True

    menu_list = Menu.query.filter_by(group=global_var['users'][message.chat.id].group).all()
    result = False
    for menu in menu_list:
        result = menu.get_menu_item(message.text)
        if result:
            break

    if result:
        screen = Screen().query.filter_by(link=result.link).first()
        if screen:
            screen.render(False, user=global_var['users'][message.chat.id])
    return True


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print('-start callback_inline-')
    group_mixin(call)
    if not auth_mixin(call.message):
        return False
    print('-after mixin-')
    screen = Screen().query.filter_by(link=get_main_link(call.data)).first()

    if screen:
        if is_params(call.data):
            screen.link = call.data

        screen.render(False,  user=global_var['users'][call.message.chat.id])
        return True
    return False


def get_main_link(link):
    return link.split('?')[0]


def is_params(link):
    return len(link.split('?')) > 1


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if not auth_mixin(message):
        return False
    pass


#--------------
#Работа с ботом
#--------------
@app.route(bot_url + '/run', methods=["POST"])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route(bot_url, methods=['GET'])
def webhook():
    bot.remove_webhook()
    time.sleep(0.1)
    bot.set_webhook(url=site_url + bot_url + '/run')
    return "!", 200
#--------------------
#Конец работы с ботом
#--------------------


def auth_mixin(message):
    print('auth_mixin')
    print(message.chat.id)
    global global_var
    if not 'users' in global_var:
        try:
            global_var['users'] = dict()
            global_var['users'][message.chat.id] = User().query.filter_by(chat_id=message.chat.id).one()
        except MultipleResultsFound as e:
            global_var['users'][message.chat.id] = False
        except NoResultFound as e:
            global_var['users'][message.chat.id] = False

    print(global_var)

    if not global_var['users'][message.chat.id]:
        global_var['users'][message.chat.id] = User()
        global_var['users'][message.chat.id].chat_id = message.chat.id
        db.session.add(global_var['users'][message.chat.id])
        db.session.commit()
    if global_var['users'][message.chat.id].is_group():
        return True

    print(global_var)

    return False


def group_mixin(call):
    # groups = Group().query.all()
    button = Screen().query.filter_by(link='/start').first().get_button_by_link(call.data)
    if not button:
        return True
    group = Group().query.filter_by(name=button.name).first()
    if not group:
        return True

    global global_var

    if not 'users' in global_var:
        global_var['users'] = dict()

    global_var['users'][call.message.chat.id] = User().query.filter_by(chat_id=call.message.chat.id).first()
    global_var['users'][call.message.chat.id].group = group.id
    db.session.add(global_var['users'][call.message.chat.id])
    db.session.commit()
    menu = Menu().query.filter_by(group=group.id).first()
    if menu:
        load_menu(menu, message=call.message)


def load_menu(menu, **kwargs):
    btnm = telebot.types.ReplyKeyboardMarkup(resize_keyboard=False)
    for item in menu.items:
        btnm.add(types.KeyboardButton(item.name))
    global_var['users'][kwargs['message'].chat.id].send_button(menu.name, btnm)


def get_subject_by_key(key):
    pass


def load_lessons(message):
    pass


def load_lesson_theme(message, sub):
    pass


def load_lesson_subtheme(message, sub, data):
    pass


def load_lesson_theme_all(message,sub, data):
    pass


def send_message(chat_id, content, **kwargs):
    parse_mode = kwargs['parse_mode'] if 'parse_mode' in kwargs else False
    buttons = kwargs['buttons'] if 'buttons' in kwargs else False
    i = 0
    send_content = ''
    b_string = ''
    b_closed = True
    for c in content:
        if (c == '\n' and i > MESSAGE_LENGTH) or (c == ' ' and i > MESSAGE_LENGTH_CRITICAL) or \
                i > MESSAGE_LENGTH_STOP:
            if parse_mode:
                parse_send_content = send_content
                if len(send_content.split('<b>')) > len(send_content.split('</b>')):
                    parse_send_content += '</b>'
                bot.send_message(chat_id, parse_send_content, parse_mode=parse_mode)
            else:
                bot.send_message(chat_id, send_content)

            i = -1
            if len(send_content.split('<b>')) > len(send_content.split('</b>')):
                send_content = '<b>'
            else:
                send_content = ''

        else:
            send_content += c
        i += 1

    if parse_mode:
        if buttons:
            bot.send_message(chat_id, send_content, reply_markup=buttons,  parse_mode=parse_mode)
        else:
            bot.send_message(chat_id, send_content, parse_mode=parse_mode)
    else:
        if buttons:
            bot.send_message(chat_id, send_content, reply_markup=buttons)
        else:
            bot.send_message(chat_id, send_content)