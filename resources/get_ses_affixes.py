# Code adapted from <http://github.com/CoNLL-UD-2018/UDPipe-Future>.
#
# Copyright 2019 Institute of Formal and Applied Linguistics, Faculty of
# Mathematics and Physics, Charles University in Prague, Czech Republic.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import sys


def _min_edit_script(source, target, allow_copy):
    a = [[(len(source) + len(target) + 1, None)] * (len(target) + 1) for _ in range(len(source) + 1)]
    for i in range(0, len(source) + 1):
        for j in range(0, len(target) + 1):
            if i == 0 and j == 0:
                a[i][j] = (0, "")
            else:
                if allow_copy and i and j and source[i - 1] == target[j - 1] and a[i - 1][j - 1][0] < a[i][j][0]:
                    a[i][j] = (a[i - 1][j - 1][0], a[i - 1][j - 1][1] + "→")
                if i and a[i - 1][j][0] < a[i][j][0]:
                    a[i][j] = (a[i - 1][j][0] + 1, a[i - 1][j][1] + "-")
                if j and a[i][j - 1][0] < a[i][j][0]:
                    a[i][j] = (a[i][j - 1][0] + 1, a[i][j - 1][1] + "+" + target[j - 1])
    return a[-1][-1][1]


def _gen_lemma_rule(form, lemma, allow_copy):
    form = form.lower()

    previous_case = -1
    lemma_casing = ""
    for i, c in enumerate(lemma):
        case = "↑" if c.lower() != c else "↓"
        if case != previous_case:
            lemma_casing += "{}{}{}".format("¦" if lemma_casing else "", case,
                                            i if i <= len(lemma) // 2 else i - len(lemma))
        previous_case = case
    lemma = lemma.lower()

    best, best_form, best_lemma = 0, 0, 0
    for l in range(len(lemma)):
        for f in range(len(form)):
            cpl = 0
            while f + cpl < len(form) and l + cpl < len(lemma) and form[f + cpl] == lemma[l + cpl]: cpl += 1
            if cpl > best:
                best = cpl
                best_form = f
                best_lemma = l

    rule = lemma_casing + ";"
    if not best:
        rule += "a" + lemma
    else:
        rule += "d{}¦{}".format(
            _min_edit_script(form[:best_form], lemma[:best_lemma], allow_copy),
            _min_edit_script(form[best_form + best:], lemma[best_lemma + best:], allow_copy),
        )
    return rule


def get_ud_ses(file, allow_copy):
    input_lines = file.readlines()
    output_lines = []
    for line in input_lines:
        line_elems = line.split('\t')
        if len(line_elems) == 3:
            ses = _gen_lemma_rule(line_elems[0], line_elems[2], allow_copy)
            output_lines.append(line_elems[0] + '\t' + line_elems[1] + '\t' + ses)
        elif len(line_elems) == 1:
            output_lines.append("\n")
    return output_lines


def _apply_lemma_rule(form, lemma_rule):
    if ';' not in lemma_rule:
        raise ValueError('lemma_rule %r for form %r missing semicolon' % (lemma_rule, form))
    casing, rule = lemma_rule.split(";", 1)
    if rule.startswith("a"):
        lemma = rule[1:]
    else:
        form = form.lower()
        rules, rule_sources = rule[1:].split("¦"), []
        assert len(rules) == 2
        for rule in rules:
            source, i = 0, 0
            while i < len(rule):
                if rule[i] == "→" or rule[i] == "-":
                    source += 1
                else:
                    assert rule[i] == "+"
                    i += 1
                i += 1
            rule_sources.append(source)

        try:
            lemma, form_offset = "", 0
            for i in range(2):
                j, offset = 0, (0 if i == 0 else len(form) - rule_sources[1])
                while j < len(rules[i]):
                    if rules[i][j] == "→":
                        lemma += form[offset]
                        offset += 1
                    elif rules[i][j] == "-":
                        offset += 1
                    else:
                        assert (rules[i][j] == "+")
                        lemma += rules[i][j + 1]
                        j += 1
                    j += 1
                    # print(lemma)
                if i == 0:
                    lemma += form[rule_sources[0]: len(form) - rule_sources[1]]
        except:
            lemma = lemma

    for rule in casing.split("¦"):
        if rule == "↓0": continue  # The lemma is lowercased initially
        if not rule: continue  # Empty lemma might generate empty casing rule
        case, offset = rule[0], int(rule[1:])
        lemma = lemma[:offset] + (lemma[offset:].upper() if case == "↑" else lemma[offset:].lower())
    return lemma


def main():
    parser = argparse.ArgumentParser(description='Obtain short-edit-script (SES) encoding for lemmas.')
    parser.add_argument('-i', '--input', default=sys.stdin.fileno(),
                        help='The input corpus file (defaults to stdin)')
    parser.add_argument('-o', '--output', default=sys.stdout.fileno(),
                        help='The output corpus file (defaults to stdout)')
    parser.add_argument('--allow_copy', choices=['True', 'False'])
    parser.add_argument('--encoding', default='utf-8', help='The character encoding for input/output (it defaults to '
                                                            'UTF-8')
    args = parser.parse_args()

    with open(args.input, encoding=args.encoding) as f:
        output_lines = get_ud_ses(f, False)
    output_file = open(args.output, mode='w', encoding=args.encoding)
    output_file.writelines(output_lines)


if __name__ == '__main__':
    main()
