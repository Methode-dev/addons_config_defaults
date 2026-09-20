from odoo import fields, models


class ResUsers(models.Model):
    """Track whether a user still owes the mandatory first-login flow.

    is_first_successful_login is a misnomer kept on purpose -- the brief that
    commissioned this field names it that way, and matching the client's own
    vocabulary here beats a technically tighter name nobody asked for. What it
    actually means is "has NOT yet completed first_login_good_practice": it
    defaults True at creation and is flipped to False only by that wizard's
    action_confirm, once both the password change and the TOTP enrolment
    succeeded. Nothing hooks into the login codepath itself to compute it --
    nothing needs to, and every private method under res.users._login /
    _update_last_login would have been a private-API bet this field doesn't
    need to make.
    """

    _inherit = 'res.users'

    is_first_successful_login = fields.Boolean(
        default=True,
        copy=False,
        help="Coché tant que l'utilisateur n'a pas changé son mot de passe "
             "initial et activé la double authentification.",
    )
