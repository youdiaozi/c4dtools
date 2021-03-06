# coding: utf-8
#
# Copyright (c) 2012-2013, Niklas Rosenstein
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be interpreted
# as representing official policies,  either expressed or implied, of
# the FreeBSD Project.
r"""
c4dtools.resource.menuparser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

New in 1.2.0.

This module implements parsing a Menu-resources and rendering them
to a dialog. The following is an example resource file:

.. code-block:: none

    # Write comments like in Python.
    MENU MENU_FILE {
        MENU_FILE_OPEN;
        MENU_FILE_SAVE;
        --------------;         # Adds a separator.
        COMMAND COMMAND_ID;     # Uses GeDialog.MenuAddCommand().
        COMMAND 5159;           # Same here.

        # Create a sub-menu.
        MENU_FILE_RECENTS {
            # Will be filled programatically.
        }
    }
    # More menus may follow ...

The symbols in the menu resource must be defined in the plugin resource
created by :func:`c4dtools.prepare`. You can also pass your own
:class:`c4dtools.resource.Resource` instance.

This is how to read the menu resource:

.. code-block:: python

    res, imp = c4dtools.prepare(__file__, __res__)

    class MyDialog(c4d.gui.GeDialog):

        MENU_FILE = res.file('menu', 'my_menu.menu')
        RECENTS_START = 1000000

        def CreateLayout(self):
            menu = c4dtools.resource.menuparser.parse_file(self.MENU_FILE)
            recents = menu.find_node(res.MENU_FILE_RECENTS)

            item_id = self.RECENTS_START
            for fn in get_recent_files(): # arbitrary function
                node = c4dtools.resource.menuparser.MenuItem(item_id, str(fn))
                recents.add(node)

            # Render the menu on the dialog, passing the dialog itself
            # and the c4dtools resource.
            self.MenuFlushAll()
            menu.render(self, res)
            self.MenuFinished()

            # ...
            return True

.. warning::

    The :mod:`c4dtools.resource.menuparser` module requires the :mod:`scan` 
    module. This is why this module is not imported implicitly with the
    :mod:`c4dtools` module. You have to import it explicitly:

    .. code-block:: python

        import c4dtools.resource.menuparser
        # or
        from c4dtools.resource import menuparser

    The :mod:`scan` module can be obtained from `github
    <https://github.com/NiklasRosenstein/py-scan>`_. The minimum version
    required is 0.4.5.

"""

import c4d
import scan
import string

from c4dtools.resource import Resource

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

assert scan.__version__ >= (0, 4, 5), "Require scan version 0.4.5 or higher"

class MenuNode(object):

    # Always a MenuContainer instance or None.
    parent = None

    def _assert_symbol(self, symbol, res):
        if not res.has_symbol(symbol):
            raise AttributeError('Resource does not have required symbol %r' %
                                 symbol)

    def _compare_symbol(self, node_id, res):
        r"""
        Sub-procedure for sub-classes implementing a ``symbol`` attribute.
        """

        if self.symbol:
            if node_id == self.symbol:
                return True

            self._assert_symbol(self.symbol, res)
            if res.get(self.symbol) == node_id:
                return True

        return False

    def render(self, dialog, res):
        pass

    def find_node(self, node_id, res):
        r"""
        New in 1.2.7. Find a node by it's identifier.
        """

        return None

    def remove(self):
        r"""
        New in 1.2.8. Remove the node from the tree.
        """

        if self.parent:
            self.parent.children.remove(self)
            self.parent = None

    def copy(self):
        r"""
        New in 1.2.8. Return a copy of the Menu tree.
        """
        raise NotImplementedError

class MenuContainer(MenuNode):
    r"""
    This class represents a container for Cinema 4D dialog menus
    containg menu commands. The class can be rendered recursively
    on a dialog to create such a menu.

    .. attribute:: symbol

        The resource-symbol for the menu-container that can be
        used to obtain the name of the menu. No sub-menu will be
        created with rendering the instance when this value
        evaluates to False (eg. None value).
    """

    def __init__(self, symbol):
        super(MenuContainer, self).__init__()
        self.children = []
        self.symbol = symbol

    def __iter__(self):
        # For partial backwards compatibility where MenuParser.parse()
        # return a list.
        return iter(self.children)

    def add(self, child):
        self.children.append(child)
        child.parent = self

    def render(self, dialog, res):
        if self.symbol:
            self._assert_symbol(self.symbol, res)
            dialog.MenuSubBegin(res.string.get(self.symbol)())
        try:
            for child in self.children:
                child.render(dialog, res)
        finally:
            if self.symbol:
                dialog.MenuSubEnd()

    def find_node(self, node_id, res):
        if self._compare_symbol(node_id, res):
            return self

        for child in self.children:
            node = child.find_node(node_id, res)
            if node:
                return node

    def copy(self):
        new = MenuContainer(self.symbol)
        for child in self.children:
            new.add(child.copy())
        return new

class MenuSeperator(MenuNode):

    def render(self, dialog, res):
        dialog.MenuAddSeparator()

    def copy(self):
        return MenuSeperator()

class MenuCommand(MenuNode):

    def __init__(self, command_id=None, symbol=None):
        super(MenuCommand, self).__init__()
        assert command_id or symbol
        self.command_id = command_id
        self.symbol = symbol

    def render(self, dialog, res):
        command_id = self.command_id
        if not command_id:
            self._assert_symbol(self.symbol, res)
            command_id = res.get(self.symbol)

        dialog.MenuAddCommand(command_id)

    def find_node(self, node_id, res):
        if self.command_id and self.command_id == node_id:
            return self
        elif self._compare_symbol(node_id, res):
            return self

        return None

    def copy(self):
        return MenuCommand(self.command_id, self.symbol)

