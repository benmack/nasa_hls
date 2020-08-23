Developer area
==============

Documentation
-------------

The documentation was set up according to the the recipt found in
the Sphinx issue 
`How to use github pages from master /docs folder elegantly with sphinx <https://github.com/sphinx-doc/sphinx/issues/3382>`_.

Docker
------

Build
~~~~~

Currently images build process is as follows (for shell and JupyterLab)::

    docker image build -t benmack/nasa-hls:2020-08-23 -f docker/Dockerfile .
    docker image build -t benmack/nasa-hls-jupyterlab:2020-08-23 -f Dockerfile-jupyterlab . 

Run
~~~

see README.md
