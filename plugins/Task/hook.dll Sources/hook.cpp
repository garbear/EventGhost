// hook.cpp : Defines the entry point for the DLL application.
//

#include "stdafx.h"
#include "hook.h"

#pragma data_seg(".shared")
static HWND g_egMessageHwnd = 0;
static HHOOK hookHandle = NULL;
static HINSTANCE hinstDLL; 
#pragma data_seg()
#pragma comment(linker, "/SECTION:.shared,RWS")


LRESULT CALLBACK CbtHook(int nCode, WPARAM wParam, LPARAM lParam) 
{
	if (nCode == HCBT_SETFOCUS)
	{
		PostMessage(g_egMessageHwnd, WM_APP+1, wParam, lParam);
	}
	//if (nCode == HCBT_CREATEWND)
	//{
	//	PostMessage(g_egMessageHwnd, WM_APP+2, wParam, lParam);
	//}
	//if (nCode == HCBT_SYSCOMMAND)
	//{
	//	if (wParam == SC_MONITORPOWER || 1)
	//	{
	//		PostMessage(g_egMessageHwnd, WM_APP+2, wParam, lParam);
	//		return 0;
	//	}
	//}
	return CallNextHookEx(hookHandle, nCode, wParam, lParam);
}


void StartHook()
{
	g_egMessageHwnd = FindWindow("HiddenMessageReceiver", "EventGhost Message Receiver");
	hookHandle = SetWindowsHookEx(WH_CBT, CbtHook, hinstDLL, 0);
}



void StopHook()
{
	UnhookWindowsHookEx(hookHandle);
	hookHandle = NULL;
}



BOOL APIENTRY DllMain( HINSTANCE hinst,
                       DWORD  ul_reason_for_call, 
                       LPVOID lpReserved
					 )
{
	switch (ul_reason_for_call)
	{
		case DLL_PROCESS_ATTACH:
			hinstDLL = hinst;
			DisableThreadLibraryCalls(hinst);
			break;
		case DLL_PROCESS_DETACH:
			break;
	}
    return TRUE;
}

