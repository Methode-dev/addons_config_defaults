from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Tell the webclient whether this user still owes the first-login
        flow, so first_login_guard_service.js can act on it the moment the
        client boots -- session_info is rebuilt (never cached) on every load,
        so a wizard completed in the previous session is reflected instantly.

        Restricted to internal users on purpose: the brief this addon
        implements is about admin-assigned staff passwords, and portal users
        (self-signed-up, never handed a password by an admin) are out of
        scope.
        """
        result = super().session_info()
        if result.get('uid') and self.env.user._is_internal():
            result['must_complete_first_login'] = self.env.user.is_first_successful_login
        return result
