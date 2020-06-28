import os
from setuptools import setup, find_packages

def get_version():
    for line in open(os.path.join(os.path.dirname(__file__), 'nasa_hls', '__init__.py')):
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"').strip("'")
    return version

def parse_requirements(file):
    return sorted(set(
        line.partition('#')[0].strip()
        for line in open(os.path.join(os.path.dirname(__file__), file))
    ) - set(''))

setup(
    name='nasa_hls',
    version=get_version(),
    url='https://github.com/benmack/nasa_hls',
    license='MIT',
    author='Benjamin Mack',
    author_email='ben8mack@gmail.com',
    description='Download data from NASA\'s Harmonized Landsat and Sentinel-2 project.',
    packages=find_packages(),
    install_requires=parse_requirements("requirements.txt"),
    setup_requires=["pytest-runner"],
    tests_require=['pytest'],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        hls_query=nasa_hls.scripts.query:query
        hls_download=nasa_hls.scripts.download:download
        hls_convert_batch=nasa_hls.scripts.convert:convert_batch
    ''',
)