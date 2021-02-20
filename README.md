xsd2pgsql
=========

Create a DB structure from an XML Schema.

Usage
=====
Ouput of ``--help``::

    usage: xsd2pgsql.py [-h] [-f] [-a]
                        FILE

    Create a database based on an XSD schema. 
    SQL is output to stdout.

    positional arguments:
      FILE                  XSD file to base the database schema on

    optional arguments:
      -h, --help            show this help message and exit
      -f, --fail            Fail on finding a bad XS type
      -a, --as-is           Don't normalize element names
