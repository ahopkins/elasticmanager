from distutils.core import setup
setup(
  name = 'elasticmanager',
  packages = ['elasticmanager','elasticmanager.management','elasticmanager.management.commands'],
  version = '0.2.5.1',
  description = 'Django model manager like class for elasticsearch integration',
  author = 'Adam Hopkins',
  author_email = 'adam@optymizer.com',
  url = 'https://github.com/ahopkins/elasticmanager',
  download_url = 'https://github.com/ahopkins/elasticmanager/archive/master.zip',
  keywords = ['django', 'elasticsearch',],
  install_requires=[
      'elasticsearch_dsl',
  ],
  classifiers = [],
)