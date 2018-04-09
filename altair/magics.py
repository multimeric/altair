"""
Magic functions for rendering vega/vega-lite specifications
"""
__all__ = ['vega', 'vegalite']

import json

import IPython
from IPython.core import magic, magic_arguments
import pandas as pd
import six
from toolz import pipe

from altair.vegalite import v1 as vegalite_v1
from altair.vegalite import v2 as vegalite_v2
from altair.vega import v2 as vega_v2
from altair.vega import v3 as vega_v3


RENDERERS = {
  'vega': {
      '2': vega_v2.Vega,
      '3': vega_v3.Vega,
  },
  'vega-lite': {
      '1': vegalite_v1.VegaLite,
      '2': vegalite_v2.VegaLite,
  }
}


TRANSFORMERS = {
  'vega': {
      # Vega doesn't yet have specific data transformers; use vegalite
      '2': vegalite_v1.data.data_transformers,
      '3': vegalite_v2.data.data_transformers,
  },
  'vega-lite': {
      '1': vegalite_v1.data.data_transformers,
      '2': vegalite_v2.data.data_transformers,
  }
}


def _prepare_data(data, data_transformers):
    """Convert input data to data for use within schema"""
    if data is None or isinstance(data, dict):
        return data
    elif isinstance(data, pd.DataFrame):
        return pipe(data, data_transformers.get())
    elif isinstance(data, six.string_types):
        return {'url': data}
    else:
        warnings.warn("data of type {0} not recognized".format(type(data)))
        return data


def _get_variable(name):
    """Get a variable from the notebook namespace."""
    ip = IPython.get_ipython()
    if name not in ip.user_ns:
        raise NameError("argument '{0}' does not match the "
                        "name of any defined variable".format(name))
    return ip.user_ns[name]


@magic.register_cell_magic
@magic_arguments.magic_arguments()
@magic_arguments.argument(
    'data',
    nargs='*',
    help='local variable name of a pandas DataFrame to be used as the dataset')
@magic_arguments.argument('-v', '--version', dest='version', default='3')
@magic_arguments.argument('-y', '--yaml', dest='yaml', action='store_true')
def vega(line, cell):
    """Cell magic for displaying Vega visualizations in CoLab.

    %%vega [name1:variable1 name2:variable2 ...] [--yaml] [--version='3']

    Visualize the contents of the cell using Vega, optionally specifying
    one or more pandas DataFrame objects to be used as the datasets.

    If --yaml is passed, then input is parsed as yaml rather than json.
    """
    args = magic_arguments.parse_argstring(vega, line)

    version = args.version
    assert version in RENDERERS['vega']
    Vega = RENDERERS['vega'][version]
    data_transformers = TRANSFORMERS['vega'][version]

    def namevar(s):
        s = s.split(':')
        if len(s) == 1:
            return s[0], s[0]
        elif len(s) == 2:
            return s[0], s[1]
        else:
            raise ValueError("invalid identifier: '{0}'".format(s))

    try:
        data = list(map(namevar, args.data))
    except ValueError:
        raise ValueError("Could not parse arguments: '{0}'".format(line))

    if args.yaml:
        import yaml
        spec = yaml.load(cell)
    else:
        spec = json.loads(cell)

    if data:
        spec['data'] = []
        for name, val in data:
            val = _get_variable(val)
            prepped = _prepare_data(val, data_transformers)
            prepped['name'] = name
            spec['data'].append(prepped)

    return Vega(spec)


@magic.register_cell_magic
@magic_arguments.magic_arguments()
@magic_arguments.argument(
    'data',
    nargs='?',
    help='local variablename of a pandas DataFrame to be used as the dataset')
@magic_arguments.argument('-v', '--version', dest='version', default='2')
@magic_arguments.argument('-y', '--yaml', dest='yaml', action='store_true')
def vegalite(line, cell):
    """Cell magic for displaying vega-lite visualizations in CoLab.

    %%vegalite [dataframe] [--yaml] [--version=2]

    Visualize the contents of the cell using Vega-Lite, optionally
    specifying a pandas DataFrame object to be used as the dataset.

    if --yaml is passed, then input is parsed as yaml rather than json.
    """
    args = magic_arguments.parse_argstring(vegalite, line)
    version = args.version
    assert version in RENDERERS['vega-lite']
    VegaLite = RENDERERS['vega-lite'][version]
    data_transformers = TRANSFORMERS['vega-lite'][version]

    if args.yaml:
        import yaml
        spec = yaml.load(cell)
    else:
        spec = json.loads(cell)
    if args.data is not None:
        data = _get_variable(args.data)
        spec['data'] = _prepare_data(data, data_transformers)

    return VegaLite(spec)
