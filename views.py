import inspect
import datetime
import math
import pytz
from datetime import date
from datetime import timezone
from db_manager import bot
from google_drive import Sheet
from db_manager import bot


class CustomView:
    functions = dict()

    def get_methods_no_index(self):
        events = inspect.getmembers(self, predicate=inspect.ismethod)
        result = []
        for event in events:
            if event[0].find('_no_index') == -1:
                result.append((event[0], event[0]))
                self.functions[event[0]] = event[1]
        return result

    def schedule_photo(self, old_screen, kwargs):
        chat_id = kwargs['user'].chat_id if 'user' in kwargs else kwargs['chat_id']
        photo = open('static/img/graph-6.jpg', 'rb')
        bot.send_photo(chat_id, photo)

    def schedule_current(self, old_screen, kwargs):
        week_screen = kwargs['screen'].get_week_screen(self.get_current_week_no_index())
        week_day = datetime.datetime.today().weekday()
        old_week = week_day
        days = ['mon', 'tue', 'wen', 'thu', 'fri', 'sater', 'sund']
        week_day = self.get_day_screen_no_index(week_day, week_screen, days)

        day_screen = kwargs['screen'].get_week_screen(self.get_current_week_no_index() + '_' + days[week_day])

        buttons = self.get_last_and_frist_buttons_no_index(day_screen)
        first_button = buttons[0]
        last_button = buttons[1]

        lesson_end = datetime.datetime.strptime(last_button.name.split(' ')[2], '%H.%M').time()
        now = datetime.datetime.now()
        now = self.utc_to_local_no_index(now).time()
        if old_week == week_day:
            if lesson_end < now:
                week_day = week_day + 1
                week_day = self.get_day_screen_no_index(week_day, week_screen, days)
                day_screen = kwargs['screen'].get_week_screen(self.get_current_week_no_index() + '_' + days[week_day])
            else:
                day_screen = self.select_now_lesson_no_index(day_screen, now)

        if 'user' in kwargs:
            day_screen.render(old_screen, user=kwargs['user'])
        elif 'chat_id' in kwargs:
            day_screen.render(old_screen, chat_id=kwargs['chat_id'])

    def select_now_lesson_no_index(self, day_screen, now_time):
        for button in day_screen.buttons:
            if datetime.datetime.strptime(button.name.split(' - ')[0], '%H.%M').time() < now_time:
                if datetime.datetime.strptime(button.name.split(' ')[2], '%H.%M').time() > now_time:
                    button.name = ' * ' + button.name

        return day_screen

    def utc_to_local_no_index(self, utc_dt):
        local_tz = pytz.timezone('Asia/Yekaterinburg')
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)

    def get_day_screen_no_index(self, week_day, week_screen, days):
        search_end = False
        while not search_end:
            for button in week_screen.buttons:
                if button.link == week_screen.link + '_' + days[week_day]:
                    search_end = True
                    break
            if not search_end:
                week_day = week_day + 1
                if week_day > 6:
                    week_day = 0

        return week_day

    def get_current_week_no_index(self):
        d0 = date(2020, 2, 23)
        d1 = datetime.datetime.now()
        delta = d1.date() - d0
        week = math.ceil(delta.days / 7)
        return '1' if week % 2 == 0 else '2'

    def template_tags(self, old_screen, kwargs):
        print('--template_tags--')
        text = kwargs['screen'].text
        text = text.replace('{% this_name %}', kwargs['screen'].name)
        text = text.replace('{% this_link %}', kwargs['screen'].link)
        text = text.replace("{% *n %}", '\n')
        text = str(text)
        buttons = self.get_last_and_frist_buttons_no_index(kwargs['screen'])
        first_button = buttons[0]
        last_button = buttons[1]
        text = text.replace('{% this_first_btn_name %}', first_button.name)
        text = text.replace('{% this_lesson_start %}', first_button.name.split(' - ')[0])
        text = text.replace('{% this_lesson_end %}', last_button.name.split(' ')[2])
        text = text.replace('{% this_last_btn_name %}', last_button.name)
        text = text.replace('{% this_buttons_len %}', str(len(kwargs['screen'].buttons)))
        kwargs['screen'].text = text
        print(text) 

        if 'user' in kwargs:
            kwargs['screen'].render_from_custom_viewe(False, screen=kwargs['screen'], user=kwargs['user'])
        elif 'chat_id' in kwargs:
            kwargs['screen'].render_from_custom_viewe(False, screen=kwargs['screen'], chat_id=kwargs['chat_id'])

    def get_last_and_frist_buttons_no_index(self, screen):
        first_button = False
        last_button = False
        i = 1
        for button in screen.buttons:
            if i == 1:
                first_button = button
            if i == len(screen.buttons):
                last_button = button
            i = i + 1
        return [first_button, last_button]

    def load_hw(self, old_screen, kwargs):
        hw = kwargs['screen'].get_hw_by_user()
        print(hw)
        if not hw:
            return False

        result = ''
        print(result)
        for homework in hw:
            result += '<b>' + homework.get_subject_name() + '</b>\n' + homework.text + '\n' + str(homework.time_stamp) + '\n\n\n'
        print(result)
        bot.send_message(kwargs['user'].chat_id, result, parse_mode='HTML')
        return False

    def load_lection(self, old_screen, kwargs):
        subject = kwargs['screen'].get_subject_by_name()

        if not subject:
            return False

        params = self.get_params_no_index(kwargs['screen'].link)
        print(kwargs['screen'].link)
        if params:
            for param in params:
                print(param)
        sheet = Sheet().open_sheet(sheet_link=subject.gd_link)
        result = sheet.get_first_list(return_items=True, column='content', help_column='_type')

        if not params:
            i = 0
            j = 0
            for item in result['items']:
                if result['help_items'][i] == 'theme':
                    kwargs['screen'].add_button(item, kwargs['screen'].link + '?theme=' + str(i), j)
                    print(j)
                    print(item)
                    j += 1
                i += 1
            # title = ''
            kwargs['screen'].dynamic_static_collapse()
            kwargs['screen'].sort_buttons(dynamic=True)

            return self.render_custom_viewe_no_index(kwargs)

        if 'theme' in params and 'show_all_theme' in params:
            print('show_all_theme')
            param = int(params['theme'])
            i = 0
            theme_count = 1
            content = ''
            for item in result['items']:
                if i > param:
                    if result['help_items'][i] == 'subtheme':
                        content += '\n\n\n<b>' + str(theme_count) + '. ' + item + '</b>'
                        theme_count += 1
                    if result['help_items'][i] == 'content':
                        content += item
                    if result['help_items'][i] == 'theme':
                        break
                i += 1

            if 'user' in kwargs:
                self.send_message_no_index(kwargs['user'].chat_id , content, buttons=kwargs['screen'].convert_buttons(), parse_mode='HTML')
            elif 'chat_id' in kwargs:
                self.send_message_no_index(kwargs['chat_id'], content, buttons=kwargs['screen'].convert_buttons(), parse_mode='HTML')

            return False
        elif 'theme' in params:
            param = int(params['theme'])
            i = 0
            j = 0
            for item in result['items']:
                if i > param:
                    if result['help_items'][i] == 'subtheme':
                        kwargs['screen'].add_button(item, kwargs['screen'].link + '&sub_theme=' + str(i), j)
                        j += 1
                    if result['help_items'][i] == 'theme':
                        break
                i += 1
            print(kwargs['screen'].link + '&show_all_theme=' + str(1))
            kwargs['screen'].add_button('показать всю тему', kwargs['screen'].link + '&show_all_theme=' + str(1), i+1)
            kwargs['screen'].dynamic_static_collapse()
            kwargs['screen'].sort_buttons(dynamic=True)

            return self.render_custom_viewe_no_index(kwargs)

    def save_answer(self, old_screen, kwargs):
        params = self.get_params_no_index(kwargs['screen'].link)
        separate_link = kwargs['screen'].link.split('/')[1]
        question_number = int(separate_link.split('_q')[0]) - 1

        import os.path
        import json
        test_data = dict()

        if os.path.isfile('data' + str(kwargs['user'].chat_id) + '.json'):
            with open('data' + str(kwargs['user'].chat_id) + '.json') as json_file:
                test_data = json.load(json_file)

        if 'answer' in params:
            separate_link = kwargs['screen'].link.split('/')[1]
            question_number = int(separate_link.split('_q')[0]) - 1
            test_data[str(question_number)] = params['answer']

            json_file = open('data' + str(kwargs['user'].chat_id) + '.json', "w+")
            json.dump(test_data, json_file)

            print(str(question_number) + ": " + params['answer'])

        print(question_number)
        if question_number == 20:
            print(test_data)
            kwargs['screen'].text = kwargs['screen'].text + self.get_types(test_data)

        self.render_custom_viewe_no_index(kwargs)

    def get_types(self, answers):
        human_nature = 0
        human_technics = 0
        human_human = 0
        human_sign_system = 0
        human_art = 0
        if answers['1'] == 'a':
            human_nature = human_nature + 1
        if answers['3'] == 'b':
            human_nature = human_nature + 1
        if answers['6'] == 'a':
            human_nature = human_nature + 1
        if answers['10'] == 'a':
            human_nature = human_nature + 1
        if answers['11'] == 'a':
            human_nature = human_nature + 1
        if answers['13'] == 'b':
            human_nature = human_nature + 1
        if answers['16'] == 'a':
            human_nature = human_nature + 1
        if answers['20'] == 'a':
            human_nature = human_nature + 1
        if answers['1'] == 'b':
            human_technics = human_technics + 1
        if answers['4'] == 'a':
            human_technics = human_technics + 1
        if answers['7'] == 'b':
            human_technics = human_technics + 1
        if answers['9'] == 'a':
            human_technics = human_technics + 1
        if answers['11'] == 'b':
            human_technics = human_technics + 1
        if answers['14'] == 'a':
            human_technics = human_technics + 1
        if answers['17'] == 'b':
            human_technics = human_technics + 1
        if answers['19'] == 'a':
            human_technics = human_technics + 1

        if_h_h = {"2": "a", "4": "b", "6": "b", "8": "a", "12": "a", "14": "b", "16": "b", "18": "a"}
        for un in if_h_h:
            if answers[un] == if_h_h[un]:
                human_human = human_human + 1
        if_h_s_s = {"2": "b", "5": "a", "9": "b", "10": "b", "12": "b", "15": "a", "19": "b", "20": "b"}
        for un in if_h_s_s:
            if answers[un] == if_h_s_s[un]:
                human_sign_system = human_sign_system + 1
        if_h_a = {"3": "a", "5": "b", "7": "a", "8": "b", "13": "a", "15": "b", "17": "a", "18": "b"}
        for un in if_h_a:
            if answers[un] == if_h_a[un]:
                human_art = human_art + 1

        order_max = max([human_nature, human_technics, human_human, human_sign_system, human_art])
        description = ['Ввсе профессии, связанные с растениеводством, животноводством и лесным хозяйством, т.е. с природными объектами и явлениями. \nОбъектом труда являются: живые организмы, растения, животные и биологические процессы.',
                       'Все технические профессии, профессии, в которых происходит активное взаимодействие с разнообразными приборами, машинами, механизмами, аппаратами, станками. \nОбъектом труда служат: технические системы и объекты (механизмы, машины, аппараты, установки), материалы и виды энергии. ',
                       'Все профессии, связанные с работой с людьми, собслуживанием людей, с общением.\nОбъектом труда являются: люди, группы, коллективы.',
                       'Все профессии, связанные с обсчетами, цифровыми и буквенными знаками, в том числе и музыкальные специальности,большинство профессий связано с переработкой информации.\nОбъектами труда являются: условные знаки, шифры, коды, таблицы, цифры,числовые значения, символы, тексты.',
                       'Все творческие специальности. \nОбъектом труда этих специальностей служат: художественные образы, способы их построения, их роли, элементы и особенности.']

        return "\nЧеловек-природа: " + self.get_discrption(description[0], human_nature, order_max) + \
               "Человек-техника: " + self.get_discrption(description[1], human_technics, order_max) + \
               "Человек-человек: " + self.get_discrption(description[2], human_human, order_max) + \
               "Человек-знаковая система: " + self.get_discrption(description[3], human_sign_system, order_max) + \
               "Человек-художник: " + self.get_discrption(description[4], human_art, order_max) + "\n"

    def get_discrption(self, text, scale_val, max_val):
        if scale_val == max_val:
            return str(scale_val) + "\n" + text + '\n'
        return str(scale_val) + "\n"

    def render_custom_viewe_no_index(self, obj):
        print(obj['screen'])
        if 'user' in obj:
            obj['screen'].render_from_custom_viewe(False, screen=obj['screen'], user=obj['user'])
        elif 'chat_id' in obj:
            obj['screen'].render_from_custom_viewe(False, screen=obj['screen'], chat_id=obj['chat_id'])
        return True

    def get_params_no_index(self, link):
        if len(link.split('?')) < 2:
            return False

        result = dict()
        params = link.split('?')[1]

        if len(params.split('&')) == 1:
            name = params.split('=')[0]
            value = params.split('=')[1]
            result[name] = value
            return result

        params = params.split('&')

        for param in params:
            name = param.split('=')[0]
            value = param.split('=')[1]
            result[name] = value

        return result

    def temp2_no_index(self, old_screen, kwargs):
        pass

    def temp3(self, old_screen, kwargs):
        pass

    def send_message_no_index(self, chat_id, content, **kwargs):
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
                bot.send_message(chat_id, send_content, reply_markup=buttons, parse_mode=parse_mode)
            else:
                bot.send_message(chat_id, send_content, parse_mode=parse_mode)
        else:
            if buttons:
                bot.send_message(chat_id, send_content, reply_markup=buttons)
            else:
                bot.send_message(chat_id, send_content)