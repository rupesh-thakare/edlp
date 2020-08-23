import os 

database_user = 'rupeshthakare'
database_password = 'dbpassword'

DEBUG = False

SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f'mysql+mysqlconnector://{database_user}:{database_password}@rupeshthakare.mysql.pythonanywhere-services.com:3306/rupeshthakare$default'
