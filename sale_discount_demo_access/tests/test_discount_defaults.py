from odoo.addons.sale_discount_demo_access.models.sale_order import (
    DISCOUNT_KEY,
    GROSS_KEY,
)
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiscountDefaults(TransactionCase):
    """The two discount fixes, from the side that can silently regress.

    Both were reported from a real walkthrough of the guided quotation tour,
    and both fail invisibly: a lost view override leaves a field that accepts
    letters and an "Appliquer" button that stops responding with no error, and
    a lost tax_totals key leaves a discount that is applied but shown nowhere.
    Neither raises. These are the assertions that make them raise.
    """

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Client Test', 'is_company': True, 'customer_rank': 1,
        })
        self.product = self.env['product.product'].create({
            'name': 'Prestation Test', 'type': 'service', 'list_price': 100.0,
        })

    def _order(self, discount=0.0):
        """One line, two units at 100, no tax.

        tax_ids emptied on purpose: the company's default sale tax differs
        between a fresh database and one that has loaded the French chart, and
        the arithmetic these tests are about is the same either way. The
        tax-INCLUDED case, which is the one _methode_gross_untaxed()'s formula
        exists for, is covered separately below.
        """
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 100.0,
                'discount': discount,
                'tax_ids': [(6, 0, [])],
            })],
        })

    # ── The totals ────────────────────────────────────────────────────────

    def test_no_discount_leaves_the_totals_exactly_as_core_built_them(self):
        """Every other model and every undiscounted order must be untouched:
        the rows are gated on this key in both the form widget and the PDF."""
        totals = self._order().tax_totals
        self.assertNotIn(GROSS_KEY, totals)
        self.assertNotIn(DISCOUNT_KEY, totals)

    def test_a_discount_is_reported_as_a_gross_amount_and_a_reduction(self):
        order = self._order(discount=10.0)
        totals = order.tax_totals
        self.assertEqual(totals[GROSS_KEY], 200.0)
        self.assertEqual(totals[DISCOUNT_KEY], 20.0)
        self.assertEqual(totals['base_amount_currency'], 180.0)

    def test_the_column_adds_up(self):
        """The reason there are two rows and not one: "Remise" alone would sit
        above a "Total HT" that already excludes it, and the column a customer
        reads top to bottom would not reconcile."""
        totals = self._order(discount=35.0).tax_totals
        self.assertAlmostEqual(
            totals[GROSS_KEY] - totals[DISCOUNT_KEY],
            totals['base_amount_currency'],
            places=2,
        )

    def test_gross_is_not_inflated_by_a_tax_included_price(self):
        """⚠ THIS IS WHY THE GROSS IS DERIVED FROM price_subtotal.

        On a tax-included price list, price_unit carries the VAT and
        price_subtotal does not. Computing the gross as price_unit x quantity
        would report 240 against a base of 180 on the order below and invent a
        20 % discount out of the tax rate alone -- on orders with NO discount
        at all, since the keys are gated on a non-zero difference.
        """
        tax = self.env['account.tax'].create({
            'name': 'TVA 20 % incluse (test)',
            'amount_type': 'percent',
            'amount': 20.0,
            'price_include_override': 'tax_included',
            'type_tax_use': 'sale',
        })
        order = self._order()
        order.order_line.tax_ids = [(6, 0, tax.ids)]
        self.assertNotIn(
            DISCOUNT_KEY,
            order.tax_totals,
            "an undiscounted tax-included order must report no discount",
        )

        order.order_line.discount = 10.0
        totals = order.tax_totals
        self.assertAlmostEqual(
            totals[GROSS_KEY] - totals[DISCOUNT_KEY],
            totals['base_amount_currency'],
            places=2,
        )
        # 2 x 100 TTC at 20 % is 166.67 HT; a tenth of that is the discount.
        self.assertAlmostEqual(totals[GROSS_KEY], 166.67, places=2)

    # ── The wiring the templates depend on ────────────────────────────────

    def test_the_discount_wizard_uses_the_guarded_widget(self):
        """Without this the Percentage field is core's, which accepts "abc",
        goes invalid on blur and makes Apply a no-op. The failure has no error
        message anywhere, so the view is pinned from here instead."""
        arch = self.env['sale.order.discount'].get_view(
            self.env.ref('sale.sale_order_line_wizard_form').id, 'form'
        )['arch']
        self.assertIn('percentage_digits_only', arch)

    def test_the_printed_totals_carry_the_discount_rows(self):
        """The PDF and the portal both render sale.document_tax_totals; an
        inherit that stops applying takes the discount off the customer-facing
        document while leaving it on screen."""
        arch = self.env.ref('sale.document_tax_totals').get_combined_arch()
        self.assertIn(DISCOUNT_KEY, arch)
