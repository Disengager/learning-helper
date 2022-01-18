# -*- coding: utf8 -*-

import json
import datetime
import inspect
import telebot
from telebot import types
from settings import *
# from robokassa import Robokassa
from survey import *
from google_drive import Sheet
from parser import Getuniq

bot = telebot.TeleBot(token)
# content = Content(token=GOOGLE_RESPONSE_TOKEN, init_items=True)

class Screen:
    link = ""
    chat_id = -1
    message_id = -1
    text = ""
    buttons = False

    def __init__(self, **kwargs):
        self.link = kwargs['link']
        self.chat_id = kwargs['chat_id']
        if 'text' in kwargs:
            self.text =  kwargs['text']
        self.message_id = kwargs['message_id']
        if "buttons" in kwargs:
            self.buttons = kwargs['buttons']

    def render(self, new_screen):
        print(str(self.chat_id))
        if new_screen:
            if self.buttons:
                bot.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=self.text,
                                      reply_markup=self.buttons)
            else:
                bot.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=self.text)
            content.get_translate_items()
            return False

        if self.buttons:
            if self.text:
                bot.send_message(self.chat_id, self.text, reply_markup=self.buttons)
        else:
            bot.send_message(self.chat_id, self.text)

        content.get_translate_items()


class Menu:
    screens = dict()
    client = False
    new_screen = False
    link = False
    CANCEL_BUTTON = 'Отмена'

    def __init__(self, **kwargs):
        if "message" in kwargs:

            events = inspect.getmembers(self, predicate=inspect.ismethod)
            home_data = self.home(is_index=True)

            if home_data:
                self.screens[home_data[0]] = Screen(link=home_data[0], text=home_data[1],
                                                    message_id=kwargs['message'].message_id,
                                                    chat_id=kwargs['message'].chat.id)
            for event in events:
                if 'screen' in event[0] and 'dynamic' in event[0]:
                    method_data = event[1](is_index=True)
                    if method_data:
                        self.screens[method_data[0]] = Screen(link=method_data[0], text=method_data[1],
                                                              message_id=kwargs['message'].message_id,
                                                              chat_id=kwargs['message'].chat.id)

            self.client = Client(kwargs['message'])
            self.message = kwargs['message']

            if self.client:
                self.home()
                self.screen_help_dynamic()

    def __get_link_list__(self):
        links = []
        events = inspect.getmembers(self, predicate=inspect.ismethod)

        home_data = self.home(is_index=True)
        if home_data:
            links.append(home_data[0])

        for event in events:
            if 'screen' in event[0] and 'dynamic' in event[0]:
                method_data = event[1](is_index=True)
                if method_data:
                    links.append(method_data[0])

        return links

    # Прослушивание эвентов. Сюда добавляютс функции на агруку различных экранов, для генерации динамического контента
    # Функция выывается при генерации любого экрана
    def events(self, link):
        self.link = link
        events = inspect.getmembers(self, predicate=inspect.ismethod)
        for event in events:
            if 'screen' in event[0] and 'dynamic' in event[0]:
                event[1]()

    # Функция редиректа,запусающая вывод определённого экрана
    def redirect(self, link):
        if self.link:
            link = self.link
        if not link and not self.screens_exist():
            return False
        if link in self.screens:
            self.screens[link].render(self.new_screen)

    # Функция указывающая, будет ли следующий экран открыт в текущем сообщение или будет выслан отдельным
    def one_screen(self):
        self.new_screen = True

    # Проверка существования экранов
    def screens_exist(self):
        return len(self.screens) > 0

    # Генеация и вывод главного меню
    def home(self, **kwargs):
        sc_link = '/home'
        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter
        if not sc_link in self.screens:
            return False
        keyboard = types.InlineKeyboardMarkup()
        db_manager = DbManager()
        roles = dict()
        result = dict()
        admin_role = db_manager.get_item(table='role', where='name = \'admin\'')
        user_roles = self.client.get_role_from_account()
        not_roles = True
        is_admin = False
        for role in user_roles:
            if role != admin_role['role_id']:
                not_roles = False
            else:
                is_admin = True

        # if not_roles:
        #     keyboard.add(self.screen_login_startup_dynamic(get_button=1, button_name='Вход для бизнесов'))
        #     keyboard.add(self.screen_login_investor_dynamic(get_button=1, button_name='Вход для инвесторов'))
        #     keyboard.add(self.screen_login_worker_dynamic(get_button=1, button_name='Вход для сотрудников'))
        #     keyboard.add(self.screen_login_partner_dynamic(get_button=1, button_name='Вход для партнёров'))
        #     if is_admin:
        #         keyboard.add(self.screen_admin_dynamic(get_button=1, button_name='Админ'))
        #
        #     self.screens[sc_link].buttons = keyboard
        #     db_manager.close()
        #     return False

        all_roles = db_manager.query(
            'SELECT role.role_id, role.name, role.caption, role.is_public, role_group.name as group_name, role_group.caption as group_caption, role.role_group_id FROM role INNER JOIN role_group ON role.role_group_id = role_group.role_group_id')
        for role in all_roles:
            result[role['role_id']] = role
            if role['is_public']:
                roles[role['role_group_id']] = role
        all_roles = result
        account_roles = db_manager.get_items(table="user_role_additional",
                                             where='user_id = ' + str(self.client.user['user_id']))

        if self.client.role:
            roles[all_roles[self.client.role['role_id']]['role_group_id']] = all_roles[self.client.role['role_id']]

        if account_roles:
            for role in account_roles:
                if role['role_id'] in all_roles:
                    roles[all_roles[role['role_id']]['role_group_id']] = all_roles[role['role_id']]

        for role in sorted(roles):
            keyboard.add(types.InlineKeyboardButton(text=roles[role]['group_caption'],
                                                    callback_data='/' + roles[role]['group_name'] + '[=_=]' +
                                                                  self.client.user['login']))
        self.screens[sc_link].buttons = keyboard
        db_manager.close()

    # Именение текста в /help
    def screen_help_dynamic(self, **kwargs):
        sc_link = '/help'

        if 'is_index' in kwargs:
            return [sc_link, content.get_item(sc_link)]

        return True

    # Вывод доступны ролей для группы стартап
    def screen_startup_dynamic(self, **kwargs):
        sc_link = '/startup'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.events('/learner')
        self.redirect('/learner')
        # self.get_role_by_group('startup')

    # Вывод доступны ролей для группы сотрудник
    def screen_worker_dynamic(self, **kwargs):
        if 'get_button' in kwargs:
            return self.get_role_by_group('worker', get_button=True, button_name=kwargs['button_name'])

        if 'is_index' in kwargs:
            return self.get_role_by_group('worker', is_index=True)

        if 'get_survey' in kwargs:
            return self.get_role_by_group('worker', get_survey=True, survey=kwargs['survey'])

        self.get_role_by_group('worker')

    # Вывод доступны ролей для группы сервис
    def screen_service_dynamic(self, **kwargs):
        sc_link = '/service'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.events('/admin')
        self.redirect('/admin')

    # Вывод доступны ролей для группы партнёр
    def screen_partner_dynamic(self, **kwargs):
        if 'get_button' in kwargs:
            return self.get_role_by_group('partner', get_button=True, button_name=kwargs['button_name'])

        if 'is_index' in kwargs:
            return self.get_role_by_group('partner', is_index=True)

        if 'get_survey' in kwargs:
            return self.get_role_by_group('partner', get_survey=True, survey=kwargs['survey'])

        self.get_role_by_group(group='partner')

    # Генерация списка доступных ролей, под указанную группу
    def get_role_by_group(self, group, **kwargs):
        sc_link = '/' + group

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        keyboard = types.InlineKeyboardMarkup()
        result = dict()
        roles = dict()

        all_roles = db_manager.query(
            'SELECT role.role_id, role.name, role.caption, role.is_public, role_group.name as group_name, role.role_group_id FROM role INNER JOIN role_group ON role.role_group_id = role_group.role_group_id AND role_group.name = \'' + group + '\' ')

        account_roles = db_manager.get_items(table="user_role_additional",
                                             where='user_id = ' + str(self.client.user['user_id']))

        for role in all_roles:
            result[role['role_id']] = role
            if role['is_public']:
                roles[role['role_id']] = role
        all_roles = result

        if self.client.role:
            if self.client.role['role_id'] in all_roles:
                roles[self.client.role['role_id']] = all_roles[self.client.role['role_id']]

        if account_roles:
            for role in account_roles:
                if role['role_id'] in all_roles:
                    roles[role['role_id']] = all_roles[role['role_id']]

        for role in roles:
            keyboard.add(types.InlineKeyboardButton(text=roles[role]['caption'],
                                                    callback_data='/' + roles[role]['name'] + '[=_=]' + self.client.user['login']))

        if 'buttons' in kwargs:
            for button in kwargs['buttons']:
                keyboard.add(button)

        keyboard.add(self.home(get_button=True, button_name='Назад'))
        db_manager.close()
        self.screens['/' + group].buttons = keyboard

    # Вывод панели админа
    def screen_admin_dynamic(self, **kwargs):
        sc_link = '/admin'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        # keyboard.add(self.just_button('Редактирование заявок \nна лидогенерацию',
        #                               '/orders_edit[=_=]' + self.client.user['login']))
        keyboard.add(self.screen_users_edit_dynamic(get_button=True, button_name='Редактирование пользователей'))
        # keyboard.add(self.just_button('Редактирование групп ролей', '/role_groups_edit[=_=]' + self.client.user['login']))
        # keyboard.add(self.just_button('Редактирование уроков', '/lessons_edit[=_=]' + self.client.user['login']))
        # keyboard.add(self.just_button('Редактирование ролей', '/roles_edit[=_=]' + self.client.user['login']))
        # keyboard.add(self.just_button('Назад', '/service[=_=]' + self.client.user['login']))
        keyboard.add(self.home(get_button=True, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    # Вывод панели ученика
    def screen_learner_dynamic(self, **kwargs):
        sc_link = '/learner'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        db_manager = DbManager()
        # all_roles = db_manager.query(
        #     'SELECT role.role_id, role.name, role.caption, role_group.name as group_name, role.role_group_id FROM role INNER JOIN role_group ON role.role_group_id = role_group.role_group_id AND role.name = \'learner\' ')

        roles = self.client.get_role_from_account(db_manager=db_manager, client=self.client.user['login'])
        learner_role = db_manager.get_item(table='role', where='name = \'learner\'')['role_id']
        role_exist = False
        for role in roles:
            if role == learner_role:
                role_exist = True
        if not role_exist:
            keyboard.add(self.screen_detroit_become_learner_dynamic(get_button=True,
                                                                    button_name=content.get_item('tariff_button_name_24')))
            keyboard.add(self.screen_detroit_become_learner_7_dynamic(get_button=True,
                                                                      button_name=content.get_item('tariff_button_name_7')))
            keyboard.add(self.screen_detroit_become_learner_31_dynamic(get_button=True,
                                                                       button_name=content.get_item('tariff_button_name_31')))
            keyboard.add(self.screen_detroit_become_learner_365_dynamic(get_button=True,
                                                                        button_name=content.get_item('tariff_button_name_365')))
            keyboard.add(self.home(get_button=True, button_name='Назад'))
            self.screens[sc_link].buttons = keyboard
            return True

        keyboard.add(self.screen_order_services_dynamic(get_button=True, button_name='Заказать услуги'))

        if not self.client.is_learner():
            self.client.lesson = db_manager.get_item(table='lesson', where='lesson_id =' + str(self.client.user['lesson_id']))
        if self.client.lesson:
            keyboard.add( types.InlineKeyboardButton(text='Перейти к последнему уроку',
                                                     callback_data='/get_current_lesson[=_=]'+ self.client.user['login'] ))

        keyboard.add(self.home(get_button=True, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

        # Вывод панели ученика

    def screen_bot_developer_dynamic(self, **kwargs):
        sc_link = '/bot_developer'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        db_manager = DbManager()
        roles = self.client.get_role_from_account(db_manager=db_manager, client=self.client.user['login'])
        learner_role = db_manager.get_item(table='role', where='name = \'bot_developer\'')['role_id']
        role_exist = False

        for role in roles:
            if role == learner_role:
                role_exist = True

        if not role_exist:
            keyboard.add(self.screen_worker_dynamic(get_button=True, button_name='Назад'))
            self.screens[sc_link].buttons = keyboard
            return True
        keyboard.add(self.screen_chat_bot_order_dynamic(get_button=True, button_name='Список заявок'))
        keyboard.add(self.screen_worker_dynamic(get_button=True, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    # Вывод панели лидогенератора
    def screen_lidogenerator_dynamic(self, **kwargs):
        sc_link = '/lidogenerator'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        db_manager = DbManager()
        role_exist = False

        all_roles = db_manager.query(
            'SELECT role.role_id, role.name, role.caption, role_group.name as group_name, role.role_group_id FROM role INNER JOIN role_group ON role.role_group_id = role_group.role_group_id AND role.name = \'lidogenerator\' ')

        role_additional = db_manager.get_items(table='user_role_additional',
                                               where='user_id = ' + str(self.client.user['user_id']))

        if not all_roles:
            return False

        if not role_additional:
            if not self.client.role or self.client.role['role_id'] != all_roles[0]['role_id']:
                keyboard.add(types.InlineKeyboardButton(text='Стать лидогенератором',
                                                        callback_data='/detroit_become_lidogenerator[=_=]' +
                                                                      self.client.user['login']))
            elif self.client.role['role_id'] == all_roles[0]['role_id']:
                keyboard.add( self.screen_get_taken_order_list_dynamic(button_name='Мои заявки', get_button=True))
                keyboard.add( self.screen_order_list_dynamic(button_name='Заявки на лидогенерацию', get_button=True))
        else :
            for role in role_additional:
                if role['role_id'] == all_roles[0]['role_id']:
                    keyboard.add( self.screen_get_taken_order_list_dynamic(button_name='Мои заявки', get_button=True))
                    keyboard.add( self.screen_order_list_dynamic(button_name='Заявки на лидогенерацию', get_button=True))
                    role_exist = True
            if not role_exist:
                if not self.client.role or self.client.role['role_id'] != all_roles[0]['role_id']:
                    keyboard.add(types.InlineKeyboardButton(text='Стать лидогенератором',
                                                            callback_data='/detroit_become_lidogenerator[=_=]' +
                                                                          self.client.user['login']))
                elif self.client.role['role_id'] == all_roles[0]['role_id']:
                    keyboard.add( self.screen_get_taken_order_list_dynamic(button_name='Мои заявки', get_button=True))
                    keyboard.add( self.screen_order_list_dynamic(button_name='Заявки на лидогенерацию', get_button=True))

        for role in all_roles:
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='/' + role['group_name'] + '[=_=]' + self.client.user['login']))
            break
        self.screens[sc_link].buttons = keyboard

    # Вывод кнопок на панели проверяющего
    def screen_validator_dynamic(self, **kwargs):
        sc_link = '/validator'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Проверить задания учеников', callback_data='/list_learner[=_=]' + self.client.user['login']))
        db_manager = DbManager()
        all_roles = db_manager.query(
            'SELECT role.role_id, role.name, role.caption, role_group.name as group_name, role.role_group_id FROM role INNER JOIN role_group ON role.role_group_id = role_group.role_group_id AND role.name = \'validator\' ')
        for role in all_roles:
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='/' + role['group_name'] + '[=_=]' + self.client.user['login']))
            break
        self.screens['/validator'].buttons = keyboard

    def screen_programmer_dynamic(self, **kwargs):
        sc_link = '/programmer'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link or sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(self.screen_programmer_order_dynamic(get_button=True, button_name='Оставить резюме'))
        keyboard.add(self.screen_worker_dynamic(get_button=True, button_name='Назад'))

        self.screens[sc_link].buttons = keyboard

    # Вывод списка учеников
    def screen_list_learner_dynamic(self, **kwargs):
        sc_link = '/list_learner'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        keyboard = types.InlineKeyboardMarkup()
        users_answer = dict()

        role = db_manager.get_item(table='role', where='name = \'learner\'')

        if not role:
            return False

        answers = db_manager.get_items(table='user_answer', where='answer_done = True')
        learners = self.client.get_accounts_by_role(role=role)

        for answer in answers:
            users_answer[ answer['user_id'] ] = True

        for learner in learners:
            if learner['user_id'] in users_answer:
                keyboard.add(types.InlineKeyboardButton(text=learner['login'],
                                                        callback_data='/get_answer_' + learner['login'] + '[=_=]'
                                                                      + self.client.user['login']))

        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='/validator[=_=]' + self.client.user['login']))
        self.screens[sc_link].buttons = keyboard

    # Функция, запускающая регистрацию на лидогенератора
    def screen_detroit_become_lidogenerator_dynamic(self, **kwargs):
        sc_link = '/detroit_become_lidogenerator'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_lidogenerator_registr,
                                                       finish_str='Регистрация успешно завершена',
                                                       cancel=cancel_lidogenerator_registr,
                                                       cancel_str='Отмена регистрации')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.create_sheet_survey(sc_link=sc_link, column_name='lidogenerator_registr')

    def screen_detroit_become_learner_dynamic(self, **kwargs):
        sc_link = '/detroit_become_learner_1'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        trans_type = db_manager.get_item(table='transaction_types', where='name=\'become_learner_1\'')

        if not trans_type:
            return False

        self.get_detroit_become_learner(out_sum=trans_type['price'], db_manager=db_manager,
                                        sc_link=sc_link, trans_type=trans_type)

    def screen_detroit_become_learner_7_dynamic(self, **kwargs):
        sc_link = '/detroit_become_learner_7'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        trans_type = db_manager.get_item(table='transaction_types', where='name=\'become_learner_7\'')

        if not trans_type:
            return False

        self.get_detroit_become_learner(out_sum=trans_type['price'], db_manager=db_manager,
                                        sc_link=sc_link, trans_type=trans_type)

    def screen_detroit_become_learner_31_dynamic(self, **kwargs):
        sc_link = '/detroit_become_learner_31'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        trans_type = db_manager.get_item(table='transaction_types', where='name=\'become_learner_31\'')

        if not trans_type:
            return False

        self.get_detroit_become_learner(out_sum=trans_type['price'], db_manager=db_manager,
                                        sc_link=sc_link, trans_type=trans_type)

    def screen_detroit_become_learner_365_dynamic(self, **kwargs):
        sc_link = '/detroit_become_learner_365'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        trans_type = db_manager.get_item(table='transaction_types', where='name=\'become_learner_365\'')

        if not trans_type:
            return False

        self.get_detroit_become_learner(out_sum=trans_type['price'], db_manager=db_manager,
                                        sc_link=sc_link, trans_type=trans_type)

    def screen_programmer_order_dynamic(self, **kwargs):
        sc_link = '/order_programmer'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_order_programmer,
                                                       finish_str='Резюме отправлена',
                                                       cancel=cancel_order_programmer,
                                                       cancel_str='Отмена составления резюме')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.create_sheet_survey(sc_link=sc_link, column_name='programmer_resume')

    # Вывод окна с услугами
    def screen_order_services_dynamic(self, **kwargs):
        sc_link = '/order_services'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        db_manager = DbManager()
        role = db_manager.get_item(table='role', where='name = \'learner\'')
        if role['role_id'] in self.client.get_role_from_account():
            keyboard.add(self.screen_order_lidogeneration_dynamic(get_button=True, button_name='Заказать лидогенерацию'))
            keyboard.add(self.screen_order_chatbot_develop_dynamic(get_button=True, button_name='Заказать разработку чат бота'))
        keyboard.add(self.screen_startup_dynamic(get_button=True, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    # Функция, запускающая процесс содания заявки
    def screen_order_lidogeneration_dynamic(self, **kwargs):
        sc_link = '/order_lidogeneration'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_order_services,
                                                       finish_str='Заявка успешно создана',
                                                       cancel=cancel_order_services,
                                                       cancel_str='Отмена оформления заявки')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.create_sheet_survey(sc_link=sc_link, column_name='order_lidogeneration')

    # Функция, запускающая процесс содания заявки
    def screen_order_chatbot_develop_dynamic(self, **kwargs):
        sc_link = '/order_chatbot_develop'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_order_chatbot,
                                                       finish_str='Заявка успешно создана',
                                                       cancel=cancel_order_chatbot,
                                                       cancel_str='Отмена оформления заявки')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        self.create_sheet_survey(sc_link=sc_link, column_name='order_chatbot_develop')

    # Функция, запускающая получение урока и меняющая роль на ученика
    def screen_get_current_lesson_dynamic(self, **kwargs):
        sc_link = '/get_current_lesson'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        role = db_manager.get_item(table='role', where='name =\'learner\'')

        if not self.client.is_learner():
            db_manager.update(table='account', set='role_id =' + str(role['role_id']),
                              where='user_id =' + str(self.client.user['user_id']) )
            db_manager.remove(table='user_role_additional', where='user_id =' + str(self.client.user['user_id']) + ' AND ' +
                                'role_id =' + str(role['role_id']) )
            db_manager.add_additional_role(user_id=self.client.user['user_id'],
                                           role_id=self.client.user['role_id'])
            self.client.user['role_id'] = role['role_id']
            self.client.authorization_user(db_manager=db_manager)

        self.client.get_lesson()

    # Вывод ответов на проверку, для выбранного ученика
    def screen_get_answer_dynamic(self, **kwargs):
        sc_link = '/get_answer'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        role = db_manager.get_item(table='role', where='name = \'learner\'')
        learners = self.client.get_accounts_by_role(role=role)
        all_answer = ''
        for learner in learners:
            if self.link == '/get_answer_' + learner['login']:

                lesson = db_manager.get_item(table='lesson', where='lesson_id =' + str(learner['lesson_id']))
                answers = db_manager.get_items(table='user_answer', where='user_id =' + str(learner['user_id']) )

                all_answer += '<b>' + content.get_item('answer_for_tracker_learner_caption') + '</b> ' + learner['login'] + '\n\n'

                if lesson:
                    all_answer += '<b>' + content.get_item('answer_for_tracker_current_lesson_caption') + '</b> ' + str(lesson['number']) + '\n\n'

                if answers:
                    for answer in answers:
                        if answer['lesson_done']:
                            parse_answer = answer['answer'].split('[=_=]')
                            question = lesson['questions'].split('[=_=]')
                            all_answer += self.client.get_all_answer(parse_answer=parse_answer, question=question)
                            if answer['answer_done']:
                                buttons = []
                                buttons.append(
                                    types.InlineKeyboardButton(text=self.client.VALIDATOR_RIGHT_BUTTON,
                                                               callback_data=self.client.VALIDATOR_RIGHT_COMMAND + '[=_=]' +
                                                                             learner['login']))
                                buttons.append(
                                    types.InlineKeyboardButton(text=self.client.VALIDATOR_WRONG_BUTTON,
                                                               callback_data=self.client.VALIDATOR_WRONG_COMMAND + '[=_=]' +
                                                                             learner['login']))

                                self.client.send_html_buttons(text=all_answer, buttons=buttons,
                                                              custom_chat=self.client.user['chat'],
                                                              add_keyboard=self.just_button(text='назад',
                                                                                            callback_data='/exit'))
                            else:
                                self.client.send_html(all_answer)
                        else:
                            self.client.send(content.get_item('answer_for_tracker_no_answer'))

    def screen_chat_bot_order_dynamic(self, **kwargs):
        sc_link = '/get_chatbot_order'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        orders = db_manager.get_items(table='orders', where='type = ' + str(ORDER_CHATBOT_ID))

        if not orders:
            if sc_link + '_' in self.link:
                self.screens[self.link] = Screen(link=self.link, text=content.get_item(sc_link),
                                                 message_id=self.client.message.message_id,
                                                 chat_id=self.client.message.chat.id)
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(self.screen_bot_developer_dynamic(get_button=True, button_name='Назад'))
            self.screens[sc_link].buttons = keyboard
            return False

        if sc_link + '_' in self.link:
            for order in orders:
                if sc_link + '_' + str(order['order_id']) == self.link:
                    result = self.get_order_card(orders=orders, order_id=order['order_id'], get_order_link=sc_link + '_',
                                                 taken=1, only_next_last=1, chatbot=1)
                    if result:
                        self.screens[self.link] = Screen(link=self.link, text=result['text'], buttons=result['buttons'],
                                                         message_id=self.client.message.message_id,
                                                         chat_id=self.client.message.chat.id)
                    break
            return True

        for order in orders:
            result = self.get_order_card(orders=orders, order_id=order['order_id'], first=True,
                                         get_order_link=sc_link + '_', taken=1, only_next_last=1, chatbot=1)
            if result and result['text']:
                self.screens[sc_link].text = result['text']

            if result and result['text']:
                self.screens[sc_link].buttons = result['buttons']
            break



        db_manager.close()

    def screen_order_list_dynamic(self, **kwargs):
        sc_link = '/order_list'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        user_order = db_manager.get_items(table='user_order', where='user_id = ' + str(self.client.user['user_id']))
        orders = db_manager.get_items(table='orders', where='type = ' + str(ORDER_LIDGEN_ID))

        if not orders:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(self.screen_lidogenerator_dynamic(get_button=True, button_name='Назад'))
            self.screens[sc_link].buttons = keyboard
            return False

        if user_order:
            orders_taken = dict()

            for order in user_order:
                orders_taken[order['order_id']] = True

            view_orders = []

            for order in orders:
                if not order['order_id'] in orders_taken:
                    view_orders.append(order)
        else:
            view_orders = orders

        for order in view_orders:
            result = self.get_order_card(orders=view_orders, order_id=order['order_id'], first=True,
                                         get_order_link='/get_order_')
            if result and result['text']:
                self.screens[sc_link].text = result['text']

            if result and result['text']:
                self.screens[sc_link].buttons = result['buttons']
            break

        db_manager.close()

    def screen_get_taken_order_list_dynamic(self, **kwargs):
        sc_link = '/get_taken_order'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if sc_link != self.link:
            return False
        db_manager = DbManager()
        orders = self.client.get_taken_orders(db_manager=db_manager)

        if not orders:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(self.screen_lidogenerator_dynamic(get_button=True, button_name='Назад'))
            self.screens[sc_link].buttons = keyboard
            return False

        for order in orders:
            result = self.get_order_card(orders=orders, order_id=order['order_id'], first=True,
                                         get_order_link=sc_link + '_', taken=1)
            if result:
                if result['text']:
                    self.screens[sc_link].text = result['text']
                if result['buttons']:
                    self.screens[sc_link].buttons = result['buttons']
            break

        db_manager.close()

    def screen_get_taken_order_dynamic(self, **kwargs):
        sc_link = '/get_taken_order_'

        if 'is_index' in kwargs:
            return False

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        orders = self.client.get_taken_orders(db_manager=db_manager)
        if not orders:
            return False

        for order in orders:
            if sc_link + str(order['order_id']) == self.link:
                result = self.get_order_card(orders=orders, order_id=order['order_id'], get_order_link=sc_link, taken=1)
                if result:
                    self.screens[self.link] = Screen(link=self.link, text=result['text'], buttons=result['buttons'],
                                                     message_id=self.client.message.message_id,
                                                     chat_id=self.client.message.chat.id)
                break
        db_manager.close()

    def screen_get_order_dynamic(self, **kwargs):
        sc_link = '/get_order'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        # user_orders = db_manager.get_items(table='user_order', where=)
        user_order = db_manager.get_items(table='user_order', where='user_id = ' + str(self.client.user['user_id']))
        orders = db_manager.get_items(table='orders', where='type = ' + str(ORDER_LIDGEN_ID))

        if not orders:
            return False

        if user_order:
            orders_taken = dict()

            for order in user_order:
                orders_taken[order['order_id']] = True

            view_orders = []

            for order in orders:
                if not order['order_id'] in orders_taken:
                    view_orders.append(order)
        else:
            view_orders = orders

        for order in view_orders:
            if '/get_order_' + str(order['order_id']) == self.link:
                result = self.get_order_card(orders=view_orders, order_id=order['order_id'], get_order_link='/get_order_')
                if result:
                    self.screens[self.link] = Screen(link=self.link, text=result['text'], buttons=result['buttons'],
                                                     message_id=self.client.message.message_id,
                                                     chat_id=self.client.message.chat.id)
                break

        db_manager.close()

    def screen_take_order_dynamic(self, **kwargs):
        sc_link = '/take_order'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        orders = db_manager.get_items(table='orders', where='type = ' + str(ORDER_LIDGEN_ID))

        if not orders:
            return False

        for order in orders:
            if sc_link + '_' + str(order['order_id']) == self.link:
                db_manager.add_user_order(order_id=  str(order['order_id']),
                                          user_id = str(self.client.user['user_id']))
                self.client.send(content.get_item('order_taken_message'))
                self.events('/lidogenerator')
                self.redirect('/lidogenerator')
                break

    def screen_repay_order_dynamic(self, **kwargs):
        sc_link = '/repay_order'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link:
            return False

        db_manager = DbManager()
        orders = db_manager.get_items(table='orders', where='type = ' + str(ORDER_LIDGEN_ID))

        if not orders:
            return False

        for order in orders:
            if sc_link + '_' + str(order['order_id']) == self.link:
                db_manager.remove(table='user_order', where='order_id = ' + str(order['order_id']) + ' AND user_id = ' +
                                                            str(self.client.user['user_id']))
                self.client.send(content.get_item('order_return_message'))
                self.events('/lidogenerator')
                self.redirect('/lidogenerator')
                break

    def screen_users_edit_dynamic(self, **kwargs):
        sc_link = '/users_edit'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if sc_link != self.link:
            return False

        db_manager = DbManager()
        keyboard = types.InlineKeyboardMarkup()
        users = db_manager.get_items(table='account')
        for user in users:
            keyboard.add(self.just_button(user['login'], '/users_edit_' + user['login'] + '[=_=]' + self.client.user['login']))
        # keyboard.add(self.just_button('Добавить пользователя', '/users_add[=_=]' + self.client.user['login']))
        keyboard.add(self.screen_admin_dynamic(get_button=True, button_name='Назад'))
        keyboard.add(self.home(get_button=True, button_name='В главное меню'))
        self.screens[sc_link].buttons = keyboard

    def screen_user_edit_login_dynamic(self, **kwargs):
        sc_link = '/users_edit'

        if 'is_index' in kwargs:
            return False

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link or sc_link == self.link:
            return False

        db_manager = DbManager()
        users = db_manager.get_items(table='account')
        keyboard = types.InlineKeyboardMarkup()
        detect_user = False

        for user in users:
            if self.link == '/users_edit_' + user['login']:
                detect_user = user

        if not detect_user:
            return False

        roles_text = ''
        user_roles = self.client.get_role_from_account(db_manager=db_manager, client=detect_user['login'])
        if user_roles:
            i = 0
            roles_text += 'У пользователя есть роли: '
            for role in user_roles:
                i += 1
                separator = ', ' if i < len(user_roles) else ' '
                if role:
                    roles_text +=  db_manager.get_item(table='role', where='role_id = ' + str(role))['caption'] + separator


        link = '/users_edit_' + detect_user['login']
        keyboard.add(self.just_button('Удалить пользователя', '/users_delete_account_' + detect_user['login'] + '[=_=]' + self.client.user['login']))
        keyboard.add( self.just_button('Добавить роли', '/users_add_role_' + detect_user['login'] + '[=_=]'  + self.client.user['login'] ) )
        keyboard.add( self.just_button('Удалить роли', '/users_delete_role_' + detect_user['login'] + '[=_=]'  + self.client.user['login'] ) )
        keyboard.add( self.screen_users_edit_dynamic(get_button=True, button_name='Назад') )
        keyboard.add(self.home(get_button=True, button_name='В главное меню'))

        self.screens[ link ] = Screen(link=link, text='Пользователь ' + detect_user['login'] + '\n\n' + roles_text,
                                      buttons=keyboard,
                                      message_id=self.client.message.message_id,
                                      chat_id=self.client.message.chat.id)

    def screen_users_add_role_login_dynamic(self, **kwargs):
        sc_link = '/users_add_role'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link + '_' in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_add_role_to_user,
                                                       finish_str='Роль добавлена',
                                                       cancel=cancel_add_role_to_user,
                                                       cancel_str='Отмена')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link or sc_link == self.link:
            return False

        db_manager = DbManager()
        roles = db_manager.get_items(table='role')
        roles_text = ''
        login = self.link.split(sc_link + '_')[1]

        survey = Survey(message=self.client.message, client=self.client)
        survey.create(question=content.get_item('admin_select_add_role_message'), link=self.link)


        user_roles = self.client.get_role_from_account(db_manager=db_manager, client=login)
        if user_roles:
            i = 0
            roles_text += content.get_item('admin_select_user_role_message') + ' '
            for role in user_roles:
                i += 1
                separator = ', ' if i < len(user_roles) else ' '
                if role:
                    roles_text +=  db_manager.get_item(table='role', where='role_id = ' + str(role))['caption'] + separator

        btnm = telebot.types.ReplyKeyboardMarkup().row(self.CANCEL_BUTTON)
        btnm.resize_keyboard = True
        self.client.send_button(text=roles_text, button=btnm)
        survey.get_question()

        keyboard = types.InlineKeyboardMarkup()
        for role in roles:
            keyboard.add(self.just_button(text=role['caption'] + (' (публичная роль)' if role['is_public'] else ''),
                                          callback_data=str(role['role_id']) + '[=_=]' + self.client.user['login']))
        self.client.send_button('***доступные роли', keyboard)


        self.screens[self.link] = Screen(link=self.link, text='Пользователь ' + login,
                                    message_id=self.client.message.message_id,
                                    chat_id=self.client.message.chat.id)

    def screen_users_delete_role_dynamic(self, **kwargs):
        sc_link = '/users_delete_role'

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link + '_' in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_delete_role_to_user,
                                                       finish_str='Роль удалена',
                                                       cancel=cancel_delete_role_to_user,
                                                       cancel_str='Отмена')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link or sc_link == self.link:
            return False

        db_manager = DbManager()
        roles = db_manager.get_items(table='role')
        roles_text = ''
        login = self.link.split(sc_link + '_')[1]

        survey = Survey(message=self.client.message, client=self.client)
        survey.create(question=content.get_item('admin_select_delete_role_message'), link=self.link)


        user_roles = self.client.get_role_from_account(db_manager=db_manager, client=login)
        if user_roles:
            i = 0
            roles_text += content.get_item('admin_select_user_role_message') + ' '
            for role in user_roles:
                i += 1
                separator = ', ' if i < len(user_roles) else ' '
                if role:
                    roles_text +=  db_manager.get_item(table='role', where='role_id = ' + str(role))['caption'] + separator

        btnm = telebot.types.ReplyKeyboardMarkup().row(self.CANCEL_BUTTON)
        btnm.resize_keyboard = True
        self.client.send_button(text=roles_text, button=btnm)
        survey.get_question()

        keyboard = types.InlineKeyboardMarkup()
        for role in roles:
            keyboard.add(self.just_button(text=role['caption'] + (' (публичная роль)' if role['is_public'] else ''),
                                          callback_data=str(role['role_id']) + '[=_=]' + self.client.user['login']))
        self.client.send_button('***доступные роли', keyboard)


        self.screens[self.link] = Screen(link=self.link, text='Пользователь ' + login,
                                    message_id=self.client.message.message_id,
                                    chat_id=self.client.message.chat.id)

    def screen_users_delete_account_dynamic(self, **kwargs):
        sc_link = '/users_delete_account'

        right_answer = 'да'
        if 'get_right_answer' in kwargs:
            return right_answer

        if 'get_survey' in kwargs and 'survey' in kwargs:
            if sc_link + '_' in kwargs['survey'].link:
                kwargs['survey'].set_finish_and_cancel(finish=finish_delete_account_to_user,
                                                       finish_str='Аккаунт удалён',
                                                       cancel=cancel_delete_account_to_user,
                                                       cancel_str='Отмена')

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link or sc_link == self.link:
            return False

        db_manager = DbManager()
        roles = db_manager.get_items(table='role')
        roles_text = ''
        login = self.link.split(sc_link + '_')[1]
        user_roles = self.client.get_role_from_account(db_manager=db_manager, client=login)
        if user_roles:
            i = 0
            roles_text += content.get_item('admin_select_user_role_message') + ' '
            for role in user_roles:
                i += 1
                separator = ', ' if i < len(user_roles) else ' '
                roles_text += db_manager.get_item(table='role', where='role_id = ' + str(role))['caption'] + separator

        survey = Survey(message=self.client.message, client=self.client)
        survey.create(question=content.get_item('account_delete_alert'), link=self.link)
        btnm = telebot.types.ReplyKeyboardMarkup().row(self.CANCEL_BUTTON)
        btnm.resize_keyboard = True
        self.client.send_button(text=roles_text, button=btnm)
        survey.get_question()

        keyboard = types.InlineKeyboardMarkup()
        buttons = []
        buttons.append(self.just_button(text='да',callback_data=right_answer + '[=_=]' + self.client.user['login']))
        buttons.append(self.just_button(text='нет',callback_data='нет[=_=]' + self.client.user['login']))
        keyboard.add(*buttons)
        self.client.send_button(content.get_item('account_delete_question'), keyboard)


        self.screens[self.link] = Screen(link=self.link, text='Пользователь ' + login,
                                    message_id=self.client.message.message_id,
                                    chat_id=self.client.message.chat.id)

    def screen_login_startup_dynamic(self, **kwargs):
        sc_link = '/login_startup'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.home(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_investor_dynamic(self, **kwargs):
        sc_link = '/login_investor'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.home(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_worker_dynamic(self, **kwargs):
        sc_link = '/login_worker'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.screen_login_worker_become_dynamic(get_button=1, button_name='Стать сотрудником'))
        keyboard.add(self.screen_login_worker_entry_dynamic(get_button=1, button_name='Вход для сотрудников'))
        keyboard.add(self.home(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_worker_become_dynamic(self, **kwargs):
        sc_link = '/login_worker_become'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link  in self.link:
            return False

        if sc_link != self.link and not sc_link + '*'  in self.link:
            return False

        db_manager = DbManager()
        worker_role = db_manager.get_item(table='role_group', where='name = \'worker\'')
        roles = db_manager.get_items(table='role', where='role_group_id = ' + str(worker_role['role_group_id']))
        i = 0
        where = ' '
        for role in roles:
            i += 1
            if i == 1:
                where += 'role_id = ' + str(role['role_id'])
            else:
                where += ' OR role_id = ' + str(role['role_id'])

        user_roles = db_manager.get_items(table='user_role_additional', where=where)
        i = 0
        for user_role in user_roles:
            if not roles and i == 0:
                where += 'user_id = ' + str(user_role['user_id'])
            else:
                where += ' OR user_id = ' + str(user_role['user_id'])


        workers = db_manager.get_items(table='account', where=where)


        carousel = self.get_carousel(workers, 'user_id', sc_link)
        keyboard = types.InlineKeyboardMarkup()
        if carousel:
            worker = carousel['object']

        keyboard.add(self.screen_login_worker_become_all_dynamic(get_button=1, button_name='Стать сотрудником'))
        if carousel and carousel['buttons']:
            keyboard.add(*carousel['buttons'])
        keyboard.add(self.screen_login_worker_dynamic(get_button=1, button_name='Назад'))

        if sc_link + '*' in self.link:
            self.screens[self.link] = Screen(link=self.link, text= 'Сотрудник: ' + str(worker['login']), buttons=keyboard,
                                             message_id=self.client.message.message_id,
                                             chat_id=self.client.message.chat.id)

        if carousel:
            self.screens[self.link].text = 'Сотрудник: ' + str(worker['login'])
        else:
            self.screens[self.link].text = 'Нет сотрудников'

        self.screens[self.link].buttons = keyboard

    def translate_to_carousel(self, items, id_key):
        result = []
        for item in items:
            result.append({'id': item[id_key], 'object': item})
        return result

    def get_carousel(self, default_items, id_key, sc_lik, **kwargs):
        items = self.translate_to_carousel(default_items, id_key)
        result = dict()
        current_index = 0
        items_index = False
        first = False
        last_index = False
        next_index = False
        buttons = []

        if self.link != sc_lik and sc_lik + '*' in self.link:
            current_index = int(self.link.split(sc_lik + '*')[1])

        i = 0
        for item in items:
            if i == 0:
                first = i
                if current_index == 0:
                    items_index = i
                    current_index = item['id']
                    if i < len(items) - 1:
                        next_index = items[i + 1]['id']
                    break
            if item['id'] == current_index:
                items_index = i
                last_index = items[i - 1]['id']
                if i < len(items) - 1:
                    next_index = items[i + 1]['id']
                break
            i += 1

        next_caption = content.get_item('carousel_next') if not 'next_caption' in kwargs else kwargs['next_caption']
        last_caption = content.get_item('carousel_last') if not 'last_caption' in kwargs else kwargs['last_caption']

        if items_index == first:
            buttons.append(types.InlineKeyboardButton(text=next_caption, callback_data=sc_lik + '*' + str(next_index) + '[=_=]' + self.client.user['login']))
        elif items_index == len(items) - 1:
            buttons.append(types.InlineKeyboardButton(text=last_caption, callback_data=sc_lik + '*' + str(last_index) + '[=_=]' + self.client.user['login']))
        else:
            buttons.append(types.InlineKeyboardButton(text=last_caption, callback_data=sc_lik + '*' + str(last_index) + '[=_=]' + self.client.user['login']))
            buttons.append(types.InlineKeyboardButton(text=next_caption, callback_data=sc_lik + '*' + str(next_index) + '[=_=]' + self.client.user['login']))

        if not items:
            return False

        result['object'] = items[items_index]['object']
        if len(items) > 1:
            result['buttons'] = buttons
        else:
            result['buttons'] = False
        return result

    def screen_login_worker_become_all_dynamic(self, **kwargs):
        sc_link = '/login_worker_become_all'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.screen_login_worker_become_dynamic(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_worker_entry_dynamic(self, **kwargs):
        sc_link = '/login_worker_entry'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        db_manager = DbManager()
        worker_role = db_manager.get_item(table='role_group', where='name = \'worker\'')
        roles = db_manager.get_items(table='role', where='role_group_id = ' + str(worker_role['role_group_id']))
        i = 0
        where = ' '
        for role in roles:
            i += 1
            if i == 1:
                where += 'role_id = ' + str(role['role_id'])
            else:
                where += ' OR role_id = ' + str(role['role_id'])

        user_roles = db_manager.get_items(table='user_role_additional', where=where)
        i = 0
        for user_role in user_roles:
            if not roles and i == 0:
                where += 'user_id = ' + str(user_role['user_id'])
            else:
                where += ' OR user_id = ' + str(user_role['user_id'])

        workers = db_manager.get_items(table='account', where=where)

        carousel = self.get_carousel(workers, 'user_id', sc_link)
        keyboard = types.InlineKeyboardMarkup()
        if carousel:
            worker = carousel['object']

        keyboard.add(self.screen_login_worker_entry_invite_dynamic(get_button=1, button_name='Запросить вход для уже действующего сотрудника'))
        if carousel and carousel['buttons']:
            keyboard.add(*carousel['buttons'])
        keyboard.add(self.screen_login_worker_dynamic(get_button=1, button_name='Назад'))

        if sc_link + '*' in self.link:
            self.screens[self.link] = Screen(link=self.link, text='Сотрудник: ' + str(worker['login']),
                                             buttons=keyboard,
                                             message_id=self.client.message.message_id,
                                             chat_id=self.client.message.chat.id)

        if carousel:
            self.screens[self.link].text = 'Сотрудник: ' + str(worker['login'])
        else:
            self.screens[self.link].text = 'Нет сотрудников'

        self.screens[self.link].buttons = keyboard

    def screen_login_worker_entry_invite_dynamic(self, **kwargs):
        sc_link = '/login_worker_entry_invite'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.screen_login_worker_entry_dynamic(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_partner_dynamic(self, **kwargs):
        sc_link = '/login_partner'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.screen_login_partner_become_dynamic(get_button=1, button_name='Стать партнёром'))
        keyboard.add(self.screen_login_partner_entry_dynamic(get_button=1, button_name='Вход для партнёров'))
        keyboard.add(self.home(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_partner_become_dynamic(self, **kwargs):
        sc_link = '/login_partner_become'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        db_manager = DbManager()
        worker_role = db_manager.get_item(table='role_group', where='name = \'partner\'')
        roles = db_manager.get_items(table='role', where='role_group_id = ' + str(worker_role['role_group_id']))
        i = 0
        where = ' '
        for role in roles:
            i += 1
            if i == 1:
                where += 'role_id = ' + str(role['role_id'])
            else:
                where += ' OR role_id = ' + str(role['role_id'])

        user_roles = db_manager.get_items(table='user_role_additional', where=where)
        i = 0
        for user_role in user_roles:
            if not roles and i == 0:
                where += 'user_id = ' + str(user_role['user_id'])
            else:
                where += ' OR user_id = ' + str(user_role['user_id'])

        workers = db_manager.get_items(table='account', where=where)

        carousel = self.get_carousel(workers, 'user_id', sc_link)
        keyboard = types.InlineKeyboardMarkup()
        if carousel:
            worker = carousel['object']

        keyboard.add(self.screen_login_lidogenerator_become_dynamic(get_button=1, button_name='Стать партнёром'))
        if carousel and carousel['buttons']:
            keyboard.add(*carousel['buttons'])
        keyboard.add(self.screen_login_partner_dynamic(get_button=1, button_name='Назад'))


        if sc_link + '*' in self.link:
            self.screens[self.link] = Screen(link=self.link, text=content.get_item('carousel_worker_caption') + ' ' + str(worker['login']),
                                             buttons=keyboard,
                                             message_id=self.client.message.message_id,
                                             chat_id=self.client.message.chat.id)

        if carousel:
            self.screens[self.link].text = content.get_item('carousel_worker_caption') + ' ' + str(worker['login'])
        else:
            self.screens[self.link].text = content.get_item('carousel_no_worker')

        self.screens[self.link].buttons = keyboard

    def screen_login_lidogenerator_become_dynamic(self, **kwargs):
        sc_link = '/login_lidogenerator'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.just_button(text='Стать Лидогенератором', callback_data='/'))
        keyboard.add(self.just_button(text='Вход для Лидогенераторов', callback_data='/'))
        keyboard.add(self.screen_login_partner_dynamic(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screen_login_partner_entry_dynamic(self, **kwargs):
        sc_link = '/login_partner_entry'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        db_manager = DbManager()
        worker_role = db_manager.get_item(table='role_group', where='name = \'partner\'')
        roles = db_manager.get_items(table='role', where='role_group_id = ' + str(worker_role['role_group_id']))
        i = 0
        where = ' '
        for role in roles:
            i += 1
            if i == 1:
                where += 'role_id = ' + str(role['role_id'])
            else:
                where += ' OR role_id = ' + str(role['role_id'])

        user_roles = db_manager.get_items(table='user_role_additional', where=where)
        i = 0
        for user_role in user_roles:
            if not roles and i == 0:
                where += 'user_id = ' + str(user_role['user_id'])
            else:
                where += ' OR user_id = ' + str(user_role['user_id'])

        workers = db_manager.get_items(table='account', where=where)

        carousel = self.get_carousel(workers, 'user_id', sc_link)
        keyboard = types.InlineKeyboardMarkup()
        if carousel:
            worker = carousel['object']

        keyboard.add(self.screen_login_partner_entry_invite_dynamic(get_button=1, button_name='Запросить вход для уже действующего патнёра'))
        if carousel and carousel['buttons']:
            keyboard.add(*carousel['buttons'])
        keyboard.add(self.screen_login_partner_dynamic(get_button=1, button_name='Назад'))

        if sc_link + '*' in self.link:
            self.screens[self.link] = Screen(link=self.link, text=content.get_item('carousel_worker_caption') + ' ' + str(worker['login']),
                                             buttons=keyboard,
                                             message_id=self.client.message.message_id,
                                             chat_id=self.client.message.chat.id)

        if carousel:
            self.screens[self.link].text = content.get_item('carousel_worker_caption') + ' ' + str(worker['login'])
        else:
            self.screens[self.link].text = content.get_item('carousel_no_worker')

        self.screens[self.link].buttons = keyboard

    def screen_login_partner_entry_invite_dynamic(self, **kwargs):
        sc_link = '/login_partner_entry_invite'

        screens_getter = self.screens_getter(sc_link, content.get_item(sc_link), kwargs)
        if screens_getter:
            return screens_getter

        if not sc_link in self.link and sc_link != self.link:
            return False

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(self.screen_login_partner_entry_dynamic(get_button=1, button_name='Назад'))
        self.screens[sc_link].buttons = keyboard

    def screens_getter(self, sc_link, text, params):
        if 'get_button' in params:
            return self.get_button(sc_link, params)

        if 'is_index' in params:
            return [sc_link, text]

        if 'get_survey' in params:
            return True

        return False

    def get_order_card(self, **kwargs):
        if not 'orders' in kwargs and not 'order_id' in kwargs:
            return False

        orders = kwargs['orders']
        order_id = kwargs['order_id']
        orders_list = dict()
        keyboard = types.InlineKeyboardMarkup()
        i = 0
        result = dict()

        for order in orders:
            orders_list[i] = order
            i += 1

        i = 0
        for order in orders:
            buttons = []
            if 'first' in kwargs:
                if not 'taken' in kwargs:
                    buttons.append(self.screen_take_order_dynamic(get_button=True, button_name='Забрать',
                                                                  callback_data='/take_order_' + str(order['order_id'])
                                                                                + '[=_=]' + self.client.user['login']))
                elif not 'only_next_last' in kwargs:
                    buttons.append(self.screen_repay_order_dynamic(get_button=True, button_name='Вернуть',
                                                                   callback_data='/repay_order_' + str(
                                                                       order['order_id']) + '[=_=]' + self.client.user['login']))

                if len(orders) > 1:
                    buttons.append(self.screen_get_order_dynamic(button_name='Следующая', get_button=True,
                                                                 callback_data=kwargs['get_order_link'] +
                                                                               str(orders_list[1]['order_id'])
                                                                               + '[=_=]' + self.client.user['login']))
                if len(buttons) > 0:
                    keyboard.add(*buttons)
                if not 'chatbot' in kwargs:
                    keyboard.add(self.screen_lidogenerator_dynamic(button_name='Назад', get_button=True))
                else:
                    keyboard.add(self.screen_bot_developer_dynamic(button_name='Назад', get_button=True))
                result['buttons'] = keyboard
                if not 'chatbot' in kwargs:
                    result['text'] = self.get_text_for_order_card(order=order, order_list=orders_list, current=i)
                else:
                    result['text'] = self.get_text_for_order_card(order=order, order_list=orders_list, current=i,
                                                                  without_title=1)
                break
            else:
                if order['order_id'] == order_id:
                    if i > 0:
                        buttons.append(self.screen_get_order_dynamic(button_name=content.get_item('order_carousel_last'),
                                                                     get_button=True,
                                                                     callback_data=kwargs['get_order_link'] +
                                                                                   str(orders_list[i - 1]['order_id']) +
                                                                                   '[=_=]' + self.client.user['login']))

                    if not 'taken' in kwargs:
                        buttons.append(self.screen_take_order_dynamic(get_button=True,
                                                                      button_name=content.get_item('order_carousel_take'),
                                                                      callback_data='/take_order_' + str(order['order_id'])
                                                                                    + '[=_=]' + self.client.user['login']))
                    elif not 'only_next_last' in kwargs:
                        buttons.append(self.screen_repay_order_dynamic(get_button=True,
                                                                       button_name=content.get_item('order_carousel_repay'),
                                                                       callback_data='/repay_order_' + str(
                                                                           order['order_id']) + '[=_=]' + self.client.user['login']))

                    if len(orders) > i + 1:
                        buttons.append(self.screen_get_order_dynamic(button_name=content.get_item('order_carousel_next'),
                                                                     get_button=True,
                                                                     callback_data=kwargs['get_order_link'] +
                                                                                   str(orders_list[i + 1]['order_id']) +
                                                                                   '[=_=]' + self.client.user['login']))

                    keyboard.add(*buttons)
                    if not 'chatbot' in kwargs:
                        keyboard.add(self.screen_lidogenerator_dynamic(button_name='Назад', get_button=True))
                        result['text'] = self.get_text_for_order_card(order=order, order_list=orders_list, current=i)
                    else:
                        keyboard.add(self.screen_bot_developer_dynamic(button_name='Назад', get_button=True))
                        result['text'] = self.get_text_for_order_card(order=order, order_list=orders_list, current=i,
                                                                      without_title=1)
                    result['buttons'] = keyboard
                    break
            i += 1
        return result

    # def get_detroit_become_learner(self, **kwargs):
    #     if not 'out_sum' in kwargs or not 'trans_type' in kwargs or not 'sc_link' in kwargs:
    #         return False
    #     db_manager = kwargs['db_manager'] if 'db_manager' in kwargs else DbManager()
    #     out_sum = kwargs['out_sum']
    #     trans_type = kwargs['trans_type']
    #     sc_link = kwargs['sc_link']
    #
    #     # rk = Robokassa(out_sum=out_sum, inv_id=str(self.client.user['user_id']))
    #     signature = rk.encode_signature(add=datetime.datetime.now())
    #
    #     transaction = db_manager.get_item(table='transactions', where='is_paid = False AND archive = False AND ' +
    #                                                                   'user_id = ' + str(self.client.user['user_id']) +
    #                                                                   ' AND price = ' + str(out_sum))
    #     if not transaction:
    #         db_manager.add_transaction(user_id=self.client.user['user_id'],
    #                                    description='Запросы на становление учеником',
    #                                    type=str(trans_type['type_id']),
    #                                    token=signature,
    #                                    out_sum=str(out_sum))
    #         transaction = db_manager.get_item(table='transactions', where='token=\'' + signature + '\'')
    #
    #     if transaction:
    #         rk.inv_id = user_encode_key + str(transaction['trans_id'])
    #         self.screens[sc_link].text = content.get_item('payment_learner_link_message') + rk.generate_link()

    def get_text_for_order_card(self, **kwargs):
        if not 'order' in kwargs or not 'order_list' in kwargs or not 'current' in kwargs:
            return False

        order = kwargs['order']
        orders_list = kwargs['order_list']
        i = kwargs['current']

        questions = order['text'].split('[=_=]')
        result = ''
        for question in questions:
            result += question + '\n'
        title = 'Заявка на лидогенерацию \n' if not 'without_title' in kwargs else ''
        return  title + result + '\n----' + str(i + 1) + ' из ' + str(len(orders_list)) + '----'

    def create_sheet_survey(self, sc_link, column_name):
        sheet = Sheet().open_sheet(
            sheet_link='https://docs.google.com/spreadsheets/d/1yfcEhcQPZlDo2hB6t6DnsprsV08N1nMvDucFd2xYB-8/edit?usp=sharing')

        result = sheet.get_first_list(return_items=True, column=column_name, help_column='_type')
        items = result['items']
        help_items = result['help_items']

        if not items:
            self.client.send(content.get_item('order_doesnt_work'))
            return False

        i = 0
        result = []
        for item in items:
            ok_button = Survey.OK_SEPARATOR if help_items[i] == ANSWER_TYPE_OK else ''
            result.append(ok_button + item)
            i += 1

        survey = Survey(message=self.client.message, client=self.client)
        survey.create(question=survey.items_to_questions(items=result), link=sc_link)

        btnm = telebot.types.ReplyKeyboardMarkup().row(self.CANCEL_BUTTON)
        btnm.resize_keyboard = True
        self.client.send_button(text=content.get_item('cancel_survey_message'), button=btnm)

        survey.get_question()

    # вызов этой функции позволяет сделать скрин функцию кнокой на конкретный скрин
    def get_button(self, sc_link, params):
        callback_data = params['callback_data'] if 'callback_data' in params \
            else sc_link + '[=_=]' + self.client.user['login']
        return types.InlineKeyboardButton(text=params['button_name'], callback_data=callback_data)

    # Удаление меню
    def close(self):
        bot.delete_message(self.message.chat.id, self.message.message_id)

    def just_button(self, text, callback_data):
        return types.InlineKeyboardButton(text=text, callback_data=callback_data)


def cancel_lidogenerator_registr(survey):
    db_manager = DbManager()
    db_manager.add_agreement(user_id=str( survey.client.user['user_id'] ), answer=survey.answer, register=str(False))
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))

    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    menu = Menu(message=survey.client.message)
    menu.events('/lidogenerator')
    menu.redirect('/lidogenerator')


def finish_lidogenerator_registr(survey):
    db_manager = DbManager()
    answers = survey.parse_answer()
    vk_url = False
    answer_str = ''

    db_manager.add_agreement(user_id=str( survey.client.user['user_id'] ), answer=survey.answer, register=str(True))
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))

    for answer in answers:
        answer_str += answer + '\n'
        if 'vk.com/' in answer:
            vk_url = answer

    if not vk_url:
        ky = types.ReplyKeyboardRemove()
        survey.client.send_button(content.get_item('lidgen_register_no_correct_vk'), button=ky)
        menu = Menu(message=survey.client.message)
        menu.events('/lidogenerator')
        menu.redirect('/lidogenerator')
        return False

    role = db_manager.get_item(table='role', where='name = \'lidogenerator\'')
    if role:
        ky = types.ReplyKeyboardRemove()
        survey.client.send_button(content.get_item('lidgen_register_wait_message'), button=ky)
        getuniq = Getuniq(login=GETUNIQ_LOGIN, password=GETUNIQ_PASSWORD).authorization()
        result = getuniq.set_access_vk(user_vk_url=vk_url)
        if not result:

            controller = db_manager.get_item(table='account', where='login = \'' + GETUNIQ_CONTROLLER + '\'')
            survey.client.send(text='Getuniq проблема при регистрации лидгена.\nПользователь: ' + survey.client.user['login'] +
                                    '. \nОтветы на регистрации:\n' + answer_str,
                               chat_id=controller['chat'])

            survey.client.send_html(content.get_item('lidgen_register_error_message'))
            ky = types.ReplyKeyboardRemove()
            menu = Menu(message=survey.client.message)
            menu.events('/lidogenerator')
            menu.redirect('/lidogenerator')
            return False
        else:
            if not survey.client.role:
                db_manager.update(table='account', where='user_id =' + str(survey.client.user['user_id']),
                                  set='role_id = ' + str(role['role_id']))
            else:
                db_manager.add_additional_role(user_id=str(survey.client.user['user_id']),
                                               role_id=str(role['role_id']))
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.finish_phrase, button=ky)
    menu = Menu(message=survey.client.message)
    menu.events('/lidogenerator')
    menu.redirect('/lidogenerator')


def cancel_order_services(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    menu = Menu(message=survey.client.message)
    menu.events('/order_services')
    menu.redirect('/order_services')


def finish_order_services(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    questions = survey.parse_question()
    i = 0
    result = ''
    for question in questions:
        separator = '[=_=]' if i < len(questions) - 1 else ''
        result += question + ': ' + answer[i] + separator
        i += 1

    db_manager.add_order(text=str(result), type=ORDER_LIDGEN_ID)
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))

    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.finish_phrase, button=ky)

    menu = Menu(message=survey.client.message)
    menu.events('/order_services')
    menu.redirect('/order_services')


def cancel_order_chatbot(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    menu = Menu(message=survey.client.message)
    menu.events('/order_services')
    menu.redirect('/order_services')


def finish_order_chatbot(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    questions = survey.parse_question()
    i = 0
    result = content.get_item('order_chatbot_message')
    for question in questions:
        separator = '\n' if i < len(questions) - 1 else ''
        result += question + ': ' + answer[i] + separator
        i += 1

    # db_manager.add_order(text=str(result), type=ORDER_LIDGEN_ID)
    role = db_manager.get_item(table='role', where='name =\'bot_developer\'')
    users = survey.client.get_accounts_by_role(role=role)
    db_manager.add_order(text=str(result), type=ORDER_CHATBOT_ID)
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))

    for user in users:
        survey.client.send(text=str(result), chat_id=user['chat'])

    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.finish_phrase, button=ky)

    menu = Menu(message=survey.client.message)
    menu.events('/order_services')
    menu.redirect('/order_services')


