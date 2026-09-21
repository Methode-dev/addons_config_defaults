from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCompanyFrDefaults(TransactionCase):
    """A company created with nothing specified must land on France/EUR/
    French, but an explicit choice -- however unlikely a Méthode deployment
    is to make one -- must survive untouched. Getting the second half wrong
    would make this addon actively hostile to the one non-French tenant that
    ever needs one.
    """

    def test_a_bare_company_defaults_to_france_euro_and_french(self):
        company = self.env['res.company'].create({'name': 'Nouvelle Société'})
        self.assertEqual(company.country_id, self.env.ref('base.fr'))
        self.assertEqual(company.currency_id, self.env.ref('base.EUR'))
        self.assertEqual(company.partner_id.lang, 'fr_FR')

    def test_an_explicit_country_and_currency_are_not_overridden(self):
        """USD rather than EUR on purpose: passing EUR here would coincide
        with the default and prove nothing about the override actually being
        skipped."""
        belgium = self.env.ref('base.be')
        usd = self.env.ref('base.USD')
        usd.active = True
        company = self.env['res.company'].create({
            'name': 'Filiale Belge',
            'country_id': belgium.id,
            'currency_id': usd.id,
        })
        self.assertEqual(company.country_id, belgium)
        self.assertEqual(company.currency_id, usd)

    def test_an_explicit_partner_language_is_not_overridden(self):
        company = self.env['res.company'].create({'name': 'Filiale Anglophone'})
        company.partner_id.lang = 'en_US'
        # Re-saving the company must not stomp back over a language the
        # partner was deliberately given after creation -- the override only
        # ever runs inside create(), never on write().
        company.write({'name': 'Filiale Anglophone (renommée)'})
        self.assertEqual(company.partner_id.lang, 'en_US')
