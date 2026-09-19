/** @odoo-module **/

import { useEffect, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { PercentageField, percentageField } from "@web/views/fields/percentage/percentage_field";

/**
 * A percentage field that cannot be made invalid.
 *
 * ── What went wrong without it ─────────────────────────────────────────────
 * The guided quotation tour (devis_demo_tour_methode) asks the lead to type 10
 * into the discount wizard's Percentage field. A lead who typed a letter got:
 * core's useInputField calling parsePercentage() on blur, that throwing,
 * record.setInvalidField() flagging the field red -- and then "Appliquer"
 * doing nothing at all, because the record is invalid. The tour, meanwhile,
 * consumed its step on the click regardless and moved the card to the cog
 * menu, which is *behind* a modal that never closed. From the lead's chair:
 * everything froze. Reported from a real walkthrough as "ça bogue fort".
 *
 * Rejecting the keystroke is the only fix that ends there. Validating on blur
 * would still let the invalid value exist, and the tour would still be
 * stepping past a modal that refuses to close.
 *
 * ── Why beforeinput and not keydown ────────────────────────────────────────
 * keydown sees keys, not text: it misses paste, drag-and-drop, autofill, IME
 * composition and every mobile keyboard that reports Unidentified. beforeinput
 * is the one event that fires for all of them, carries the text about to be
 * inserted, and is cancellable. The cost is having to reconstruct the
 * would-be value from the selection, which nextValue() below does.
 */

/** Digits, optionally one separator, and at least one digit before it.
 *
 * A leading "." or "," is deliberately not a valid intermediate state: nobody
 * reaches a real number that way (you type the 0 first), and allowing it lets
 * the field sit on a string parsePercentage() throws on -- which is the exact
 * state this widget exists to make unreachable. Both separators are accepted
 * because the French locale these clones run in formats with a comma while the
 * numpad and a pasted value routinely carry a dot.
 */
const NUMERIC = /^\d*$|^\d+[.,]\d*$/;

/**
 * 100, and it is core's constraint rather than a house rule: sale.order.discount
 * stores a fraction and _check_discount_amount rejects anything above 1.0 with
 * "Invalid discount amount". Letting 150 be typed just moves the same dead end
 * from a red field to a red dialog.
 */
const MAX_PERCENTAGE = 100;

function insertedText(ev) {
    if (ev.data !== null && ev.data !== undefined) {
        return ev.data;
    }
    // Paste and drop put the payload on dataTransfer and leave data null.
    return ev.dataTransfer ? ev.dataTransfer.getData("text") : "";
}

function nextValue(el, ev) {
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? el.value.length;
    return el.value.slice(0, start) + insertedText(ev) + el.value.slice(end);
}

/**
 * Exported for the unit tests.
 *
 * The whole decision lives in this one pure function precisely so it can be
 * exercised as a table of bad inputs without mounting a view -- `el` is only
 * ever read for .value/.selectionStart/.selectionEnd and `ev` for
 * .inputType/.data/.dataTransfer, so a plain object stands in for both.
 */
export function isAcceptable(el, ev) {
    // Deletions can only ever shorten the value, and "" is a legal state --
    // the field is not required, and blocking backspace would be its own bug.
    if (String(ev.inputType || "").startsWith("delete")) {
        return true;
    }
    const candidate = nextValue(el, ev);
    if (!NUMERIC.test(candidate)) {
        return false;
    }
    const numeric = Number(candidate.replace(",", "."));
    // Not-a-number here means an intermediate like "10," which NUMERIC already
    // vouched for; only a real overshoot is refused.
    return !Number.isFinite(numeric) || numeric <= MAX_PERCENTAGE;
}

export class GuardedPercentageField extends PercentageField {
    setup() {
        super.setup();
        // Same ref name core's own useInputField uses (web.PercentageField
        // renders t-ref="numpadDecimal"), so this is the very input the parent
        // is reading and writing -- not a second one.
        this.guardedInputRef = useRef("numpadDecimal");
        useEffect(
            (el) => {
                if (!el) {
                    return;
                }
                // Phones: a decimal pad instead of the full QWERTY. Prevention
                // is better than rejection when the offending key is simply
                // not on screen.
                el.setAttribute("inputmode", "decimal");
                const onBeforeInput = (ev) => {
                    if (!isAcceptable(el, ev)) {
                        ev.preventDefault();
                    }
                };
                el.addEventListener("beforeinput", onBeforeInput);
                return () => el.removeEventListener("beforeinput", onBeforeInput);
            },
            () => [this.guardedInputRef.el]
        );
    }
}

export const guardedPercentageField = {
    ...percentageField,
    component: GuardedPercentageField,
    displayName: _t("Percentage (digits only)"),
};

registry.category("fields").add("percentage_digits_only", guardedPercentageField);
