from setuptools import setup, find_packages

tests_require = [
    'nose',
    'nose-cov',
    'mock',
    'webtest',
    'WSGIProxy2',
    'jsonschema',
]

version = '0.0.0'
try:
    import htppproxy
    version = htppproxy.__version__
except ImportError:
    pass

setup(
    name='httpproxy',
    version=version,
    packages=find_packages(),
    install_requires=[
        'pyramid',
        'pyramid_debugtoolbar',
    ],
    extras_require=dict(
        tests=tests_require,
    ),
    tests_require=tests_require,
    test_suite='nose.collector',
    entry_points="""\
    [paste.app_factory]
    main = httpproxy:main
    """
)
