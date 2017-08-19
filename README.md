# web-library
web app for managing a simple library with books and users

features:
+ checking out and returning books
+ putting books on hold and unholding
+ db backend + orm
+ web app

how to use:
+ set up a database and fill it with books and users manually (sorry...)
+ copy config.py.template to config.py and set to correct values
+ configure apache2 with mod_apache

to create tables run the following in a python shell:
```
import config
import library
pm = library.PersistenceManager(config.DB_PATH)
pm.create_tables()
```
