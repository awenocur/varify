import sys
from setuptools import setup, find_packages

PACKAGE = 'varify'
VERSION = __import__(PACKAGE).get_version()

install_requires = [
    'django>=1.4.11,<1.5',
    'markdown==2.1.1',
    'south==0.8.2',
    'python-memcached==1.48',
    'coverage',
    'raven>=3.3.9',
    'uwsgi',
    'rq>=0.3.8',
    'django-rq>=0.5.1',
    'rq-dashboard>=0.3.1',
    'django-rq-dashboard',
    'django-widget-tweaks',
    'psycopg2==2.4.4',
    'avocado>=2.3.3,<3.0',
    'serrano>=2.3.4,<3.0',
    'modeltree>=1.1.7',
    'django-haystack==2.0.0',
    'whoosh==2.4.1',
    'openpyxl==1.6.1',
    'django-objectset>=0.2.2',
    'django-siteauth==0.9b1',
    'django-registration2==0.9b2',
    'django-tracking2==0.1.2',
    'django-bootstrap-form>=0.5',
    'django-guardian==1.0.4',
    'django-sts==0.7.3',
    'pycap==0.8.1',
    'django-reversion==1.6.6',
    'diff-match-patch',
    'pyvcf>=0.6.5',
    'vdw'
]

if sys.version_info < (2, 7):
    install_requires += ['importlib']

kwargs = {
    'name': PACKAGE,
    'version': VERSION,
    'packages': find_packages(exclude=['tests', '*.tests', '*.tests.*',
                                       'tests.*']),
    'include_package_data': True,
    'install_requires': install_requires,
    # This is a hack to get setuptools to install the latest version of the
    # varify-data-warehouse from the github repo. Until varify-data-warehouse
    # is released on pypi, we need to continue to install from github.
    'dependency_links': [
        'https://github.com/cbmi/varify-data-warehouse/archive/master.zip#egg=vdw',     # noqa
    ],
    'test_suite': 'test_suite',
    'tests_require': ['httpretty'],
    'author': '',
    'author_email': '',
    'description': '',
    'license': '',
    'keywords': '',
    'url': '',
    'classifiers': [],
}

setup(**kwargs)
