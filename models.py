# from flask_sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.sqltypes import JSON

from db_manager import db, bot
from telebot import types
from views import CustomView
from flask import Markup


class Screen(db.Model):
    _tablename__ = 'screen'
    PAGE = 0
    SURVEY = 1
    CAROUSEL = 2
    TYPE = {
        PAGE: 'page',
        SURVEY: 'survey',
        CAROUSEL: 'carousel',
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)
    text = db.Column(db.String(5000), unique=False)
    link = db.Column(db.String(255), unique=True)
    custom_view = db.Column(db.Boolean, default=False, nullable=False)
    def_name = db.Column(db.String(500), unique=False)
    buttons = db.relationship('ScreenButton', backref='screen_buttons')
    type = db.Column(db.SmallInteger, default=TYPE)
    is_template = db.Column(db.Boolean, default=False, nullable=False)
    message_id = 1
    dynamic_buttons = []

    # def __init__(self, username, email):
    #     self.email = email
    #     pass
    def __init__(self):
        self.dynamic_buttons = []

    def __repr__(self):
        return '<Экран" %r>' % self.name

    def render(self, old_screen, **kwargs):
        print('-start-render-')
        if self.custom_view and self.def_name != '':
            kwargs['screen'] = self
            CustomView().functions[self.def_name](old_screen, kwargs)
            print('-load_custom_view-')
            return False

        print('step 1')

        if not 'user' in kwargs and not 'chat_id' in kwargs:
            print('-no-user-')
            return False
        print('step 2')
        chat_id = kwargs['user'].chat_id if 'user' in kwargs else kwargs['chat_id']
        print('step 3')
        if old_screen:
            if len(self.get_buttons()) > 0:
                print('-start-edit-message-')
                return bot.edit_message_text(chat_id=chat_id, message_id=self.message_id, text=self.text,
                                             parse_mode='HTML',
                                             reply_markup=self.convert_buttons())
            print('-start-edit-message-2-')
            return bot.edit_message_text(chat_id=chat_id, message_id=self.message_id, text=self.text, parse_mode='HTML')
        print('step 4')
        if len(self.get_buttons()) > 0:
            print('-exsist-buttons-')
            if self.text:
                print('exsist-text-')
                bot.send_message(chat_id, self.text, parse_mode='HTML', reply_markup=self.convert_buttons())
        else:
            print('-send-message-')
            bot.send_message(chat_id, self.text, parse_mode='HTML')
        print('-nothing-')
        self.dynamic_buttons = []
        db.session.remove()
        global global_var

        global_var = dict()

    def render_from_custom_viewe(self, old_screen, **kwargs):
        old_func_name = self.def_name
        self.def_name = ''
        self.text = kwargs['screen'].text
        
        if 'user' in kwargs:
            self.render(old_screen, user=kwargs['user'])
        elif 'chat_id' in kwargs:
            self.render(old_screen, chat_id=kwargs['chat_id'])
        
        self.def_name = old_func_name

    def convert_buttons(self):
        keyboard = types.InlineKeyboardMarkup()
        for button in self.get_buttons():
            if self.detect_url(button.link):
                keyboard.add(types.InlineKeyboardButton(text=button.name, url=button.link))
            else:
                keyboard.add(types.InlineKeyboardButton(text=button.name, callback_data=button.link))
        return keyboard

    def get_buttons(self):
        # return self.buttons
        print('-start-check-buttons-')
        print(self.dynamic_buttons)
        print(self.buttons)
        if len(self.dynamic_buttons) < 1:
            return self.buttons
        return self.dynamic_buttons

    def get_button_by_link(self, link):
        for button in self.buttons:
            if button.link == link:
                return button
        return False

    def get_week_screen(self, week_nubmer):
        return self.query.filter_by(link='/shedule_' + week_nubmer).first()

    def detect_url(self, link):
        return link.find('http') == 0

    def get_subject_by_name(self):
        self.dynamic_buttons = []
        return Subject().query.filter_by(name=self.name).first()

    def get_hw_by_user(self):
        return Homework().query.filter_by(complete=False)

    def add_button(self, text, link, sort):
        screen_button = ScreenButton()
        screen_button.name = text
        screen_button.link = link
        screen_button.sort = sort
        return self.dynamic_buttons.append(screen_button)

    def sort_buttons(self, **kwargs):
        orders = []
        buttons = []

        button_list = self.dynamic_buttons if 'dynamic' in kwargs else self.buttons

        for button in button_list:
            orders.append(button.sort)
            buttons.append(button)

        orders.sort()
        print(orders)

        if 'dynamic' in kwargs:
            self.dynamic_buttons = []
        else:
            self.buttons.clear()

        for order in orders:
            for button in buttons:
                if button.sort == order:
                    if 'dynamic' in kwargs:
                        self.dynamic_buttons.append(button)
                    else:
                        self.buttons.append(button)
                    buttons.remove(button)
                    break

    def dynamic_static_collapse(self):
        for button in self.buttons:
            self.dynamic_buttons.append(button)

    @property
    def get_type(self):
        return self.TYPE[self.type]


