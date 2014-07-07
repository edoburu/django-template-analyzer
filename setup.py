#!/usr/bin/env python
from setuptools import setup, find_packages
from os.path import dirname, join

setup(
    name='django-template-analyzer',
    version='1.3',
    license='BSD License',
    platforms=['OS Independent'],

    description='Django Template Analyzer - Extract template nodes from a Django template',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),

    author='Diederik van der Boor & Django CMS developers',
    author_email='opensource@edoburu.nl',

    url='https://github.com/edoburu/django-template-analyzer',
    download_url='https://github.com/edoburu/django-template-analyzer/zipball/master',

    packages=find_packages(),
    include_package_data=True,

    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Framework :: Django',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ]
)
