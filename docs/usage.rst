=====
Usage
=====

To use Django Drip Marketing in a project, add it to your `INSTALLED_APPS`:

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
