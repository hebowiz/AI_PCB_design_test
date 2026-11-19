"""Small KiCad S-expression reader; preserves atoms versus quoted strings."""
import re

class Q(str):
    pass

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack = []
    root = []
    cur = root
    for tok in tokens:
        if tok == '(':
            child = []
            cur.append(child)
            stack.append(cur)
            cur = child
        elif tok == ')':
            cur = stack.pop()
        else:
            cur.append(Q(tok[1:-1].replace('\\"', '"').replace('\\\\', '\\')) if tok.startswith('"') else tok)
    return root[0]

def dump(obj):
    if isinstance(obj, list):
        return '(' + ' '.join(map(dump, obj)) + ')'
    if isinstance(obj, Q):
        return '"' + obj.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return str(obj)

def children(obj, key):
    return [x for x in obj if isinstance(x, list) and x and x[0] == key]

def one(obj, key, default=None):
    return next(iter(children(obj, key)), default)
