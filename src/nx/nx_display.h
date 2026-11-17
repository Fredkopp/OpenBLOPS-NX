#pragma once
// The default window's size and present rate (nx_display.cpp).

void NX_DisplayInit();
// The size the renderer draws at (R_SetWndParms).
void NX_DisplayRenderSize(int *width, int *height);
// The display's refresh rate in Hz: 60, or 120 on Switch 2 when chosen.
int NX_DisplayRefreshRate();
// Once a frame on the main thread: follows docking, the TV's resolution and
// the Screen Refresh Rate setting.
void NX_DisplayUpdate();