class ScreenButton(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)
    link = db.Column(db.String(255), unique=False)
    sort = db.Column(db.Integer)
    screen = db.Column(db.Integer, db.ForeignKey('screen.id'), nullable=False)

    def __repr__(self):
        return '<Кнопка %r>' % self.name


class Group(db.Model):
    _tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    users = db.relationship('User', backref='group_users', lazy=True)
    menus = db.relationship('Menu', backref='group_menus', lazy=True)

    def __repr__(self):
        return '<Группа %r>' % self.name


class User(db.Model):
    _tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    group = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    homeworks = db.relationship('Homework', backref='user_hw', lazy=True)

    def __repr__(self):
        return '<Пользователь %r>' % self.id

    def is_group(self):
        if self.group  and self.group > 0:
            return True

        self.get_start_screen()
        return False

    def get_menu_list(self):
        pass

    def get_start_screen(self):
        keyboard = types.ReplyKeyboardRemove()
        self.send_button('Здравствуйте', keyboard)
        start_screen = Screen().query.filter_by(link='/start').first()
        start_screen.render(old_screen=False, user=self)

    def send_button(self, text, buttons):
        bot.send_message(self.chat_id, text, reply_markup=buttons)

    def edit_message(self, text, message_id, **kwargs):
        chat_id = kwargs['chat_id'] if 'chat_id' in kwargs else self.chat_id
        if 'buttons' in kwargs:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text,
                                  reply_markup=kwargs['buttons'])
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        return True


class Menu(db.Model):
    _tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    group = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    enable = db.Column(db.Boolean, default=True, nullable=False)
    items = db.relationship('MenuItem', backref='menu_items', lazy=True, order_by="MenuItem.row")

    def __repr__(self):
        return '<Меню %r>' % self.name

    def get_menu_item(self, text):
        for item in self.items:
            if item.name == text:
                return item
        return False


class MenuItem(db.Model):
    _tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False)
    link = db.Column(db.String(255), unique=False)
    menu = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    col = db.Column(db.Integer)
    row = db.Column(db.Integer)

    def __repr__(self):
        return '<Пункт %r>' % self.name


class Subject(db.Model):
    _tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    gd_link = db.Column(db.String(500))
    Homeworks = db.relationship('Homework', backref='subject_hw', lazy=True)

    def __repr__(self):
        return '<Предмет %r>' % self.name


class Homework(db.Model):
    _tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    text = db.Column(db.String(2000))
    complete = db.Column(db.Boolean, default=False, nullable=False)
    text_archive = db.Column(db.Boolean, default=False, nullable=False)
    time_stamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return '<Дз %r>' % self.name

    def get_subject_name(self):
        subject = Subject().query.filter_by(id=self.subject).first()
        if not subject:
            return ''

        return subject.name

    def save_temp_data_as_hw(self, temp):

        pass


# class Schedule(db.Model):
#     _tablename__ = 'schedule'
#     pass
