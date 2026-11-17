#pragma once

struct keyBoardUtitlity // sizeof=0x8
{                                       // XREF: .data:keyBoardUtitlity uiKeyboard/r
    bool keyboardActive;                // XREF: UI_SetActiveKeyboardType(int):loc_7443D0/r
                                        // UI_SetActiveKeyboardType(int)+75/w ...
    // padding byte
    // padding byte
    // padding byte
    int keyboardType;                   // XREF: UI_GetActiveKeyboardType(void)+3/r
};

#ifdef KISAK_NX
#include <stddef.h>

// Which ASCII characters the Switch keyboard accepts. All but UI_NX_TEXT_ANY
// refuse '@' (a string reference) and '^' (a colour code); UI_NX_TEXT_SAFE
// also refuses what UI_VerifyString does ({ } % \ ; ").
enum UiNxTextFilter
{
    UI_NX_TEXT_ANY,
    UI_NX_TEXT_PLAIN,
    UI_NX_TEXT_SAFE,
    UI_NX_TEXT_FILENAME,
    UI_NX_TEXT_ALNUM,
    UI_NX_TEXT_DIGITS,
    UI_NX_TEXT_DECIMAL,   // digits and one decimal mark, returned as '.'
};

struct UiNxTextRequest
{
    const char *header = nullptr;    // localized text in the game's encoding
    bool headerIsUtf8 = false;
    const char *initialText = "";    // in the game's encoding
    int maxChars = 255;              // in bytes of game text
    bool password = false;
    UiNxTextFilter filter = UI_NX_TEXT_ANY;
    // Also accept the letters of the game's language (é, ß, Cyrillic, Hangul,
    // kana...) with UI_NX_TEXT_ANY, _PLAIN or _SAFE. Leave it off for text
    // other players see: their game may read the bytes in another encoding.
    bool nativeText = false;
};

// Shows the Switch software keyboard. A refused character is reported inside
// the keyboard, which stays open. Returns false when the player cancels.
bool UI_NX_EditText(const UiNxTextRequest &request, char *out, size_t outSize);
#endif

int __cdecl UI_GetActiveKeyboardType();
void __cdecl UI_SetActiveKeyboardType(int keyboardType);
void __cdecl UI_ClearKeyboardActive();
void __cdecl UI_Keyboard_New_f();
void __cdecl UI_KeyboardComplete(int localClientNum);
void __cdecl UI_Keyboard_Complete_f();
void __cdecl UI_Clear_Keyboard_Active_f();
