===================
Open Documentbeheer
===================

:Version: 0.1.0
:Source: https://github.com/maykinmedia/open-dms
:Keywords: documents, management, dms, drc
:PythonVersion: 3.12

|ruff|

Document management in `Common Ground`_ made easy (`Nederlandse versie`_).

Developed by `Maykin B.V.`_ as part of Maykin's Open Overheid Initiatief 
({M}OOI).


Introduction
============

In a `Common Ground`_ setting, there can be multiple Document Registration 
Components (DRCs), or document storage locations. These documents can only be
retrieved or viewed via the their API's (the `Documenten API`_).

There a few solutions that combine a management (DMS) layer on top of their
registration layer. However, in Common Ground, these 2 layers should be 
separated: You want to keep your UI seperated from the data.

Open Documentbeheer is a DRC vendor independent solution that works based on
the Documenten API specification and can work with multiple DRCs at the same
time. Search, open, view, download and edit documents with ease while keeping
everything organized in your own data layer.


Documentation
=============

See ``INSTALL.rst`` for installation instructions, available settings and
commands.


References
==========

* `Issues <https://taiga.maykinmedia.nl/project/opendms>`_
* `Code <https://bitbucket.org/maykinmedia/opendms>`_
.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff


Licentie
========

Copyright © Maykin B.V., 2026

Licensed under the `Business Source License`_ (BSL) 1.1

* `Why this license?`_ :bulb: 


.. _`Maykin B.V.``: https://www.maykinmedia.nl
.. _`Common Ground`: https://www.commonground.nl
.. _`Documenten API`: https://vng-realisatie.github.io/gemma-zaken/standaard/documenten/
.. _`Nederlandse versie`: README.rst
.. _`Business Source License`: LICENSE.md
.. _`Waarom deze licentie?`: https://github.com/maykinmedia/open-dms/blob/main/docs/why-bsl.rst

