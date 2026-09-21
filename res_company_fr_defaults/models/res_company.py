from odoo import api, models


class ResCompany(models.Model):
    """Default a freshly created company to France/EUR/French.

    Applied after super().create() rather than folded into vals, because the
    "was it explicit" check has to run against the caller's ORIGINAL vals --
    Odoo's own create() already fills in plenty of defaults (e.g. currency
    from the chart template) before this override ever gets control if the
    check ran on the post-create record instead, and by then "explicit" and
    "defaulted by something else" would be indistinguishable.
    """

    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        had_country = [bool(vals.get('country_id')) for vals in vals_list]
        had_currency = [bool(vals.get('currency_id')) for vals in vals_list]
        companies = super().create(vals_list)

        france = self.env.ref('base.fr')
        euro = self.env.ref('base.EUR')
        self.env['res.lang']._activate_lang('fr_FR')

        for company, country_was_set, currency_was_set in zip(
                companies, had_country, had_currency, strict=True):
            if not country_was_set:
                company.country_id = france
            if not currency_was_set:
                company.currency_id = euro
            company.partner_id.lang = 'fr_FR'
        return companies
