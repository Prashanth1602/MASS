import os


DATABASE_HOST = "{{ input.database_host }}"
DATABASE_PORT = {{ input.database_port }}
DATABASE_NAME = "{{ input.database_name }}"
DATABASE_USERNAME = "{{ input.database_username }}"

DATABASE_PASSWORD = {{ input.database_password }}


REDIS_HOST = "{{ input.redis_host }}"
REDIS_PORT = {{ input.redis_port }}