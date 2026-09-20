import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { user } from "@web/core/user";

const WIZARD_ACTION_XMLID = "first_login_password_totp.action_first_login_good_practice";

/**
 * Forces first_login_good_practice open the moment the webclient is usable,
 * and again on every subsequent close that didn't clear the flag.
 *
 * There is no dialog prop in Odoo's core Dialog component (@web/core/dialog/
 * dialog.js) to disable its Escape hotkey or hide its close button, and both
 * of those are unconditional there regardless of any prop passed in -- so
 * "blocking" isn't built as a dialog variant here. Instead, the wizard's own
 * onClose is used to re-check res.users.is_first_successful_login and
 * re-open the exact same action if it is still true, whatever caused the
 * close (Escape, the X button, or completing the form without confirming).
 * Only action_confirm on the server ever flips the flag, so the loop breaks
 * exactly when -- and only when -- the flow actually completed.
 */
export const firstLoginGuardService = {
    dependencies: ["action", "orm"],
    start(env, { action, orm }) {
        if (!session.must_complete_first_login) {
            return;
        }

        const openWizard = () => {
            action.doAction(WIZARD_ACTION_XMLID, {
                onClose: async () => {
                    const [record] = await orm.read(
                        "res.users",
                        [user.userId],
                        ["is_first_successful_login"]
                    );
                    if (record.is_first_successful_login) {
                        openWizard();
                    }
                },
            });
        };

        // Not called straight from WEB_CLIENT_READY: WebClient's own
        // onMounted() fires loadRouterState() (which itself calls doAction
        // for the user's default app) in the same tick as WEB_CLIENT_READY,
        // without awaiting it first. Calling our target:'new' doAction
        // immediately loses the race -- confirmed against a real browser:
        // the promise resolves with no error, but no .o_dialog ever mounts,
        // because the router's own action-loading tears down whatever the
        // action manager was in the middle of stacking. Waiting for the
        // router's action to finish rendering (ACTION_MANAGER:UI-UPDATED)
        // before stacking our dialog on top removes the race; the timeout
        // is a safety net for the case where a user has no default action
        // at all and that event never fires.
        const clientReadyListener = () => {
            env.bus.removeEventListener("WEB_CLIENT_READY", clientReadyListener);
            let opened = false;
            const openOnce = () => {
                if (opened) {
                    return;
                }
                opened = true;
                env.bus.removeEventListener("ACTION_MANAGER:UI-UPDATED", openOnce);
                openWizard();
            };
            env.bus.addEventListener("ACTION_MANAGER:UI-UPDATED", openOnce);
            browser.setTimeout(openOnce, 3000);
        };
        env.bus.addEventListener("WEB_CLIENT_READY", clientReadyListener);
    },
};

registry.category("services").add("firstLoginGuard", firstLoginGuardService);
