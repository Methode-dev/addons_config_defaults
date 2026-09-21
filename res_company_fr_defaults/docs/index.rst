res_company_fr_defaults
=========================

A freshly created res.company defaulted to whatever country/currency Odoo's
own installer picked, not France/EUR -- models/res_company.py fills those in
(plus the company partner's language) whenever a create() call leaves them
unset, without touching an explicit choice. See the module description in
``__manifest__.py`` for the full history of what this addon fixes and why.

.. toctree::
   :maxdepth: 1
   :caption: Addon root

   modules/manifest
   modules/init

.. toctree::
   :maxdepth: 1
   :caption: models/

   modules/models_init
   modules/models_res_company

.. toctree::
   :maxdepth: 1
   :caption: tests/

   modules/tests_init
   modules/tests_company_fr_defaults
