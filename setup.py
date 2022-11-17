"""
Build and install the project.
"""

from setuptools import setup, find_packages

setup(
    name='whots_metadata',
    version='0.0.1',
    extras_require={
        'scrapy': ['scrapy>=2.7.0'],
    },
    packages=find_packages(where='src/whots_metadata'),
    package_dir={"": "src/whots_metadata"},
    author='Fernando Carvalho Pacheco',
    author_email='fernando.pacheco@hawaii.edu',
    description='A scrapy framework project for scraping WHOTS information  '
                'from https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html',
)
