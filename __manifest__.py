{
    'name': 'Demo Config Defaults - Methode',
    'author': 'Méthode - Progiciel sur Mesure',
    'version': '19.0.2.0.0',
    'category': 'Technical',
    'summary': "Universal sane defaults for every demo template (SHARED_ADDONS)",
    'description': """
A home for company-wide settings a demo lead should never have to (and, once
base.group_system is withheld -- demo_lead.py's _create_lead_user, CANNOT)
flip on themselves via Settings. First tenant: sale order line discounts.

Every demo lead's user is deliberately built WITHOUT base.group_system
(PLAN.md §10 item "no app installs, no hardcore settings"), and
sale.menu_sale_general_settings (Sales > Configuration > Settings) turns out
to be gated by base.group_system alone, not sales_team.group_sale_manager --
verified live against the running dev database. So a feature that is only a
Settings checkbox away in a normal install (e.g. "Discounts" on the order
line) is otherwise unreachable for a lead. This addon pre-applies exactly
what checking that box does -- an implied_group grant on base.group_user --
at template-build time instead.

Second tenant, same root cause: a direct "Mise en page des documents" menu
under the Sales app root (data/document_layout_menu.xml), gated only by
base.group_user, so a lead can still reach the Document Layout wizard —
sale.menu_sale_general_settings, the normal path to it, is behind
base.group_system too and would otherwise be a dead end.

Third and fourth tenants are about the discount once it is enabled, both
reported from a real walkthrough of the guided tour:

  - the wizard's Percentage field accepted letters, went invalid on blur and
    made "Appliquer" stop responding with no visible cause
    (views/sale_order_discount_views.xml + the percentage_digits_only widget);
  - an applied discount appeared nowhere in the totals, because Odoo folds it
    into price_subtotal before the tax engine runs. models/sale_order.py adds
    a gross amount and a discount row to tax_totals, rendered in the form view
    and in the printed quotation.

Baked into every template via SHARED_ADDONS (build_demo_templates.py), same
as demo_access_methode.
""",
    'depends': ['sale_management'],
    'data': [
        'data/document_layout_menu.xml',
        'views/sale_order_discount_views.xml',
        'views/sale_report_discount_totals.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'methode_demo_config_defaults/static/src/js/percentage_input_guard.js',
            'methode_demo_config_defaults/static/src/xml/tax_totals_discount.xml',
        ],
        'web.assets_unit_tests': [
            'methode_demo_config_defaults/static/tests/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
