import setuptools


with open("README.rst") as f:
    long_description = f.read()


setuptools.setup(
    name='django-diplomacy',
    version="0.8.0",
    author='Jeff Bradberry',
    author_email='jeff.bradberry@gmail.com',
    description='A play-by-web app for Diplomacy',
    long_description=long_description,
    long_description_content_type='test/x-rst',
    url='http://github.com/jbradberry/django-diplomacy',
    packages=setuptools.find_packages(),
    entry_points={
        'turngeneration.plugins': ['diplomacy = diplomacy.plugins:TurnGeneration'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment :: Turn Based Strategy'
    ],
)
