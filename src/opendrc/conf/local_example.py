#
# Any machine specific settings when using development settings.
#

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "opendrc",
        "USER": "opendrc",
        "PASSWORD": "opendrc",
        # Empty for localhost through domain sockets or '127.0.0.1' for localhost
        # through TCP.
        "HOST": "",
        "PORT": "",  # Set to empty string for default.
    }
}
