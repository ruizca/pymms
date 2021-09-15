pymms
=====
.. inclusion-marker-main-readme

``pymms`` is a simple Python 3 wrapper for the
Portable, Interactive Multi-Mission Simulator (`PIMMS`_).
PIMMS is developed by NASA's High Energy Astrophysics 
Science Archive Research Center (`HEASARC`_)

Dependencies
------------
``pymms`` needs a working PIMMS `installation`_.

Example
-------
A simple example of using ``pymms``:

.. code-block:: python

    >>> from pymms import pimms
    >>> pimms(
    ...     flux=1e-14,
    ...     mission="xmm",
    ...     detector="pn", 
    ...     filter="thin", 
    ...     model="powerlaw", 
    ...     phoindex=2.0,
    ...     nh=1e22,
    ...     z=3.0, 
    ...     galnh=1e20,
    ...     input_energy_range=(0.5, 2.0),
    ...     output_energy_range=(2.0, 10.0),
    ... )
    0.001704

.. _PIMMS: https://heasarc.gsfc.nasa.gov/docs/software/tools/pimms.html
.. _HEASARC: https://heasarc.gsfc.nasa.gov/
.. _installation: https://heasarc.gsfc.nasa.gov/docs/software/tools/pimms_install.html