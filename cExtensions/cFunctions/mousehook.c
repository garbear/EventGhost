/*
// This file is part of the EventGhost project.
//
// Copyright (C) 2005-2008 Lars-Peter Voss <bitmonster@eventghost.org>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
*/

#include "Python.h"
#define _WIN32_WINNT 0x501
#include <windows.h>
#include "utils.h"
#include "hooks.h"

PyObject* gPyMouseCallback = NULL;
HHOOK gOldMouseHook = NULL;


static BOOL
CallPyMouseCallback(char *msgString, int buttonNum, int param)
{
	BOOL result = FALSE;
	PyObject *pyArgs;
	PyObject *pyRes;
	PyGILState_STATE gil;

	gil = PyGILState_Ensure();
	pyArgs = Py_BuildValue("(sii)", msgString, buttonNum, param);
	pyRes = PyObject_CallObject(gPyMouseCallback, pyArgs);
	if(pyRes == NULL)
	{
		PyErr_Print();
	}else{
		result = (Py_True == pyRes);
		Py_XDECREF(pyRes);
	}
	Py_DECREF(pyArgs);
	PyGILState_Release(gil);
	return result;
}


static LRESULT CALLBACK 
MouseHookProc(int nCode, WPARAM wParam, LPARAM lParam) 
{
	PMSLLHOOKSTRUCT mhs;
	static BOOL mouseState[5] = {FALSE, FALSE, FALSE, FALSE, FALSE};
	char *mesg = NULL;
	int buttonNum = 0;
	int param = 0;
	
	AwakeWaitThread();
	if (nCode != HC_ACTION)
	{	
		goto out_nextHook;
	}
	mhs = (PMSLLHOOKSTRUCT) lParam;
	switch(wParam)
	{
		//case WM_LBUTTONDOWN:
		//	DEBUG("WM_LBUTTONDOWN");
		//	mouseState[0] = TRUE;
		//	mesg = "LeftButton";
		//	buttonNum = 0;
		//	param = 1;
		//	goto out_callCallback;
		//case WM_LBUTTONUP:
		//	DEBUG("WM_LBUTTONUP");
		//	mouseState[0] = FALSE;
		//	mesg = "LeftButton";
		//	buttonNum = 0;
		//	param = 0;
		//	goto out_callCallback;
		//case WM_MOUSEMOVE:
		//	DEBUG("WM_MOUSEMOVE");
		//	break;
		//case WM_MOUSEWHEEL:
		//	DEBUG("WM_MOUSEWHEEL");
		//	break;
		case WM_MBUTTONDOWN:
			DEBUG("WM_MBUTTONDOWN");
			mouseState[1] = TRUE;
			mesg = "MiddleButton";
			buttonNum = 1;
			param = 1;
			goto out_callCallback;
		case WM_MBUTTONUP:
			DEBUG("WM_MBUTTONUP");
			mouseState[1] = FALSE;
			mesg = "MiddleButton";
			buttonNum = 1;
			param = 0;
			goto out_callCallback;
		//case WM_RBUTTONDOWN:
		//	DEBUG("WM_RBUTTONDOWN");
		//	mouseState[2] = TRUE;
		//	mesg = "RightButton";
		//	buttonNum = 2;
		//	param = 1;
		//	goto out_callCallback;
		//case WM_RBUTTONUP:
		//	DEBUG("WM_RBUTTONUP");
		//	mouseState[2] = FALSE;
		//	mesg = "RightButton";
		//	buttonNum = 2;
		//	param = 0;
		//	goto out_callCallback;
		case WM_XBUTTONDOWN:
			DEBUG("WM_XBUTTONDOWN");
			if (HIWORD(mhs->mouseData) == XBUTTON1)
			{
				mouseState[3] = TRUE;
				mesg = "XButton1";
				buttonNum = 3;
			}else{
				mouseState[4] = TRUE;
				mesg = "XButton2";
				buttonNum = 4;
			}
			param = 1;
			goto out_callCallback;
		case WM_XBUTTONUP:
			DEBUG("WM_XBUTTONUP");
			if (HIWORD(mhs->mouseData) == XBUTTON1)
			{
				mouseState[3] = FALSE;
				mesg = "XButton1";
				buttonNum = 3;
			}else{
				mouseState[4] = FALSE;
				mesg = "XButton2";
				buttonNum = 4;
			}
			param = 0;
			goto out_callCallback;
		//case WM_XBUTTONDBLCLK:
		//	DEBUG("WM_XBUTTONDBLCLK");
		//	break;
		//default:
		//	DEBUG("unknown mouse message");
	}
	goto out_nextHook;

out_callCallback:
	if (gPyMouseCallback)
	{
		if (!CallPyMouseCallback(mesg, buttonNum, param))
		{
			// return a nonzero value to prevent the system from passing the 
			// message to the rest of the hook chain or the target window 
			// procedure
			return 42; 
		}
	}
out_nextHook:
	return CallNextHookEx(gOldMouseHook, nCode, wParam, lParam);
}


PyObject *
SetMouseCallback(PyObject *self, PyObject *args)
{
	PyObject* callback;

	if (!PyArg_ParseTuple(args, "O", &callback))
	{
		PyErr_Print();
		return NULL;
	}
	Py_XDECREF(gPyMouseCallback);
	if (callback == Py_None)
	{
		callback = NULL;
	}
	Py_XINCREF(callback);
	gPyMouseCallback = callback;
	Py_RETURN_NONE;
}


void SetMouseHook(HINSTANCE hMod)
{
	gOldMouseHook = SetWindowsHookEx(
		WH_MOUSE_LL,	// hook low-level mouse input events
		MouseHookProc,	// pointer to the hook procedure
		hMod,			// handle to the DLL containing the hook procedure
		0				// associated with all existing threads running in 
	);					// the same desktop as the calling thread
}


void UnsetMouseHook(void)
{
	UnhookWindowsHookEx(gOldMouseHook);
}