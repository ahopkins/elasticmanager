# elasticmanager
A manager for translating an ORM into Elasticsearch

*This package is still in active development. Currently it is being built as an mixin for the Django ORM. However, once stable, this will be abstracted away to be able to plugin to other ORMs.*

This pacakge requires `elasticsearch-dsl` which you can get:

    pip install elasticsearch-dsl

## Getting Started

1. To get started, install from pip.

    pip install elasticmanager

1. Add `elasticmanager` to your `settings.py` (this enables management commands).
1. Put the name of your index in `settings.py`: `ELASTICSEARCH_INDEX = 'myindex'`
1. Subclass `elasticmanager.ElasticModel`.

    ```python
    from django.db import models
    from elasticmanager.models import ElasticModel
    class Visitor(ElasticModel, models.Model):
       name = models.CharField(max_lendth=100)
       created = models.DateTimeField(auto_now_add=True, editable=False)
    ```


1. Create a `doctypes.py` in the same app as the corresponding `models.py`.
   Add a `DocType` to this file with the same name as your model. (See [Elasticsearch DSL documenation for more information on creating a `DocType`](https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#doctype))

    ```python
    from django.conf import settings
    from elasticmanager.doctypes import BaseDocType
    from . import models
    class Visitor(BaseDocType):

       pk = field.Keyword()
       name = field.Keyword()
       created = field.Date()

       class Meta:
           model = models.Visitor
           index = settings.ELASTICSEARCH_INDEX
    ```


   Note that the `Meta` information for the `doctype` should link to the `model` and the `index`.

1. Run `./manage.py rebuild_mapping`
1. Run `./manage.py rebuild_indexing` (if there are items in the DB that need to be inexed)

There is also another management command (`./manage.py remove_index <NAME>`) that can be used to delete an entire index. Helpful during development stages.

Currently, all calls to the `.save()` method on an instance of the model will trigger the `.save()` on the doctype, and therefore will keep the index in Elasticsearch up to date.

## Making calls to query and filter

Calls somewhat approximate the default Django syntax.

**Get all instances**

```python
visitors = Visitor.elastic.all()              # Return everything from Elasticsearch
```

**Get one instance**

```python
visitor = Visitor.elastic.get(pk=123)         # Return an instance from Elasticsearch given a specific key
visitor = Visitor.elastic.first()             # Return first instance in a queryset
visitor = Visitor.elastic.last()              # Return last instance in a queryset
```

**Count the number of instances**

```python
count = Visitor.elastic.count()               # Count the number of instances in a queryset
```

**Filter/query** *This lines up with the [query](https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html#queries) and [filter](https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html#filters) methods. See the linked documentation for more information.*

```python
johns = Visitor.elastic.filter(name="John")   # Return everything from Elasticsearch
```

**Chaining applies**

```python
first_john = Visitor.elastic.filter(name="John").first()
```

Under the hood, there is an `execute()` method that is committing the search. This can be called by itself, and probably should be if you are (for example) manipulating a queryset. But, you should not need to call that if you are, for example, calling `count()` or if you are iterating over the result set.

```python
johns = Visitor.elastic.filter(name="John")
for john in johns:
    print(john)

# or

johns = Visitor.elastic.filter(name="John")
johns.execute()
print(johns.results)
```

*This requirement will be removed with some more fine tuning to work more intuitively.*

## Plans for the future

- Abstraction from using `models.Manager`
- Fix the class factory so that a `Model` can be automatically transformed into a `DocType` without having to define it in `doctypes.py`.
- Tests
- Aggregations
- Additional Exception handling
- More management commands
- More powerful API

If you have any questions, thoughts, complaints, compliments, let me know.