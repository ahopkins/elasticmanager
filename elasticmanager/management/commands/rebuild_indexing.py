import django.apps
from django.conf import settings

from elasticsearch_dsl import Index

from elasticmanager.management.commands import BasicCommand

class Command(BasicCommand):
    def add_arguments(self, parser):
        parser.add_argument('models', 
                            nargs='*', 
                            type=str,
                            help='Specific models to run on')

    def handle(self, *args, **kwargs):
        self._heading('Elasticsearch indexing process starting')

        models = kwargs.get('models')
        self.gather_models(models)
        self.run_indexing()

    def gather_models(self, passed_models):
        models = {m.__name__: m for m in django.apps.apps.get_models()}
        gathered = []

        self._label("Number of models found: {}".format(len(models)))

        if passed_models:
            for model in passed_models:
                if model in models:
                    gathered.append(models[model])
        else:
            gathered = [model for model_name, model in models.items()]

        self.models = []
        for model in gathered:
            if getattr(model, 'is_elastic', None):
                self.models.append((model.__module__, model.__name__))

        self._label("Number of elastic models found: {}".format(len(self.models)))
        # self._write(', '.join([m[1] for m in self.models]))

    def run_indexing(self):
        index = Index(settings.ELASTICSEARCH_INDEX)
        if not index.exists():
            index.create()
        index.open()
        self._write("Flushing {}".format(settings.ELASTICSEARCH_INDEX))
        for module, name in self.models:
            label, _ = module.split('.')
            ModelClass = django.apps.apps.get_model(label, name)
            self._write("Running indexing for {}".format(ModelClass.__name__))
            ModelClass.elastic.run_indexing()
            self._write("")