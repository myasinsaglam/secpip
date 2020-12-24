import sys
import os
import codecs
import setuptools


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")



setuptools.setup(
    name='secpip',
    version=get_version("src/__init__.py"),
    # scripts=['src/secpip', 'bin/secpip'],
    author=['M.Yasin SAGLAM'],
    author_email='myasinsaglam@crypttech.com',
    license='MIT',
    description='Secure Pip Package Management Tool',
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    url='https://github.com/myasinsaglam/secpip',
    packages=setuptools.find_packages(exclude=["test", "excluded"]),
    package_data={"":["*"]},
    entry_points={
        'console_scripts': [
            "secpip=src.secpip:main",
            "secpip{}=src.secpip:main".format(sys.version_info[0]),
            "secpip{}.{}=src.secpip:main".format(*sys.version_info[:2]),
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License ',
        'Natural Language :: English',
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security",
        "Topic :: Software Development",
        "Topic :: Text Processing",
        "Topic :: Utilities"
    ],

    keywords='secpip python pip security vulnerability secure package install manage dump download report migrate '
             'uninstall',
    install_requires=[
        'packaging',
        'pip==20.2.4',
        'requests',
        'termcolor',
        'virtualenv'
    ],
)