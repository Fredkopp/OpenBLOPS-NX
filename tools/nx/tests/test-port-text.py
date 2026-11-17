"""Check the port's UI strings and the Switch keyboard's text handling.

Every OPENBLOPS_ key the code names must exist in port_ui_translations.tsv,
SEH_GetPortString must never return null for one (callers format with it),
game text must convert to UTF-8 for the keyboard, and the keyboard's text
check must accept and refuse the right characters.
"""
from pathlib import Path
import argparse
import csv
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiler', default='C:/msys64/ucrt64/bin/g++.exe')
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
out = root / 'build-nx/port-text-tests'
out.mkdir(parents=True, exist_ok=True)

with (root / 'src/stringed/port_ui_translations.tsv').open(encoding='utf-8', newline='') as source:
    keys = {'OPENBLOPS_' + row['key'] for row in csv.DictReader(source, delimiter='\t')}

# Button prompt references: the menus show them through
# UI_NX_FormatControlPrompt, which swaps in the game's own label.
prompts = {'OPENBLOPS_ZOMBIE_REFRESH', 'OPENBLOPS_ZOMBIE_JOIN'}
shared = (root / 'src/ui/ui_shared.cpp').read_text(encoding='utf-8')
for prompt in prompts:
    assert '{"%s", ' % prompt in shared, f'{prompt} is no longer a button prompt'

missing = {}
for path in (root / 'src').rglob('*'):
    if path.suffix not in ('.cpp', '.h') or path.name == 'port_ui_translations.inc':
        continue
    for key in re.findall(r'"@?(OPENBLOPS_[A-Z0-9_]+)"', path.read_text(encoding='utf-8', errors='replace')):
        if key not in keys and key not in prompts:
            missing.setdefault(key, path.relative_to(root).as_posix())
assert not missing, f'keys missing from port_ui_translations.tsv: {missing}'


def function(path, signature):
    source = (root / path).read_text(encoding='utf-8')
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


code = r'''
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <string>
#define KISAK_NX
int portLanguage = 0;
const char *SEH_GetPortString(const char *reference, bool utf8 = false);
int SEH_PortLanguage() { return portLanguage; }
struct PortString { const char *reference; const char *game[10]; const char *utf8[10]; };
constexpr PortString portStrings[] = {
    {"OPENBLOPS_KEYBOARD_INVALID_CHAR", {}, {"Not allowed: %s", "Interdit : %s"}},
};
enum SwkbdTextCheckResult { SwkbdTextCheckResult_OK, SwkbdTextCheckResult_Bad };
char decimalDelimiter = ',';
char Com_GetDecimalDelimiter() { return decimalDelimiter; }
bool I_isforfilename(int c) { return isalnum(c) || c == '_' || c == '-'; }
bool I_isalnum(int c) { return isalnum(c); }
bool I_isdigit(int c) { return isdigit(c); }
'''
code += (root / 'src/ui/ui_keyboard.h').read_text(encoding='utf-8').split('#ifdef KISAK_NX', 1)[1].split('#endif', 1)[0]
code += function('src/stringed/stringed_hooks.cpp', 'const char *SEH_GetPortString(')
code += function('src/stringed/stringed_hooks.cpp', 'bool SEH_GameTextToUtf8(')
code += 'static UiNxTextFilter s_nxTextFilter;\n'
code += function('src/ui/ui_keyboard.cpp', 'static bool UI_NX_IsAllowedChar(')
code += function('src/ui/ui_keyboard.cpp', 'static SwkbdTextCheckResult UI_NX_CheckText(')
code += r'''
static std::string check(UiNxTextFilter filter, const char *input)
{
    s_nxTextFilter = filter;
    char text[128];
    snprintf(text, sizeof(text), "%s", input);
    return UI_NX_CheckText(text, sizeof(text)) == SwkbdTextCheckResult_OK ? "" : text;
}

static std::string utf8(const char *text, bool *exact = nullptr, size_t size = 64)
{
    char out[64];
    const bool converted = SEH_GameTextToUtf8(text, out, size);
    if (exact)
        *exact = converted;
    return out;
}

int main()
{
    assert(!strcmp(SEH_GetPortString("OPENBLOPS_KEYBOARD_INVALID_CHAR", true), "Not allowed: %s"));
    assert(!strcmp(SEH_GetPortString("OPENBLOPS_NOT_A_KEY"), "OPENBLOPS_NOT_A_KEY"));
    assert(!SEH_GetPortString("MENU_OK"));

    bool exact = false;
    assert(utf8("caf\xe9 \x80", &exact) == "caf\xc3\xa9 \xe2\x82\xac" && exact);
    assert(utf8("\x81", &exact) == "?" && !exact);
    assert(utf8(nullptr, &exact).empty() && exact);
    assert(utf8("abcdef", &exact, 4) == "abc" && !exact);
    portLanguage = 5;   // Russian text is Windows-1251; only ASCII converts
    assert(utf8("ok \xe0", &exact) == "ok ?" && !exact);
    portLanguage = 1;

    assert(check(UI_NX_TEXT_ANY, "Server ^1@home").empty());
    assert(check(UI_NX_TEXT_PLAIN, "Player One").empty());
    assert(check(UI_NX_TEXT_PLAIN, "a@b") == "Interdit : @");
    assert(check(UI_NX_TEXT_PLAIN, "^1red") == "Interdit : ^");
    assert(check(UI_NX_TEXT_ANY, "caf\xc3\xa9") == "Interdit : \xc3\xa9");
    assert(check(UI_NX_TEXT_ANY, "\xe2\x82\xac") == "Interdit : \xe2\x82\xac");
    assert(check(UI_NX_TEXT_DIGITS, "123").empty() && check(UI_NX_TEXT_DIGITS, "1a") == "Interdit : a");
    assert(check(UI_NX_TEXT_DECIMAL, "1.5").empty() && check(UI_NX_TEXT_DECIMAL, "1,5").empty());
    assert(check(UI_NX_TEXT_ALNUM, "ab 1") == "Interdit :  ");
    assert(check(UI_NX_TEXT_FILENAME, "my_save-1").empty() && check(UI_NX_TEXT_FILENAME, "a/b") == "Interdit : /");
    puts("port text tests passed");
}
'''
source = out / 'port-text.cpp'
binary = out / 'port-text.exe'
source.write_text(code, encoding='utf-8')
subprocess.run([args.compiler, '-std=c++20', '-Wall', '-Werror', '-O1', str(source), '-o', str(binary)], check=True)
subprocess.run([str(binary)], check=True)
