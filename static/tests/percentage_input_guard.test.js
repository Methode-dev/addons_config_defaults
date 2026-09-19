import { describe, expect, test } from "@odoo/hoot";

import { isAcceptable } from "@methode_demo_config_defaults/js/percentage_input_guard";

describe.current.tags("headless");

/**
 * The bad-input matrix the discount field has to survive.
 *
 * Aimed at the predicate rather than at a mounted view on purpose: what broke
 * in front of a prospect was one decision -- "may this text enter the field" --
 * and every mounting detail between the keyboard and that decision is core's,
 * already covered by core, and would only make these cases harder to read.
 *
 * ⚠ This file needs a browser to run (hoot drives a real DOM), and the dev
 * image has no chrome binary on arm64 -- same constraint
 * devis_demo_tour_methode's Python suite documents for start_tour. It runs in
 * CI / on an x86 host; locally the behaviour is confirmed by walking the tour.
 */

/** A stand-in for the input: only value + selection are ever read. */
function input(value = "", { start = null, end = null } = {}) {
    return {
        value,
        selectionStart: start === null ? value.length : start,
        selectionEnd: end === null ? (start === null ? value.length : start) : end,
    };
}

function typed(text) {
    return { inputType: "insertText", data: text };
}

function pasted(text) {
    return {
        inputType: "insertFromPaste",
        data: null,
        dataTransfer: { getData: () => text },
    };
}

describe("what the discount percentage refuses", () => {
    test("letters, in any position", () => {
        expect(isAcceptable(input(""), typed("abc"))).toBe(false);
        expect(isAcceptable(input("10"), typed("a"))).toBe(false);
        expect(isAcceptable(input(""), typed("a"))).toBe(false);
    });

    test("scientific notation, which parseFloat would have swallowed", () => {
        expect(isAcceptable(input(""), typed("1e5"))).toBe(false);
        expect(isAcceptable(input("1"), typed("e"))).toBe(false);
    });

    test("signs and arithmetic", () => {
        expect(isAcceptable(input(""), typed("-"))).toBe(false);
        expect(isAcceptable(input(""), typed("--"))).toBe(false);
        expect(isAcceptable(input("10"), typed("+5"))).toBe(false);
    });

    test("a leading separator, which parsePercentage throws on", () => {
        expect(isAcceptable(input(""), typed(","))).toBe(false);
        expect(isAcceptable(input(""), typed("."))).toBe(false);
    });

    test("a second separator", () => {
        expect(isAcceptable(input("10,5"), typed(","))).toBe(false);
    });

    test("more than 100 %, which core's own constraint rejects anyway", () => {
        expect(isAcceptable(input("15"), typed("0"))).toBe(false);
        expect(isAcceptable(input("10"), typed("1"))).toBe(false);
        expect(isAcceptable(input(""), typed("999"))).toBe(false);
    });

    test("a paste that is only partly numeric", () => {
        expect(isAcceptable(input(""), pasted("12abc"))).toBe(false);
        expect(isAcceptable(input(""), pasted("10 %"))).toBe(false);
    });
});

describe("what it still allows", () => {
    test("the digits the tour asks for", () => {
        expect(isAcceptable(input(""), typed("1"))).toBe(true);
        expect(isAcceptable(input("1"), typed("0"))).toBe(true);
    });

    test("decimals, with either separator", () => {
        expect(isAcceptable(input("10"), typed(","))).toBe(true);
        expect(isAcceptable(input("10,"), typed("5"))).toBe(true);
        expect(isAcceptable(input("10"), typed("."))).toBe(true);
    });

    test("the boundary itself", () => {
        expect(isAcceptable(input("10"), typed("0"))).toBe(true);
        expect(isAcceptable(input(""), pasted("100"))).toBe(true);
    });

    test("deleting, including back to empty", () => {
        expect(isAcceptable(input("10"), { inputType: "deleteContentBackward" })).toBe(true);
        expect(isAcceptable(input("1"), { inputType: "deleteContentBackward" })).toBe(true);
        expect(isAcceptable(input("10"), { inputType: "deleteByCut" })).toBe(true);
    });

    test("replacing a selection, rather than appending to it", () => {
        // Appended to "10" this would read "1050" and be refused; over a
        // selected "10" it reads "50" and is fine. The selection is the whole
        // difference, and reading it is why nextValue() exists rather than a
        // naive value + data.
        expect(isAcceptable(input("10", { start: 0, end: 2 }), typed("50"))).toBe(true);
    });
});
