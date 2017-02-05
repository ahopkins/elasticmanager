from django.conf import settings

from elasticsearch_dsl.connections import connections

CONNECTION = connections.create_connection(hosts=settings.ELASTICSEARCH_HOSTS, timeout=20)