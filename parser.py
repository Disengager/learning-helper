# -*- coding: utf8 -*-
import os
from selenium import webdriver
from options import Options


class Parser:
    url = False
    login = False
    password = False
    session = False
    parser_webdriver = False

    def __init__(self, **kwargs):
        self.url = kwargs['url'] if 'url' in kwargs else False
        self.login = kwargs['login'] if 'login' in kwargs else False
        self.password = kwargs['password'] if 'password' in kwargs else False
        self.parser_webdriver = webdriver.Chrome(executable_path=os.getenv("CHROMEDRIVER_PATH"))

    def set_form(self, **kwargs):
        if not 'fields' in kwargs:
            return False
        for field in kwargs['fields']:
            if 'name' in field:
                self.check_property(field=field, element=self.parser_webdriver.find_element_by_name(field['name']))
            if 'id' in field:
                self.check_property(field=field, element=self.parser_webdriver.find_element_by_id(field['id']))
            if 'class' in field:
                self.check_property(field=field,
                                    element=self.parser_webdriver.find_element_by_class_name(field['class']))
            if 'tag' in field:
                self.check_property(field=field, element=self.parser_webdriver.find_element_by_tag_name(field['tag']))
            if 'selector' in field:
                self.check_property(field=field,
                                    element=self.parser_webdriver.find_element_by_css_selector(field['selector']))
            if 'x_path' in field:
                self.check_property(field=field,
                                    element=self.parser_webdriver.find_element_by_xpath(field['x_path']))

    def check_property(self, field, element):
        if 'keys' in field:
            element.send_keys(field['keys'])
            # assert "No results found." not in element.page_source
        if 'click' in field:
            element.click()
            # assert "No results found." not in element.page_source

    # если нет параметра url будет парсить текущую страницу
    def parse_page(self, **kwargs):
        if not self.url:
            return False
        if 'url' in kwargs:
            self.url = kwargs['url']
            self.parser_webdriver.get(self.url)
        content = self.parser_webdriver.find_element_by_tag_name('body')
        return content.get_attribute('innerHTML')

    def close(self):
        self.parser_webdriver.close()


class Getuniq(Parser):

    def authorization(self, **kwargs):
        self.url = 'https://getuniq.me/ru/login'
        self.parser_webdriver.get(self.url)
        fields = []
        fields.append({"id": "_username", "keys": self.login})
        fields.append({"id": "_password", "keys": self.password})
        fields.append({"id": "form_submit", "click": True})
        self.set_form(fields=fields)
        return self

    def set_access_vk(self, **kwargs):
        self.url = 'https://getuniq.me/ru/services/vk/49159/access/new'
        self.parser_webdriver.get(self.url)
        fields = []
        fields.append({"id": "vk_access_userId", "keys": kwargs['user_vk_url']})
        fields.append({"x_path": '//label[@for="vk_access_role_0"]', "click": True})
        fields.append({"selector": ".form-group_btn-cont .btn-primary", "click": True})
        self.set_form(fields=fields)
        text = self.parse_page()
        return text.find('Доступ предоставлен') != -1
