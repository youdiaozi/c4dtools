c4dtools - Scripting Utilities for the Cinema 4D Python API
===========================================================

`c4dtools` is a lightweight library providing convenient classes and functions
that play nice with the Cinema 4D Python API. The most important tools are the
automated resource parser and self-contained library importer.

The `c4dtools` library is throughly documented and fullfills most of the rules
defined in PEP8. The library is fast as well. The resource-symbol loading will
be cached by default (resulting in a file called c4d_symbols.cache, encoded
in JSON format) to speed-up loading of the symbols. If the original c4d_symbols.h
file is changed, the cache is rebuilt.

## For Cinema 4D User

The `c4dtools` library is **not a plugin**. It is a code library that can be used
to make things easier when writing plugins. A plugom that relies on this library
requires you to install the it before the plugin can be used.

## Installation

The `c4dtools` library is casual Python package. For the Python interpreter
embedded into Cinema 4D to find it, you need to install it into the preferences
folder of your Cinema 4D installation.

1. Download and unpack the `c4dtools` library from github.
2. Goto the Cinema 4D preferences and press the "Open Preferences Folder..."
   button in the bottom left.
3. From the folder that has opened, navigat to `library > python > packages`.
   The next folder you select depends on your OS.
4. Copy the `c4dtools`, the one containing all the `*.py` files, directly into
   the folder specific to your OS.

To install a new version of the library, simply delete the old `c4dtools` folder
and paste the new one.

## Alternative Installation

Add a directory to the `PYTHONPATH` environment variable where you put in the
`c4dtools` library folder. Again, the library folder is *only* the one containing
all the `*.py` files.

## Example Code

```python
import c4d
import c4dtools

res, importer = c4dtools.prepare(__file__)

# Import libraries from the `lib` folder relative to the plugins
# directory, 100% self-contained and independent from `sys.path`.
mylib = importer.import_('mylib')
mylib.do_stuff()

class MyDialog(c4d.gui.GeDialog):

    def CreateLayout(self):
        # Access symbols from the `res/c4d_symbols.h` file via
        # the global `res` variable returned by `c4dtools.prepare()`.
        return self.LoadDialogResource(res.DLG_MYDIALOG)

    def InitValues(self):
        # Load strings from the `res/strings_xx/c4d_strings.str` file
        # via `res.string`.
        string_1 = res.string.IDC_MYSTRING_1()
        string_2 = res.string.IDC_MYSTRING_2("Peter")

        self.SetString(res.EDT_STRING1, string_1)
        self.SetString(res.EDT_STRING2, string_2)

        return True

# As of the current release, the only wrapped plugin class is
# `c4d.plugins.CommandData`. The plugin is registered automatically
# in `c4dtools.plugins.main()`, the information for registration
# is defined on class-level.
class MyCommand(c4dtools.plugins.Command):

    PLUGIN_ID = 100008 # !! Must be obtained from the plugincafe !!
    PLUGIN_NAME = res.string.IDC_MYCOMMAND()
    PLUGIN_HELP = res.string.IDC_MYCOMMAND_HELP()

    def Execute(self, doc):
        dlg = MyDialog()
        return dlg.Open(c4d.DLG_TYPE_MODAL)

# Invoke the registration of `MyCommand` via `c4dtools.plugins.main()`
# on the main-run of the python-plugin.
if __name__ == '__main__':
    c4dtools.plugins.main()
```

  [1]: https://github.com/NiklasRosenstein/XPAT


