from distutils.core import setup
setup(
  name = 'django-elasticmanager',
  packages = ['elasticmanager'],
  version = '0.1',
  description = 'Djago model manager like class for elasticsearch integration',
  author = 'Adam Hopkins',
  author_email = 'adam@optymizer.com',
  url = '',
  download_url = '',
  keywords = ['django', 'elasticsearch'],
  install_requires=[
      'elasticsearch_dsl',
  ],
  classifiers = [],
)