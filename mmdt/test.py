import os, sys, importlib, traceback
print('CWD:', os.getcwd())
print('sys.path:', sys.path if sys.path else None)
print('First 5 sys.path entries:', sys.path[:5])
try:
    m = importlib.import_module('api.urls')
    print('Module:', m)
    print('Has urlpatterns:', hasattr(m, 'urlpatterns'))
    print('Type of urlpatterns:', type(getattr(m, 'urlpatterns', None)))
    print('Value of urlpatterns:', getattr(m, 'urlpatterns', None))
except Exception as e:
    print('IMPORT ERROR:', repr(e))
traceback.print_exc()
