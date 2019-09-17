import os
basedir = os.path.abspath(os.path.dirname(__file__))

# BASIC APP CONFIG
WTF_CSRF_ENABLED = True
SECRET_KEY = '4PyKQJjXVbX6'
LOG_LEVEL = 'INFO'
LOG_FILE = ''

# TIMEOUT - for large zones
TIMEOUT = 10

# UPLOAD DIR
UPLOAD_DIR = os.path.join(basedir, 'upload')

#SQLite
SQLALCHEMY_DATABASE_URI = 'sqlite:////powerdns-admin/data/padmin.sqlite'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

SAML_ENABLED = False
