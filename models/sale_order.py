from odoo import api, models

# The two keys this module adds to the tax_totals payload. Namespaced because
# that dict is core's and gets deep-copied straight into a client component; a
# bare "discount_amount_currency" would be indistinguishable from something
# Odoo might add upstream tomorrow.
GROSS_KEY = 'methode_discount_base_amount_currency'
DISCOUNT_KEY = 'methode_discount_amount_currency'


class SaleOrder(models.Model):
    """Make an applied discount visible in the totals.

    Odoo folds a line's `discount` into its `price_subtotal` before the tax
    engine ever sees it, so `account.tax._get_tax_totals_summary()` has no
    notion of a discount at all -- take 10 % off every line of a quotation and
    the only trace anywhere on the screen is a "Disc.%" column on the lines
    themselves, which the printed report hides entirely unless a line carries
    one. The lead applies a discount and nothing in the totals moves except
    numbers they were not watching. Reported from a real walkthrough of the
    guided tour, whose whole discount sequence lands on a screen that does not
    acknowledge it.

    Two rows are added, not one: a "Remise" line on its own would sit above a
    "Total HT" that already excludes it, and the column would not add up. With
    the gross amount above it, the arithmetic reads top to bottom.
    """

    _inherit = 'sale.order'

    @api.depends_context('lang')
    @api.depends(
        'order_line.price_subtotal', 'order_line.discount',
        'currency_id', 'company_id', 'payment_term_id',
    )
    def _compute_tax_totals(self):
        """order_line.discount is added to core's own depends list.

        It is arguably redundant -- changing a discount recomputes
        price_subtotal, which is already a trigger -- but an override that
        re-declares @api.depends REPLACES the inherited one rather than adding
        to it, so the list has to be complete either way, and being explicit
        about the field this override actually reads is worth one line.
        """
        super()._compute_tax_totals()
        for order in self:
            totals = order.tax_totals
            if not totals:
                continue
            gross = order._methode_gross_untaxed()
            base = totals.get('base_amount_currency') or 0.0
            currency = order.currency_id or order.company_id.currency_id
            discount = gross - base
            if not currency or currency.is_zero(discount) or discount < 0:
                continue
            totals[GROSS_KEY] = currency.round(gross)
            totals[DISCOUNT_KEY] = currency.round(discount)
            # Reassigned rather than mutated in place: the dict is already in
            # the field cache, so mutation happens to work, but a compute that
            # writes its field is the only version that stays true if Binary
            # ever starts copying on read.
            order.tax_totals = totals

    def _methode_gross_untaxed(self):
        """What the untaxed total would have been at full price.

        Derived from price_subtotal rather than from price_unit * quantity, and
        that is the whole subtlety here: on a tax-INCLUDED price list,
        price_unit carries the tax and price_subtotal does not, so multiplying
        out would overstate the gross by the VAT rate and invent a discount on
        an order that has none. Undoing the discount factor keeps the figure in
        exactly the same tax basis as the "Total HT" it sits above:

            price_subtotal = base(price_unit x qty) x (1 - discount/100)

        and base() is linear, so dividing back out is exact.
        """
        self.ensure_one()
        gross = 0.0
        for line in self._get_priced_lines():
            rate = (line.discount or 0.0) / 100.0
            if rate >= 1.0:
                # 100 % off leaves price_subtotal at zero, which remembers
                # nothing about what it was. Falling back to the raw line
                # amount is approximate under tax-included pricing and is the
                # only figure still available.
                gross += line.price_unit * line.product_uom_qty
            else:
                gross += line.price_subtotal / (1.0 - rate)
        return gross
