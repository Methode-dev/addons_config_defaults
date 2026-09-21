import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Replicate exactly what ticking "Discounts" in Sales > Configuration >
    Settings does, without a lead ever needing to reach that screen.

    Verified the real mechanism in sale/wizard/res_config_settings.py: the
    setting is a plain Boolean field with
    ``implied_group='sale.group_discount_per_so_line'`` -- Odoo's
    res.config.settings framework handles a field like that by adding the
    implied group to base.group_user, nothing more exotic.
    product.group_product_pricelist is added alongside because the real
    Settings form's own @api.depends('group_discount_per_so_line') onchange
    turns that group on too the moment discounts are enabled -- same
    end state, applied directly instead of relying on a UI onchange nobody
    will ever trigger here.
    """
    base_group = env.ref('base.group_user')
    discount_group = env.ref('sale.group_discount_per_so_line')
    pricelist_group = env.ref('product.group_product_pricelist')
    base_group.write({
        'implied_ids': [(4, discount_group.id), (4, pricelist_group.id)],
    })
    _logger.info(
        "sale_discount_demo_access: base.group_user now implies %s, %s",
        discount_group.name, pricelist_group.name,
    )
