"""
settings_test.py para la ejecucion de pruebas automatizadas.

Por que existe este archivo
---------------------------
settings.py apunta a la base PostgreSQL productiva alojada en Render. Django
nunca escribe en la base configurada (crea una paralela llamada
'test_<NOMBRE>' y la destruye al terminar), pero aun asi ejecutar la suite
contra Render seria lento (cada query viaja Guatemala -> Oregon), fragil ante
cortes de red y propenso a colisiones si dos workflows de CI corren a la vez.

Aqui se redirige a un PostgreSQL 18 efimero:
  - En local  -> el contenedor de docker-compose.test.yml (puerto 5433).
  - En CI     -> el service container de GitHub Actions (puerto 5432).

Es el mismo motor que produccion, por lo que se conserva la fidelidad de
comportamiento (nombres de tabla en mayusculas, FK RESTRICT, tipos date/time).

Uso:
    pytest                                        (ya configurado en pytest.ini)
    python manage.py test --settings=umg_config.settings_test
"""

import os

# settings.py resuelve las credenciales productivas con python-decouple y falla
# si no encuentra el archivo .env. En CI ese archivo no existe (ni debe), asi
# que se siembran valores ficticios antes de importarlo. decouple da prioridad a
# os.environ sobre el .env, y de todas formas el bloque DATABASES se reemplaza
# por completo mas abajo: estos valores jamas se usan para conectarse.
for _clave, _valor in {
    'DB_NAME': 'placeholder',
    'DB_USER': 'placeholder',
    'DB_PASSWORD': 'placeholder',
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
}.items():
    os.environ.setdefault(_clave, _valor)

from .settings import *  # noqa: E402,F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('TEST_DB_NAME', 'umglab_test'),
        'USER': os.environ.get('TEST_DB_USER', 'umglab'),
        'PASSWORD': os.environ.get('TEST_DB_PASSWORD', 'umglab'),
        'HOST': os.environ.get('TEST_DB_HOST', 'localhost'),
        'PORT': os.environ.get('TEST_DB_PORT', '5433'),
    }
}

DEBUG = False

# El hashing de contrasenas de Django es lento a proposito; en pruebas no aporta
# nada y multiplica el tiempo de ejecucion de la suite.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Evita que el correo real se dispare desde una prueba.
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
