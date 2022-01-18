# -*- coding: utf8 -*-

import psycopg2
import psycopg2.extras
import urllib.parse as urlparse
import os
import telebot
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from settings import token


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bot = telebot.TeleBot(token)
