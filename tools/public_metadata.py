"""Portable copies of observation metadata, without local account or host values.

Use this at serialization boundaries for logs/reports. Do not replace actual
subprocess environments or commands with the returned observation copy.
"""
import json
from pathlib import Path
import re


def public_record(value, root, _key=''):
    root = str(Path(root).resolve())
    home = str(Path.home())
    if _key in {'HOME', 'USERPROFILE'}:
        return '/' + 'home/user'
    if _key in {'PATH', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'VIRTUAL_ENV'}:
        return '<local-environment-omitted>'
    if _key in {'USER', 'LOGNAME', 'USERNAME'}:
        return 'user'
    if _key.casefold() in {'node', 'hostname', 'host_name', 'cpu_model', 'platform', 'cpu_topology', 'topology'}:
        return '<local-host-omitted>'
    if isinstance(value, dict):
        return {public_record(key, root): public_record(item, root, str(key)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [public_record(item, root) for item in value]
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str):
        # Root replacement precedes home replacement so project paths stay portable.
        value = value.replace(root + '/', './').replace(root, '.')
        if home not in ('/', ''):
            value = value.replace(home + '/', '/' + 'home/user/').replace(home, '/' + 'home/user')
        if _key in {'branch', 'ref'}:
            account = Path.home().name
            value = re.sub(r'(?<![A-Za-z0-9_])' + re.escape(account) + r'/', 'user/', value)
    return value


def public_json(value, root, **kwargs):
    return json.dumps(public_record(value, root), **kwargs)
