first_login_password_totp
===========================

Admin-assigned passwords were never forced to change, and no user had 2FA --
whoever learned an initial password kept standing access indefinitely.
res.users gains ``is_first_successful_login`` (models/res_users.py), surfaced
to the client via ``ir.http.session_info()`` (models/ir_http.py) for internal
users only, and enforced by a single wizard (first.login.good.practice) that
makes the user set a new password and enroll in TOTP together before they can
use anything else. See the module description in ``__manifest__.py`` for the
full history of what this addon fixes and why.

.. toctree::
   :maxdepth: 1
   :caption: Addon root

   modules/manifest
   modules/init

.. toctree::
   :maxdepth: 1
   :caption: models/

   modules/models_init
   modules/models_first_login_good_practice
   modules/models_ir_http
   modules/models_res_users

.. toctree::
   :maxdepth: 1
   :caption: tests/

   modules/tests_init
   modules/tests_first_login_wizard
