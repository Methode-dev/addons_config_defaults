sale_discount_demo_access
==========================

Pre-applies the "Discounts" setting (Sales > Configuration > Settings) that a
demo lead's user -- built without base.group_system -- can never reach
themselves, plus a direct Document Layout menu gated the same way, and the
UI/totals fixes the discount needed once enabled. See the module description
in ``__manifest__.py`` for the full tenant-by-tenant history of what this
addon fixes and why.

.. toctree::
   :maxdepth: 1
   :caption: Addon root

   modules/manifest
   modules/hooks
   modules/init

.. toctree::
   :maxdepth: 1
   :caption: models/

   modules/models_init
   modules/models_sale_order

.. toctree::
   :maxdepth: 1
   :caption: tests/

   modules/tests_init
   modules/tests_discount_defaults
