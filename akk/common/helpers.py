import os
import re
import sys
from urllib.parse import urlparse, urljoin
import unicodedata

from flask import request, url_for, redirect


def is_safe_url(target):
    """
    TODO: Copy from where?
    :param target:
    :return:
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    """
    TODO: Copy from where?
    :return:
    """
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back_or(endpoint, **values):
    """
    TODO: Copy from where?
    :param endpoint:
    :param values:
    :return:
    """
    target = request.form.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    Stolen from http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'(?u)[^-\w. ]', '_', value).strip()


def install_secret_key(app, filename='secret_key'):
    """
    TODO: Copy from where?
    Configure the SECRET_KEY from a file
    in the instance directory.

    If the file does not exist, print instructions
    to create it from a shell with a random key,
    then exit.
    """
    filename = os.path.join(app.instance_path, filename)

    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        print('Error: No secret key. Create it with:')
        full_path = os.path.dirname(filename)
        if not os.path.isdir(full_path):
            print('mkdir -p {filename}'.format(filename=full_path))
        print('head -c 24 /dev/urandom > {filename}'.format(filename=filename))
        sys.exit(1)