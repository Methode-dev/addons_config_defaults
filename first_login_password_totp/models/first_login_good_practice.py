import base64
import os

from odoo import _, api, fields, models
from odoo.addons.auth_totp.models.totp import TOTP_SECRET_SIZE
from odoo.exceptions import ValidationError

MIN_PASSWORD_LENGTH = 8


class FirstLoginGoodPractice(models.TransientModel):
    """Force a new password and 2FA enrolment before a first-timer can work.

    Both steps live on one form behind one Confirm button instead of two
    separate dismissible dialogs, because two wizards is two chances to close
    one and stop -- neither step here is meant to be optional. The TOTP half
    reuses auth_totp.wizard's own secret generation and QR rendering
    untouched (totp_wizard_id below); only the access checks that normally
    gate that machinery are bypassed on purpose, and both exist to protect a
    scenario this flow already covers by construction:

      - res.users.action_totp_enable_wizard() and auth_totp.wizard.enable()
        are both @check_identity, which re-asks for the CURRENT password
        before letting an already-logged-in user touch their own 2FA
        settings from Preferences. Here the user is mid-way through PROVING
        they know that exact password -- it is current_password below --
        so gating the TOTP step behind the same proof a second time would
        only be a redundant click, not additional security.
      - so action_confirm calls res.users._totp_try_setting() directly, the
        private method both of the above ultimately call, instead of going
        through either @check_identity wrapper.
    """

    _name = 'first.login.good.practice'
    _description = "Assistant première connexion"
    _transient_max_hours = 0.1

    # Not required=True: that would be a DB-level NOT NULL, which blocks the
    # very default_get()-only create() below that puts the QR code on screen
    # before the user has typed anything -- the same reason core's own
    # change.password.own wizard (odoo/addons/base/models/res_users.py)
    # leaves its equivalent fields plain and checks them in code instead.
    current_password = fields.Char(string="Mot de passe actuel")
    new_password = fields.Char(string="Nouveau mot de passe")
    confirm_password = fields.Char(string="Confirmer le mot de passe")
    totp_wizard_id = fields.Many2one(
        'auth_totp.wizard',
        string="Activation de la double authentification",
    )
    # Related rather than shown via a nested sub-form: a Many2one field
    # cannot host an inline <form> the way a One2many can, so the two bits of
    # totp_wizard_id the view actually needs to render (the QR code, and the
    # secret as a fallback for a phone camera that can't reach it) are
    # exposed directly here instead.
    totp_qrcode = fields.Binary(related='totp_wizard_id.qrcode', readonly=True)
    totp_secret_display = fields.Char(
        string="Clé secrète", related='totp_wizard_id.secret', readonly=True)
    totp_code = fields.Char(string="Code de vérification", size=7)

    @api.model
    def default_get(self, fields_list):
        """Pre-create the embedded TOTP secret so its QR code is already on
        screen -- generating it only after Confirm would mean showing an
        empty form first and a second round-trip before there's anything to
        scan.
        """
        vals = super().default_get(fields_list)
        if 'totp_wizard_id' in fields_list and not vals.get('totp_wizard_id'):
            totp_wizard = self.env['auth_totp.wizard'].search(
                [('user_id', '=', self.env.user.id)], order='id desc', limit=1)
            if not totp_wizard:
                secret = base64.b32encode(os.urandom(TOTP_SECRET_SIZE // 8)).decode()
                secret = ' '.join(map(''.join, zip(*[iter(secret)] * 4, strict=False)))
                totp_wizard = self.env['auth_totp.wizard'].create({
                    'user_id': self.env.user.id,
                    'secret': secret,
                })
            vals['totp_wizard_id'] = totp_wizard.id
        return vals

    def action_confirm(self):
        self.ensure_one()
        if not self.new_password:
            raise ValidationError(_("Le nouveau mot de passe est obligatoire."))
        if self.new_password != self.confirm_password:
            raise ValidationError(_(
                "Le nouveau mot de passe et sa confirmation ne correspondent pas."))
        if len(self.new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(_(
                "Le nouveau mot de passe doit contenir au moins %d caractères.",
                MIN_PASSWORD_LENGTH))
        if not self.totp_wizard_id.secret:
            raise ValidationError(_("La session a expiré, veuillez recharger la page."))
        if not self.totp_code:
            raise ValidationError(_(
                "Le code de vérification à 6 chiffres est obligatoire."))
        try:
            # _totp_try_setting compares against hotp()'s return value, which
            # is an int (odoo/addons/auth_totp/models/totp.py hotp()), not a
            # zero-padded string -- an int is what auth_totp.wizard.enable()
            # itself passes it too, for the same reason.
            totp_code = int(self.totp_code)
        except ValueError:
            raise ValidationError(_(
                "Le code de vérification ne doit contenir que des chiffres.")) from None

        # Raises AccessDenied on a wrong current password -- the same check
        # Settings > Change Password relies on (odoo/addons/base/models/
        # res_users.py ResUsers.change_password).
        self.env['res.users'].change_password(self.current_password, self.new_password)

        if not self.env.user._totp_try_setting(self.totp_wizard_id.secret, totp_code):
            raise ValidationError(_("Le code de vérification est incorrect."))

        self.env.user.is_first_successful_login = False
        return {'type': 'ir.actions.act_window_close'}