def cancel_order_programmer(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    menu = Menu(message=survey.client.message)
    menu.events('/worker')
    menu.redirect('/worker')


def finish_order_programmer(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    questions = survey.parse_question()
    i = 0
    result = 'Резюме от программиста \n\n'
    for question in questions:
        separator = '\n' if i < len(questions) - 1 else ''
        result += question + ': ' + answer[i] + separator
        i += 1

    # db_manager.add_order(text=str(result), type=ORDER_LIDGEN_ID)
    user = db_manager.get_item(table='account', where='login = \'' + CHATBOT_ORDER_CONTROLLER + '\'')
    survey.client.send(text=str(result), chat_id=user['chat'])
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))

    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.finish_phrase, button=ky)

    menu = Menu(message=survey.client.message)
    menu.events('/worker')
    menu.redirect('/worker')


def cancel_add_role_to_user(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    client = survey.link.split('/users_add_role_')[1]

    menu = Menu(message=survey.client.message)
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client

    menu.events(user_edit_link)
    menu.redirect(user_edit_link)


def finish_add_role_to_user(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    ky = types.ReplyKeyboardRemove()
    menu = Menu(message=survey.client.message)
    client = survey.link.split('/users_add_role_')[1]
    roles = survey.client.get_role_from_account(db_manager=db_manager, client=client)

    client = db_manager.get_item(table='account', where='login = \'' + client + '\'')
    if not client:
        return False

    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client['login']
    if int(answer[0]) in roles:
        survey.client.send_button('Такая роль уже есть.', button=ky)
        menu.events(user_edit_link)
        menu.redirect(user_edit_link)
        return False

    db_manager.add_additional_role(user_id=client['user_id'], role_id=int(answer[0]) )
    survey.client.send_button(survey.finish_phrase, button=ky)

    menu.events(user_edit_link)
    menu.redirect(user_edit_link)


def cancel_delete_role_to_user(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    client = survey.link.split('/users_delete_role_')[1]

    menu = Menu(message=survey.client.message)
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client

    menu.events(user_edit_link)
    menu.redirect(user_edit_link)


def finish_delete_role_to_user(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    ky = types.ReplyKeyboardRemove()
    menu = Menu(message=survey.client.message)
    client = survey.link.split('/users_delete_role_')[1]
    roles = survey.client.get_role_from_account(db_manager=db_manager, client=client)

    client = db_manager.get_item(table='account', where='login = \'' + client + '\'')
    if not client:
        return False

    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client['login']
    if int(answer[0]) in roles:
        db_manager.remove(table='user_role_additional',
                          where='user_id = ' + str(client['user_id']) + ' AND role_id = ' + str(answer[0]) )
        if client['role_id'] and client['role_id'] == int(answer[0]):
            db_manager.update(table='account', where='user_id = ' + str(client['user_id']), set='role_id = NULL')
        survey.client.send_button(survey.finish_phrase, button=ky)

        menu.events(user_edit_link)
        menu.redirect(user_edit_link)
        return False


    survey.client.send_button('Такой роли не существует у пользвоателя.', button=ky)
    menu.events(user_edit_link)
    menu.redirect(user_edit_link)
    return False

def cancel_delete_account_to_user(survey):
    ky = types.ReplyKeyboardRemove()
    survey.client.send_button(survey.cancel_phrase, button=ky)
    client = survey.link.split('/users_delete_account_')[1]

    menu = Menu(message=survey.client.message)
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client

    menu.events(user_edit_link)
    menu.redirect(user_edit_link)


def finish_delete_account_to_user(survey):
    db_manager = DbManager()
    answer = survey.parse_answer()
    ky = types.ReplyKeyboardRemove()
    client = survey.link.split('/users_delete_account_')[1]
    menu = Menu(message=survey.client.message)

    client = db_manager.get_item(table='account', where='login = \'' + client + '\'')
    db_manager.remove(table='survey', where='survery_id =' + str(survey.id))
    user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client['login']

    if not client:
        survey.client.send_button('Аккаунта не существует', button=ky)
        menu.events(user_edit_link)
        menu.redirect(user_edit_link)
        db_manager.close()
        return False

    if answer[0] == menu.screen_users_delete_account_dynamic(get_right_answer=True):
        try:
            db_manager.remove(table='user_answer', where='user_id = ' + str(client['user_id']))
            db_manager.remove(table='user_role_additional', where='user_id = ' + str(client['user_id']))
            db_manager.remove(table='account', where='user_id = ' + str(client['user_id']))
            survey.client.send_button(survey.finish_phrase, button=ky)
            user_edit_link = menu.screen_users_edit_dynamic(is_index=True)[0] + '_' + client['login']
        except Exception:
            survey.client.send_button('Во время удаления возникла ошибка.', button=ky)
        menu.events(user_edit_link)
        menu.redirect(user_edit_link)
        db_manager.close()
        return False

    survey.client.send_button('Удаление отменено.', button=ky)
    menu.events(user_edit_link)
    menu.redirect(user_edit_link)
    db_manager.close()


