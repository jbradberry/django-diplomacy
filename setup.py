from distutils.core import setup

setup(name='django-diplomacy',
      description='A play-by-web app for Diplomacy',
      version="0.7.0dev",
      author='Jeff Bradberry',
      author_email='jeff.bradberry@gmail.com',
      url='http://github.com/jbradberry/django-diplomacy',
      packages=["diplomacy"],
      classifiers=['Development Status :: 2 - Pre-Alpha',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Games/Entertainment :: Turn Based Strategy'],
      long_description=open('README.txt').read(),
      )
