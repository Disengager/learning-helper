# -*- coding: utf8 -*-
import telebot
from telebot import types
from db_manager import DbManager
from settings import token, user_encode_key, ORDER_LIDGEN_ID, CHATBOT_ORDER_CONTROLLER


class Survey:
    OK_SEPARATOR = '[=ок=]'
    id = False
    message = False
    client = False
    question = False
    answer = False
    data = False
    link = False
    exist = False
    custom_finish = False
    custom_cancel = False
    cancel_phrase = 'Отмена'
    finish_phrase = 'Отпралвено'
    ok_button = False

    def __init__(self, **kwargs):
        self.client = kwargs['client'] if 'client' in kwargs else self.client
        self.message = kwargs['message'] if 'message' in kwargs else self.message
        self.custom_cancel = kwargs['custom_cancel'] if 'custom_cancel' in kwargs else self.custom_cancel
        self.custom_finish = kwargs['custom_finish'] if 'custom_finish' in kwargs else self.custom_finish
        self.ok_button = kwargs['ok_button'] if 'ok_button' in kwargs else self.ok_button

        if self.client:
            db_manager = DbManager()
            survey = db_manager.get_item(table='survey', where='user_id =' + str(self.client.user['user_id']) )
            if survey:
                self.question = survey['question'] if survey['question'] else self.question
                self.answer = survey['answer'] if survey['answer'] else self.answer
                self.data = survey['data'] if survey['data'] else self.data
                self.id = survey['survery_id'] if survey['survery_id'] else self.id
                self.link = survey['link'] if survey['link'] else self.link
                self.exist = True
            db_manager.close()

    def is_exist(self):
        return self.exist and self.id

    def is_last_question(self):
        return self.get_question_id() > len(self.parse_question()) - 1

    def parse_question(self):
        return self.question.split('[=_=]')

    def parse_answer(self):
        if not self.answer:
            return 0
        return self.answer.split('[=_=]')

    def create(self, **kwargs):
        if not 'question' in kwargs and not 'link' in kwargs:
            return False
        db_manager = DbManager()
        self.answer = ''
        self.question = str(kwargs['question'])
        if self.is_exist():
            db_manager.update(table='survey',
                              set='question = \'' + str(kwargs['question']) + '\', answer = \'\', link = \'' + str(kwargs['link'] + '\''),
                              where='survery_id  = ' + str( self.id ))
        else:
            self.id = db_manager.add_survey(link=kwargs['link'], question=kwargs['question'],
                                            user_id=self.client.user['user_id'])

    def get_question_id(self):
        if self.parse_answer() == 0:
            return 0
        return len(self.parse_answer()) - 1

    def get_question(self, **kwargs):
        if self.is_last_question():
            self.finish()
            return False

        questions = self.parse_question()
        current_question = questions[self.get_question_id()]

        if not self.is_ok_question(current_question):
            self.client.send(current_question)
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Ок', callback_data='ок[=_=]' + self.client.user['login']))
            self.client.send_button(text=current_question.split(self.OK_SEPARATOR)[1], button=keyboard)

    def set_answer(self, **kwargs):
        if not 'text' in kwargs or kwargs['text'] == "":
            return False

        questions = self.parse_question()
        current_question = questions[self.get_question_id()]

        if self.is_ok_question(current_question):
            self.client.edit(self.client.message.old_text)
            kwargs['text'] = 'ок'
        if self.answer:
            self.answer = self.answer + kwargs['text'] + '[=_=]'
        else:
            self.answer = kwargs['text'] + '[=_=]'
        db_manager = DbManager()
        db_manager.update(table='survey',
                          set='answer = \'' + self.answer + '\'',
                          where='survery_id  = ' + str(self.id))

        db_manager.close()
        self.get_question()

    def set_finish_and_cancel(self, **kwargs):
        if 'cancel_str' in kwargs:
            self.cancel_phrase = kwargs['cancel_str']
        if 'finish_str' in kwargs:
            self.finish_phrase = kwargs['finish_str']
        if 'cancel' in kwargs:
            self.custom_cancel = kwargs['cancel']
        if 'finish' in kwargs:
            self.custom_finish = kwargs['finish']

    def items_to_questions(self, **kwargs):
        if not 'items' in kwargs:
            return False

        items = kwargs['items']
        questions = ''
        i = 0
        for item in items:
            if item != '':
                separator = '[=_=]' if i < len(items) - 1 else ''
                questions += item + separator
                i += 1

        return questions

    def is_ok_question(self, current_question):
        find = current_question.find(self.OK_SEPARATOR)
        return find != -1

    def cancel(self):
        if self.custom_cancel:
            self.custom_cancel(survey=self)
        self.delete_survey()

    def finish(self):
        if self.custom_finish:
            self.custom_finish(survey=self)
        self.delete_survey()

    def delete_survey(self):
        db_manager = DbManager()
        db_manager.remove(table='survey', where='survery_id =' +str(self.id))
        db_manager.close()