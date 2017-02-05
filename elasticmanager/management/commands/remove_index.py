from elasticsearch_dsl import Index

from elasticmanager.management.commands import BasicCommand

class Command(BasicCommand):
    def add_arguments(self, parser):
        parser.add_argument('index', 
                            nargs='+', 
                            type=str,
                            help='index to remove')

    def handle(self, *args, **kwargs):
        index_name = kwargs.get('index')[0]
        if self._yesno('Are you sure you want to remove {}?'.format(index_name)):
            Index(index_name).delete()
            self._write('Removal of {} complete.'.format(index_name))