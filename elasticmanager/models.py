from django.db import models
from django.conf import settings
import django.db.models.options as options
from django.utils.text import camel_case_to_spaces
from django.utils.module_loading import import_string
from django.core.exceptions import FieldDoesNotExist
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# from elasticsearch import helpers
from elasticsearch_dsl import Mapping, DocType, Index
from elasticsearch_dsl.document import DocTypeMeta
from elasticsearch.exceptions import NotFoundError, AuthorizationException

import importlib


options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'es_index',
    'es_type',
    'es_doc_type',
)

field_map = {
    'string': ['CharField','EmailField'],
    'byte': [],
    'short': [],
    'integer': [],
    'long': [],
    'float': [],
    'double': [],
    'boolean': ['BooleanField'],
    'date': ['DateField','DatetimeField'],
    'nested': [],
}



class ElasticManager(models.Manager):
    default_index = settings.ELASTICSEARCH_INDEX
    page_size = 3

    def __iter__(self):
        s = self.get_search()
        return iter(s.scan())

    def __getitem__(self, k):
        s = self.get_search()
        if isinstance(k, slice):
            return list(s[k])
        elif isinstance(k, int):
            try:
                return list(s[k: k+1])[0]
            except IndexError:
                raise IndexError("Requested object does not exist in the query")

    def get_doc_type(self):
        doc_type = getattr(self.model._meta, 'es_doc_type', None)
        if doc_type is None:
            try:
                app_label = self.model._meta.app_label
                object_name = self.model._meta.object_name
                module = importlib.import_module('{}.doctypes'.format(app_label))
                doc_type = getattr(module, object_name)
                if doc_type is None:
                    raise NotImplementedError
            except NotImplementedError:
                raise NotImplementedError("Failed to implement es_doc_type on {}".format(self.type))
        return doc_type

    def get_index(self):
        base_index = getattr(self.model._meta, 'es_index', None)
        if base_index is None:
            return self.default_index
        return base_index

    def get_type(self):
        base_type = getattr(self.model._meta, 'es_type', None)
        if base_type is None:
            return self.model._meta.db_table.split('_')[1]
        return base_type

    def get_search(self):
        if not hasattr(self, 'search') or getattr(self, 'search', None) is None:
            DT = self.get_doc_type()
            s = DT.search()
            setattr(self, 'search', s)
        return getattr(self, 'search')

    def _set_search(self, search):
        setattr(self, 'search', search)

    def clear(self):
        self._set_search(None)


    def all(self):
        self.clear()
        s = self.get_search()
        s = s.filter('match_all')
        self._set_search(s)
        return self

    def filter(self, **kwargs):
        s = self.get_search()
        s = s.filter('term', **kwargs)
        self._set_search(s)
        return self

    def query(self, *args, **kwargs):
        s = self.get_search()
        s = s.query(*args, **kwargs)
        self._set_search(s)
        return self

    def execute(self, page_size=None, page=None):
        page_size = page_size if page_size is not None else self.page_size
        results = self.get_search()
        paginator = Paginator(results, page_size)
        setattr(self, 'results', paginator)
        # self.clear()
        return self.page(page)

    def page(self, page=1):
        paginator = getattr(self, 'results')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)
        return results

    def get(self, id=None, pk=None, **kwargs):
        DT = self.get_doc_type()
        id = id if id is not None else pk
        return DT.get(id, **kwargs)

    def count(self):
        if not hasattr(self, 'results'):
            self.execute()
        return self.results.count
        # TODO:
        # - assign the count to a copy
        # - clear() the results
        # - return the copied count

    def first(self):
        return self[0]

    def last(self):
        count = self.count()
        return self[count-1]

    def all_from_db(self):
        return super().all()

    def filter_from_db(self):
        return super().filter()

    def exclude_from_db(self):
        return super().exclude()

    def get_from_db(self):
        return super().get()

    def count_from_db(self):
        return super().count()

    def first_from_db(self):
        return super().first()

    def last_from_db(self):
        return super().last()
        

    def run_mapping(self):
        index = Index(self.get_index())
        if not index.exists():
            index.create()
        index.close()
        DT = self.get_doc_type()
        DT.init()

    def run_indexing(self):
        queryset = self.all_from_db()
        for instance in queryset:
            instance.index()

    def setup(self):
        items = ('index','type','doc_type')
        for item in items:
            if getattr(self, item, None) is None:
                method_name = "get_{}".format(item)
                method = getattr(self, method_name)
                setattr(self, item, method())


class ElasticModel(models.Model):
    """Abstract model for managing Elasticsearch thru Elasticsearch DSL
    
    To implement, simply apply this mixin to the model. To override the followig defauls, define
    them in your models Meta class

        class Meta:
            es_index = 'some-index'                 # Defaults to settings.ELASTICSEARCH_INDEX
            es_type = 'some-type'                   # Defaults to the models db_table name
            es_doc_type = nameOfSomeDocTypeClass    # Raises error if not implemented

    
    """
    is_elastic = True
    objects = models.Manager()
    elastic = ElasticManager()

    class Meta:
        abstract = True

    # def __apply_properties(self, pdoc, pname, pdict):
    #         for name, info in pdict.get(pname).get('properties').items():
    #             if info.get('type') == 'nested':
    #                 self.__apply_properties()
    #             else:
    #                 value = getattr(self, name)
    #                 setattr(DT, name, value)
    #         return pdoc

    def index(self, *args, **kwargs):
        print('.', sep=' ', end='', flush=True)
        if getattr(self.__class__.elastic, 'doc_type', None) is None:
            self.__class__.elastic.setup()
        DT = self.__class__.elastic.doc_type
        try:
            pdoc = DT.get(id=self.pk)
        except NotFoundError:
            pdoc = DT(_id=self.pk)
        pname = DT._doc_type.mapping.properties.name
        pdict = DT._doc_type.mapping.properties.to_dict()
        if pname in pdict:
            for name, info in pdict.get(pname).get('properties').items():
                value = getattr(self, name)
                if info.get('type') == 'nested':
                    plist = []
                    property_name = list(info.get('properties').keys())[0]
                    for item in value.all():
                        value = getattr(item, property_name)
                        plist.append({property_name: value})
                    setattr(pdoc, name, plist)
                else:
                    if callable(value):
                        value = value()
                    setattr(pdoc, name, value)
                pdoc.save()
            return pdoc
        else:
            pass
            # TODO:
            # - Raise no index exception

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.index()
        except AuthorizationException:
            # TODO:
            # - Better solution
            #   This is a hack to open the Index if it is closed. 
            #   Should probably run a test elsewhere to check if open or closed
            #   Perhaps in middleware, or same location as CONNECTION
            index = Index(self.__class__.elastic.get_index())
            index.open()
            self.index()