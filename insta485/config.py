"""Insta485 development configuration."""

import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = '/'

# Secret key for encrypting cookies, a sequence of octets(0~255)
SECRET_KEY = (b'\xda\xc9\x83\xc0\xfd\xe4\xca\xe4\x0f\xa2/'
              b'\xd2\xe0j\xf3 \xb6\xe8\x8c=u3\xc9\\')
SESSION_COOKIE_NAME = 'login'

# File Upload to var/uploads/
INSTA485_ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = INSTA485_ROOT/'var'/'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Static Resources
STATIC_FOLDER = INSTA485_ROOT/'insta485'/'static'

# Database file is var/insta485.sqlite3
DATABASE_FILENAME = INSTA485_ROOT/'var'/'insta485.sqlite3'
