
====================
IMAGE-ValidationTool
====================

.. image:: https://img.shields.io/travis/cnr-ibba/IMAGE-ValidationTool.svg
        :target: https://travis-ci.org/cnr-ibba/IMAGE-ValidationTool

.. image:: https://coveralls.io/repos/github/cnr-ibba/IMAGE-ValidationTool/badge.svg?branch=master
        :target: https://coveralls.io/github/cnr-ibba/IMAGE-ValidationTool?branch=master

IMAGE Validation Tool component of the IMAGE Inject Tool

Install From sources
--------------------

The sources for IMAGE Validation Tool can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/cnr-ibba/IMAGE-ValidationTool

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/cnr-ibba/IMAGE-ValidationTool/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install

If you need to modify libraries, you could prefer to install package in editable
mode. Please ensure that you removed the old pakcage if installed

.. code-block:: console

    $ pip uninstall image-validation

Then install the package with PIP:

.. code-block:: console

    $ pip install -e .


.. _Github repo: https://github.com/cnr-ibba/IMAGE-ValidationTool
.. _tarball: https://github.com/cnr-ibba/IMAGE-ValidationTool/tarball/master
