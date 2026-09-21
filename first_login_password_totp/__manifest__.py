{
    'name': 'First Login Password & TOTP - Methode',
    'author': 'Méthode - Progiciel sur Mesure',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': "Force a password change and TOTP enrollment on first login (SHARED_ADDONS)",
    'description': """
Admin-assigned passwords were never forced to change, and no user had 2FA --
whoever learned an initial password kept standing access indefinitely.
res.users gains is_first_successful_login (models/res_users.py), surfaced to
the client via ir.http.session_info() (models/ir_http.py) for internal users
only, and enforced by a single wizard (first.login.good.practice) that makes
the user set a new password and enroll in TOTP together before they can use
anything else. Reading web/static/src/core/dialog/dialog.js confirmed core's
Dialog has no prop to disable its Escape hotkey or its close button, so
"blocking" isn't a dialog prop here: first_login_guard_service.js reopens the
same action the instant it closes without the flag having cleared, on the X
button, Escape and everything else alike.

Baked into every template via SHARED_ADDONS (build_demo_templates.py), same
as demo_access_methode.

Split out of the combined addons_config_defaults bundle: this concern shares
no code, data or tests with sale_discount_demo_access or
res_company_fr_defaults, the other two addons that used to live in the same
manifest.
""",
    'depends': ['auth_totp'],
    'data': [
        'security/ir.model.access.csv',
        'views/first_login_good_practice_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'first_login_password_totp/static/src/services/first_login_guard_service.js',
            'first_login_password_totp/static/src/scss/first_login_good_practice.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
