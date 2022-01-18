from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy.sql.sqltypes import JSON
from db_manager import app, db

# migrate = Migrate(app, db)
# manager = Manager(app)
# manager.add_command('db', MigrateCommand)

from models import *

db.create_all()

# if __name__ == '__main__':
#     manager.run()