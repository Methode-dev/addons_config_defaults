{
    'name': 'Company France Defaults - Methode',
    'author': 'Méthode - Progiciel sur Mesure',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': "New companies default to France/EUR/French (SHARED_ADDONS)",
    'description': """
A freshly created res.company defaulted to whatever country/currency Odoo's
own installer picked, not France/EUR -- models/res_company.py fills those in
(plus the company partner's language) whenever a create() call leaves them
unset, without touching an explicit choice.

Baked into every template via SHARED_ADDONS (build_demo_templates.py), same
as demo_access_methode.

Split out of the combined addons_config_defaults bundle: this concern shares
no code, data or tests with sale_discount_demo_access or
first_login_password_totp, the other two addons that used to live in the
same manifest.
""",
    'depends': ['base'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
