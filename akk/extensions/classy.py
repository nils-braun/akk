from urllib.parse import urlparse, urljoin

from flask import url_for, request, redirect
from flask_classy import route, FlaskView


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


def is_safe_url(target):
    """
    TODO: Copy from where?
    :param target:
    :return:
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def add_methods(methods):
    def decorator(f):
        route_name = "/{}/".format(f.__name__)
        return route(route_name, methods=methods)(f)

    return decorator


class BaseView(FlaskView):
    @property
    def next_url(self):
        """
        TODO: Copy from where?
        :return:
        """
        for target in request.values.get('next'), request.referrer:
            if not target:
                continue
            if is_safe_url(target):
                return target
