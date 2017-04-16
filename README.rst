=============================
Django Drip Marketing
=============================

.. image:: https://badge.fury.io/py/django-drip-marketing.svg
    :target: https://badge.fury.io/py/django-drip-marketing

.. image:: https://travis-ci.org/madisvain/django-drip-marketing.svg?branch=master
    :target: https://travis-ci.org/madisvain/django-drip-marketing

.. image:: https://codecov.io/gh/madisvain/django-drip-marketing/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/madisvain/django-drip-marketing

Drip marketing for Django

Documentation
-------------

The full documentation is at https://django-drip-marketing.readthedocs.io.

Quickstart
----------

Install Django Drip Marketing::

    pip install django-drip-marketing

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'drip_marketing.apps.DripMarketingConfig',
        ...
    )

Add Django Drip Marketing's URL patterns:

.. code-block:: python

    from drip_marketing import urls as drip_marketing_urls


    urlpatterns = [
        ...
        url(r'^', include(drip_marketing_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
