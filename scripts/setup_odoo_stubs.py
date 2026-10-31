# -*- coding: utf-8 -*-
"""
Generate lightweight Odoo Development & Type Stubs for host IDEs (Pyrefly, Pylance, Pyright, mypy).
This resolves all 'Cannot find module odoo.*' warnings in local IDE environments without needing
a full Linux Odoo install on the Windows host machine.
"""

import os
import sys

site_pkgs = [p for p in sys.path if 'site-packages' in p and 'AppData' in p][0]
odoo_dir = os.path.join(site_pkgs, 'odoo')
tests_dir = os.path.join(odoo_dir, 'tests')
addons_dir = os.path.join(odoo_dir, 'addons')
os.makedirs(tests_dir, exist_ok=True)
os.makedirs(addons_dir, exist_ok=True)

with open(os.path.join(addons_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('__path__ = __import__("pkgutil").extend_path(__path__, __name__)\n')

# 1. odoo/__init__.py
with open(os.path.join(odoo_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
"""Odoo Framework Development and Type Stubs for Host IDEs."""

def _(text, *args, **kwargs):
    return text

from . import exceptions
from . import tests
from . import models
from . import fields
from . import api
from . import http
''')

# 2. odoo/exceptions.py
with open(os.path.join(odoo_dir, 'exceptions.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
"""Odoo Core Exceptions."""

class UserError(Exception):
    pass

class ValidationError(Exception):
    pass

class AccessError(Exception):
    pass

class AccessDenied(Exception):
    pass

class MissingError(Exception):
    pass

class RedirectWarning(Exception):
    pass
''')

# 3. odoo/tests/__init__.py
with open(os.path.join(tests_dir, '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
from . import common
''')

# 4. odoo/tests/common.py
with open(os.path.join(tests_dir, 'common.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
"""Odoo Test Infrastructure Stubs."""
import unittest

def tagged(*tags):
    def decorator(cls_or_func):
        return cls_or_func
    return decorator

class TransactionCase(unittest.TestCase):
    env = None
    cr = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()

class SavepointCase(TransactionCase):
    pass

class SingleTransactionCase(TransactionCase):
    pass

class HttpCase(TransactionCase):
    pass
''')

# 5. odoo/models.py
with open(os.path.join(odoo_dir, 'models.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
class MetaModel(type):
    pass

class Model:
    _name = ''
    _description = ''
    _inherit = []
    _order = 'id desc'

class TransientModel(Model):
    pass

class AbstractModel(Model):
    pass
''')

# 6. odoo/fields.py
with open(os.path.join(odoo_dir, 'fields.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
class Field:
    def __init__(self, *args, **kwargs):
        pass

class Char(Field): pass
class Integer(Field): pass
class Float(Field): pass
class Boolean(Field): pass
class Text(Field): pass
class Selection(Field): pass
class Many2one(Field): pass
class One2many(Field): pass
class Many2many(Field): pass
class Date(Field):
    @classmethod
    def context_today(cls, *args, **kwargs):
        from datetime import date
        return date.today()

class Datetime(Field):
    @classmethod
    def now(cls, *args, **kwargs):
        from datetime import datetime
        return datetime.now()

class Binary(Field): pass
class Monetary(Field): pass
class Html(Field): pass
class Command:
    @classmethod
    def create(cls, vals): return (0, 0, vals)
    @classmethod
    def update(cls, id, vals): return (1, id, vals)
    @classmethod
    def delete(cls, id): return (2, id, 0)
    @classmethod
    def unlink(cls, id): return (3, id, 0)
    @classmethod
    def link(cls, id): return (4, id, 0)
    @classmethod
    def clear(cls): return (5, 0, 0)
    @classmethod
    def set(cls, ids): return (6, 0, ids)
''')

# 7. odoo/api.py
with open(os.path.join(odoo_dir, 'api.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
def depends(*args):
    def dec(fn): return fn
    return dec

def constrains(*args):
    def dec(fn): return fn
    return dec

def onchange(*args):
    def dec(fn): return fn
    return dec

def model(fn): return fn
def model_create_multi(fn): return fn
def readonly(fn): return fn
def autovacuum(fn): return fn
def returns(*args, **kwargs):
    def dec(fn): return fn
    return dec
''')

# 8. odoo/http.py
with open(os.path.join(odoo_dir, 'http.py'), 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
def route(*args, **kwargs):
    def dec(fn): return fn
    return dec

class Request:
    env = None
    session = None
    httprequest = None

request = Request()

class Response:
    def __init__(self, *args, **kwargs):
        pass

class Controller:
    pass
''')

print("Odoo development and type stubs installed to:", odoo_dir)