class MenuString(MenuNode):

    def __init__(self, symbol):
        super(MenuString, self).__init__()
        self.symbol = symbol

    def render(self, dialog, res):
        self._assert_symbol(self.symbol, res)
        dialog.MenuAddString(*res.string.get(self.symbol).both)

    def find_node(self, node_id, res):
        if self._compare_symbol(node_id, res):
            return self
            
    def copy(self):
        return MenuString(self.symbol)

class MenuItem(MenuNode):
    r"""
    This class represents an item added via
    :meth:`c4d.gui.GeDialog.MenuAddString`. It is not created from this
    module but may be used create dynamic menus.

    .. attribute:: id

        The integral number of the symbol to add.

    .. attribute:: string

        The menu-commands item string.
    """

    def __init__(self, id, string):
        super(MenuItem, self).__init__()
        self.id = id
        self.string = string

    def render(self, dialog, res):
        dialog.MenuAddString(self.id, self.string)

    def find_node(self, node_id, res):
        if node_id == self.id:
            return self

    def copy(self):
        return MenuItem(self.id, self.string)

class MenuSet(scan.TokenSet):

    def on_init(self):
        digits = string.digits
        letters = string.letters + '_'

        self.add('comment', 2, scan.HashComment(skip=True))
        self.add('menu',    1, scan.Keyword('MENU'))
        self.add('command', 1, scan.Keyword('COMMAND'))
        self.add('bopen',   1, scan.Keyword('{'))
        self.add('bclose',  1, scan.Keyword('}'))
        self.add('end',     1, scan.Keyword(';'))
        self.add('sep',     0, scan.CharacterSet('-'))
        self.add('symbol',  0, scan.CharacterSet(letters, letters + digits))
        self.add('number',  0, scan.CharacterSet(digits))

class MenuParser(object):

    def __init__(self, **options):
        super(MenuParser, self).__init__()
        self.options = options

    def __getitem__(self, name):
        return self.options[name]

    def _assert_type(self, token, *tokentypes):
        for tokentype in tokentypes:
            if not token or token.type != tokentype:
                raise scan.UnexpectedTokenError(token, tokentypes)

    def _command(self, lexer):
        self._assert_type(lexer.token, lexer.t_command)
        lexer.read_token()

        command_id = None
        symbol_name = None
        if lexer.token.type == lexer.t_number:
            command_id = int(lexer.token.value)
        elif lexer.token.type == lexer.t_symbol:
            symbol_name = lexer.token.value
        else:
            raise scan.UnexpectedTokenError(lexer.token, [lexer.t_number,
                    lexer.t_symbol])

        return MenuCommand(command_id, symbol_name)

    def _menu(self, lexer):
        self._assert_type(lexer.token, lexer.t_menu)
        lexer.read_token()
        self._assert_type(lexer.token, lexer.t_symbol)
        items = MenuContainer(lexer.token.value)
        lexer.read_token()
        self._assert_type(lexer.token, lexer.t_bopen)
        lexer.read_token()

        while lexer.token and lexer.token.type != lexer.t_bclose:

            require_endstmt = True
            if lexer.token.type == lexer.t_menu:
                item = self._menu(lexer)
                require_endstmt = False
            elif lexer.token.type == lexer.t_command:
                item = self._command(lexer)
            elif lexer.token.type == lexer.t_sep:
                item = MenuSeperator()
            elif lexer.token.type == lexer.t_symbol:
                item = MenuString(lexer.token.value)
            else:
                raise scan.UnexpectedTokenError(lexer.token, [lexer.t_menu,
                        lexer.t_command, lexer.t_sep, lexer.t_symbol])

            items.add(item)

            if require_endstmt:
                lexer.read_token()
                self._assert_type(lexer.token, lexer.t_end)
                lexer.read_token()

        self._assert_type(lexer.token, lexer.t_bclose)
        lexer.read_token()
        return items

    def parse(self, lexer):
        menus = MenuContainer(None)
        while lexer.token:
            menu = self._menu(lexer)
            menus.add(menu)
        return menus


def parse_file(filename):
    r"""
    Parse a ``*.menu`` file from the local file-system. Returns a list
    of :class:`MenuContainer` objects.
    """

    return parse_fileobject(open(filename, 'rb'))

def parse_string(data):
    r"""
    Parse a ``*.menu`` formatted string. Returns a list of of
    :class:`MenuContainer` objects.
    """

    fl = StringIO.StringIO(data)
    fl.seek(0)
    return parse_fileobject(fl)

def parse_fileobject(fl):
    r"""
    Parse a file-like object. Returns a list of :class:`MenuContainer`
    objects.
    """

    scanner = scan.Scanner(fl)
    scanner.read()
    lexer = scan.Lexer(scanner, MenuSet())
    lexer.read_token()
    parser = MenuParser()
    return parser.parse(lexer)

def parse_and_prepare(filename, dialog, res):
    r"""
    Like :func:`parse_file`, but renders the parsed menus to the dialog.
    """

    if not isinstance(dialog, c4d.gui.GeDialog):
        raise TypeError('Expected c4d.gui.GeDialog as 2nd argument.')
    if not isinstance(res, Resource):
        raise TypeError('Expected c4dtools.resource.Resource as 3rd argument.')

    menu = parse_file(filename)
    menu.render(dialog, res)


