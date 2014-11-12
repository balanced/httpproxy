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
    import httpproxy
    version = httpproxy.__version__
except ImportError:
    pass

setup(
    name='httpproxy',
    version=version,
    packages=find_packages(),
    url='https://github.com/balanced/httpproxy',
    author='victorlin',
    author_email='victorlin@balancedpayments.com',
    install_requires=[
        'Flask >=0.8,<0.11',
        'urllib3 >=1.7.1,<2.0',
        'coid >=0.1,<0.2',
        'ohmr >=0.1,<0.2',
        'netaddr >=0.7.10,<0.8',
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
