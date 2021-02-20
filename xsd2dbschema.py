#! /usr/bin/python
""" xsd2dbschema.py
========================================

Create a database based on an XSD schema. 

Usage
========================================
    <file>  XSD file to base the database schema on

    -f  --fail  Fail on finding a bad XS type
    -a  --as-is     Don't normalize element names.

"""

""" Some configuration items """
MAX_RECURSE_LEVEL = 10

# TODO: add MariaDB also
""" XSD to Postgres data type translation dictionary. 
"""
class SDict(dict):
    def __getitem__(self, item):
        return dict.__getitem__(self, item) % self
    def get(self, item):
        try:
            return dict.__getitem__(self, item) % self
        except KeyError:
            return None
DEFX2P = SDict({
    'string':               'varchar',
    'boolean':              'boolean',
    'decimal':              'numeric',
    'float':                'real',
    'double':               'double precision',
    'duration':             'interval',
    'dateTime':             'timestamp',
    'time':                 'time',
    'date':                 'date',
    'gYearMonth':           'timestamp',
    'gYear':                'timestamp',
    'gMonthDay':            'timestamp',
    'gDay':                 'timestamp',
    'gMonth':               'timestamp',
    'hexBinary':            'bytea',
    'base64Binary':         'bytea',
    'anyURI':               'varchar',
    'QName':                None,
    'NOTATION':             None,
    'normalizedString':     '%(string)s',
    'token':                '%(string)s',
    'language':             '%(string)s',
    'NMTOKEN':              None,
    'NMTOKENS':             None,
    'Name':                 '%(string)s',
    'NCName':               '%(string)s',
    'ID':                   None,
    'IDREF':                None,
    'IDREFS':               None,
    'ENTITY':               None,
    'ENTITIES':             None,
    'integer':              'integer',
    'nonPositiveInteger':   '%(integer)s',
    'negativeInteger':      '%(integer)s',
    'long':                 '%(integer)s',
    'int':                  '%(integer)s',
    'short':                '%(integer)s',
    'byte':                 '%(integer)s',
    'nonNegativeInteger':   '%(integer)s',
    'unsignedLong':         '%(integer)s',
    'unsignedInt':          '%(integer)s',
    'unsignedShort':        '%(integer)s',
    'unsignedByte':         '%(integer)s',
    'positiveInteger':      '%(integer)s',
})
USER_TYPES = {}

XMLS = "{http://www.w3.org/2001/XMLSchema}"
XMLS_PREFIX = "xs:"

""" Output """
SQL = ''

""" Helpers
"""
class InvalidXMLType(Exception): pass
class MaxRecursion(Exception): pass

""" Normalize strings like column names for PG """
def pg_normalize(string):
    if not string: string = ''
    string = string.replace('-', '_')
    string = string.replace('.', '_')
    string = string.replace(' ', '_')
    string = string.lower()
    return string

""" Look for elements recursively 

    returns tuple (children bool, sql string)
"""
def look4element(ns, el, parent=None, recurse_level=0, fail=False, normalize=True):
    if recurse_level > MAX_RECURSE_LEVEL: raise MaxRecursion()
    cols = ''
    children = False
    sql = ''
    for x in el.findall(ns + 'element'):
        children = True
        
        rez = look4element(ns, x, x.get('name') or parent, recurse_level + 1, fail=fail)
        sql += rez[1] + '\n'
        if not rez[0]:

            #print 'parent(%s) <%s name=%s type=%s> %s' % (parent, x.tag, x.get('name'), x.get('type'), x.text)
            
            thisType = x.get('type') or x.get('ref') or 'string'
            k = thisType.replace(XMLS_PREFIX, '')
            
            pgType = DEFX2P.get(k) or USER_TYPES.get(k) or None
            if not pgType and fail:
                raise InvalidXMLType("%s is an invalid XSD type." % (XMLS_PREFIX + thisType))
            elif pgType:
                colName = x.get('name') or x.get('ref')
                if normalize:
                    colName = pg_normalize(colName)

                if not cols:
                    cols = "%s %s" % (colName, pgType)
                else:
                    cols += ", %s %s" % (colName, pgType)
            
    if cols:
        sql += """CREATE TABLE %s (%s);""" % (parent, cols)
    for x in el.findall(ns + 'complexType'):
        children = True
        rez = look4element(ns, x, x.get('name') or parent, recurse_level + 1, fail=fail)
        sql += rez[1] + '\n'
    for x in el.findall(ns + 'sequence'):
        children = True
        rez = look4element(ns, x, x.get('name') or parent, recurse_level + 1, fail=fail)
        sql += rez[1] + '\n'
    return (children, sql)

""" Take care of any types that were defined in the XSD """
def buildTypes(ns, root_element):
    for el in root_element.findall(ns + 'element'):
        if el.get('name') and el.get('type'):
            USER_TYPES[pg_normalize(el.get('name'))] = DEFX2P.get(el.get('type').replace(XMLS_PREFIX, ''))

    for el in root_element.findall(ns + 'simpleType'):
        restr = el.find(ns + 'restriction')
        USER_TYPES[pg_normalize(el.get('name'))] = restr.get('base').replace(XMLS_PREFIX, '')

""" Do it
"""
if __name__ == '__main__':

    """ Imports
    """
    import argparse
    import pyxb.utils.domutils as domutils
    from lxml import etree

    """ Handle options
    """
    parser = argparse.ArgumentParser(description='Create a database based on an XSD schema.  SQL is output to stdout.')
    parser.add_argument(
        'xsd', 
        metavar='FILE', 
        type=open, 
        nargs='+',
        help='XSD file to base the database schema on'
    )
    parser.add_argument(
        '-f', '--fail', 
        dest = 'failOnBadType', 
        action = 'store_true',
        default = False,
        help = 'Fail on finding a bad XS type'
    )
    parser.add_argument(
        '-a', '--as-is', 
        dest = 'as_is', 
        action = 'store_true',
        default = False,
        help = "Don't normalize element names"
    )
    args = parser.parse_args()

    """ CORE
    """
    for f in args.xsd: # parse all given files
        """ Parse the XSD file
        """
        xsd = etree.parse(f)
        
        # glean out defined types
        buildTypes(XMLS, xsd)
        
        # parse structure
        if args.as_is:
            norm = False
        else:
            norm = True
        
        result = look4element(XMLS, xsd, pg_normalize(f.name.split('.')[0]), fail=args.failOnBadType, normalize=norm)

        if result[1]:
            print(result[1].replace('\n\n', ''))
        else:
            raise Exception("This shouldn't happen and will never happen.")
