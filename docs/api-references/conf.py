# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import os
import sys

# -- Path setup --------------------------------------------------------------
from recommonmark.transform import AutoStructify

sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'ICONService API References'
copyright = '2019, ICON Foundation'
author = 'ICON Foundation'

about = {}
path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../iconservice/__version__.py')
with open(path, 'r', encoding='utf-8') as f:
    exec(f.read(), about)

version = about["__version__"]
release = ''


# -- General configuration ---------------------------------------------------

needs_sphinx = '1.8'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'recommonmark'
]

source_suffix = {'.md': 'markdown'}

master_doc = 'index'

add_module_names = False

autodoc_mock_imports = [
    "setproctitle",
    "plyvel",
    "earlgrey",
    "iconcommons",
    "coincurve",
]


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_show_sourcelink = False


# -- Options for HTMLHelp output ---------------------------------------------

htmlhelp_basename = 'ICONServicedoc'


# -- Options for manual page output ------------------------------------------

man_pages = [
    (master_doc, 'iconservice', 'ICONService Documentation',
     [author], 1)
]


# -- recommenmark configuration -------------------------------------------------
github_doc_root = 'https://github.com/rtfd/recommonmark/tree/master/doc/'


def setup(app):
    app.add_config_value('recommonmark_config', {
        'url_resolver': lambda url: github_doc_root + url,
        'auto_toc_tree_section': 'Contents',
    }, True)
    app.add_transform(AutoStructify)
