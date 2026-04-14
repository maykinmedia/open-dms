===================
Open Documentbeheer
===================

:Version: 0.1.0
:Source: https://github.com/maykinmedia/open-dms
:Keywords: documenten, management, dms, drc
:PythonVersion: 3.12

|ruff|

Document management in `Common Ground`_ maar dan makkelijk (`English version`_).

Ontwikkeld door `Maykin B.V.`_ als onderdeel van Maykin's Open Overheid Initiatief 
({M}OOI).


Introductie
===========

In een `Common Ground`_ omgeving kunnen er meerdere 
document-registratiecomponenten (DRC's) of document-opslaglocaties zijn. Deze documenten kunnen alleen opgevraagd of bekeken worden via hun API's (de 
`Documenten API`_).

Er zijn een paar oplossingen die een beheerlaag (DMS) combineren met hun registratielaag. In Common Ground moeten deze twee lagen echter gescheiden 
zijn: Het scheiden van de gebruikersinterface van de gegevens.

Open Documentbeheer is een DRC-leverancieronafhankelijke oplossing die werkt op 
basis van de Documenten API-specificatie en met meerdere DRC's tegelijk kan 
werken. Zoek, open, bekijk, download en bewerk documenten eenvoudig, terwijl je
alles georganiseerd houdt in je eigen datalaag.


Documentatie
=============

Lees ``INSTALL.rst`` voor installatie instructies, beschikbare instellingen en
commando's.


Links
=====

* `Issues <https://taiga.maykinmedia.nl/project/opendms>`_
* `Code <https://bitbucket.org/maykinmedia/opendms>`_
.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff


Licentie
========

Copyright © Maykin B.V., 2026

Licensed under the `Business Source License`_ (BSL) 1.1

* `Waarom deze licentie?`_ :bulb: 


.. _`Maykin B.V.``: https://www.maykinmedia.nl
.. _`Common Ground`: https://www.commonground.nl
.. _`Documenten API`: https://vng-realisatie.github.io/gemma-zaken/standaard/documenten/
.. _`English version`: README.EN.rst
.. _`Business Source License`: LICENSE.md
.. _`Waarom deze licentie?`: https://github.com/maykinmedia/open-dms/blob/main/docs/why-bsl.rst
