drf-lookup
==========

Drf-lookup helps you retrieve options for serializer fields and django-filter
filters. It adds additional actions to the viewset, checks the ``queryset`` and
``choices`` attributes and returns valid values for the requested field/filter.
This is useful when you are retrieving parameters asynchronously and don't need
to create a view for each case.

.. toctree::
    :maxdepth: 2
    :caption: User Guide

    source/quickstart
    source/mixins
    source/lookup
    source/serializers
    source/settings