from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFirstLoginWizard(TransactionCase):
    """is_first_successful_login only ever moves True -> False, and only
    through a fully completed first.login.good.practice: a half-finished
    attempt (wrong current password, mismatched confirmation, wrong TOTP
    code) must leave the user exactly as exposed as before it ran.
    """

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Nouvel Utilisateur',
            'login': 'nouvel.utilisateur@example.com',
            'password': 'CorrectHorseBattery1',
        })

    def _wizard(self):
        return self.env['first.login.good.practice'].with_user(self.user).create({})

    # ── The flag itself ─────────────────────────────────────────────────

    def test_a_freshly_created_user_owes_the_flow(self):
        self.assertTrue(self.user.is_first_successful_login)

    # ── Wiring, not the crypto ──────────────────────────────────────────

    def test_confirm_creates_and_shows_a_real_totp_wizard(self):
        """The QR code and secret come from auth_totp.wizard itself
        (models/first_login_good_practice.py deliberately reuses it rather
        than generating its own); this only checks that the sub-record and
        its related display fields are actually wired up."""
        wizard = self._wizard()
        self.assertTrue(wizard.totp_wizard_id)
        self.assertEqual(wizard.totp_wizard_id.user_id, self.user)
        self.assertTrue(wizard.totp_qrcode)
        self.assertEqual(wizard.totp_secret_display, wizard.totp_wizard_id.secret)

    def test_confirm_with_valid_data_completes_both_steps(self):
        wizard = self._wizard()
        wizard.write({
            'current_password': 'CorrectHorseBattery1',
            'new_password': 'AnotherStrongPass2',
            'confirm_password': 'AnotherStrongPass2',
        })
        code = _totp_code_for(wizard.totp_wizard_id.secret)
        wizard.totp_code = code
        wizard.action_confirm()

        self.assertFalse(self.user.is_first_successful_login)
        self.assertTrue(self.user.totp_enabled)

    def test_mismatched_confirmation_leaves_the_flag_untouched(self):
        wizard = self._wizard()
        wizard.write({
            'current_password': 'CorrectHorseBattery1',
            'new_password': 'AnotherStrongPass2',
            'confirm_password': 'SomethingElseEntirely3',
            'totp_code': _totp_code_for(wizard.totp_wizard_id.secret),
        })
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        self.assertTrue(self.user.is_first_successful_login)
        self.assertFalse(self.user.totp_enabled)

    def test_wrong_totp_code_leaves_the_flag_untouched(self):
        """The password half must not be committed on its own either: a user
        who gets this far and then fumbles the 6-digit code should not walk
        away with a changed password and no 2FA, silently worse off than
        before if they forget the new password."""
        wizard = self._wizard()
        wizard.write({
            'current_password': 'CorrectHorseBattery1',
            'new_password': 'AnotherStrongPass2',
            'confirm_password': 'AnotherStrongPass2',
            'totp_code': '000000',
        })
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        self.assertTrue(self.user.is_first_successful_login)
        self.assertFalse(self.user.totp_enabled)

    def test_wrong_current_password_is_rejected(self):
        from odoo.exceptions import AccessDenied

        wizard = self._wizard()
        wizard.write({
            'current_password': 'NotTheRealPassword',
            'new_password': 'AnotherStrongPass2',
            'confirm_password': 'AnotherStrongPass2',
            'totp_code': _totp_code_for(wizard.totp_wizard_id.secret),
        })
        with self.assertRaises(AccessDenied):
            wizard.action_confirm()
        self.assertTrue(self.user.is_first_successful_login)


def _totp_code_for(secret):
    """The current 6-digit code for `secret`, computed with the exact same
    HOTP implementation auth_totp itself ships (odoo.addons.auth_totp.models.
    totp.hotp) -- there is nothing addon-specific to fake here, the wizard's
    job is only to wire the real thing up correctly. TOTP.match() takes the
    code to VERIFY, not to generate, so hotp() is what has to be called here.
    """
    import base64
    import functools
    import re
    import time

    from odoo.addons.auth_totp.models.totp import TIMESTEP, hotp

    compress = functools.partial(re.sub, r'\s', '')
    key = base64.b32decode(compress(secret).upper())
    counter = int(time.time() / TIMESTEP)
    return str(hotp(key, counter))
