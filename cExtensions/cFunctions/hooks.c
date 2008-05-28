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
#include "keyhook.h"
#include "mousehook.h"

volatile DWORD gLastTickCount;
volatile BOOL gIsInIdle = FALSE;
DWORD gWaitThreadId = 0;
DWORD gHookThreadId = 0;
HANDLE gHookThreadHandle;
HANDLE gWaitThreadHandle;
HANDLE waitEvent;
DWORD gIdleTimeout = 60000;

PyObject* gPyIdleCallback;
PyObject* gPyUnIdleCallback;


static DWORD WINAPI 
HookThreadProc(HANDLE startupEvent)
{
    MSG msg;
    BOOL bRet; 
	HINSTANCE hMod;

	CoInitialize(NULL);
	if(0==SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL))
		ErrorExit("SetThreadPriority");;
	hMod = LoadLibrary("cFunctions.pyd");
	SetKeyboardHook(hMod);
	SetMouseHook(hMod);
    PeekMessage(&msg, NULL, WM_USER, WM_USER, PM_NOREMOVE);
	SetEvent(startupEvent);
	DEBUG("HookThread started");
	while( (bRet = GetMessage( &msg, NULL, 0, 0 )) != 0)
    { 
        if (bRet == -1)
        {
            print("error\n");
			// handle the error and possibly exit
        }
        else
        {
            //print("msg");
			if(msg.message == WM_USER + 1)
			{
				print("HookThread WM_USER\n");
				//break;
			}
			TranslateMessage(&msg); 
            DispatchMessage(&msg); 
			//print("DispatchMessage\n");
        }
    } 
	UnsetKeyboardHook();
	UnsetMouseHook();
	CoUninitialize();
	DEBUG("HookThread stopped");
	return(0);
}


static DWORD WINAPI 
WaitThreadProc(HANDLE startupEvent)
{
	DWORD res;
	PyGILState_STATE gil;
	HANDLE pHandles[] = { waitEvent }; 
	MSG msg;

	CoInitialize(NULL);
	gLastTickCount = GetTickCount();

	if(0==SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL))
		ErrorExit("WaitThread SetThreadPriority");
				
	PeekMessage(&msg, NULL, WM_USER, WM_USER, PM_NOREMOVE);
	SetEvent(startupEvent);
	DEBUG("WaitThread started");
	while(1)
	{
		while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) 
		{
			//DispatchMessage(&msg);
            if(msg.message == WM_USER+1)
			{
				DEBUG("WM_USER+1");
				if(gIsInIdle)
				{
					gil = PyGILState_Ensure();
					PyObject_CallObject(gPyUnIdleCallback, NULL);
					PyGILState_Release(gil);
					gIsInIdle = FALSE;
				}
				continue;
			}
			else if(msg.message == WM_QUIT)
				goto out;
			else
			{
				print("got WaitThread mesg");
				TranslateMessage(&msg);
				DispatchMessage(&msg); 
			}
		}
		
		res = MsgWaitForMultipleObjects(
			1, 
			pHandles, 
			FALSE, 
			gIdleTimeout - (GetTickCount() - gLastTickCount),
			QS_ALLEVENTS);

		switch (res)
		{
			case WAIT_OBJECT_0: 
				//print("WAIT_OBJECT_0");
				continue;
			case WAIT_OBJECT_0+1: 
				//print("WAIT_OBJECT_0+1");
				continue;
			case WAIT_TIMEOUT: 
				if(!gIsInIdle && ((GetTickCount() - gLastTickCount) >= gIdleTimeout))
				{
					gil = PyGILState_Ensure();
					PyObject_CallObject(gPyIdleCallback, NULL);
					PyGILState_Release(gil);
					gIsInIdle = TRUE;
				}
				continue;
			default:
				print("unknow result\n");
				continue;
		}
		//res = WaitForSingleObject(waitEvent, INFINITE);

	}
out:
	DEBUG("WaitThread stopped");
	CoUninitialize();
	return(0);
}


void 
AwakeWaitThread(void)
{
	gLastTickCount = GetTickCount();
	if (gIsInIdle)
		PostThreadMessage(gWaitThreadId, WM_USER+1, 0, 0);
}


PyObject *
SetIdleTime(PyObject *self, PyObject *args)
{

	if (!PyArg_ParseTuple(args, "l", &gIdleTimeout))
        return NULL;
	if(PostThreadMessage(gWaitThreadId, WM_USER+1, 0, 0) == 0)
		RAISE_SYSTEMERR("SetIdleTime:PostThreadMessage");
	Py_RETURN_NONE;
}


PyObject *
ResetIdleTimer(PyObject *self, PyObject *args)
{
	if(PostThreadMessage(gWaitThreadId, WM_USER+1, 0, 0) == 0)
		RAISE_SYSTEMERR("ResetIdleTimer:PostThreadMessage");
	Py_RETURN_NONE;
}


PyObject *
StartHooks(PyObject *self, PyObject *args)
// def StartHooks(idleCallback, unidleCallback) => None
{
	HANDLE startupEvent;

	if (!PyArg_ParseTuple(args, "OO", &gPyIdleCallback, &gPyUnIdleCallback))
	{
		PyErr_Print();
		return NULL;
	}
	Py_INCREF(gPyIdleCallback);
	Py_INCREF(gPyUnIdleCallback);
	PyEval_InitThreads();

	DEBUG("RegisterKeyhook");
	waitEvent = CreateEvent(NULL, FALSE, FALSE, NULL);
	startupEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
	gWaitThreadHandle = CreateThread(
		NULL,			// default security
		0,				// default stack size
		WaitThreadProc, // name of the thread function
		startupEvent,   // the thread parameters
		0,				// default startup flags
		&gWaitThreadId);
	switch(WaitForSingleObject(startupEvent, 3000))
	{
		case WAIT_TIMEOUT:
			RAISE_SYSTEMERR("WAIT_TIMEOUT for WaitThread");
		case WAIT_OBJECT_0:
			break;
	}
	ResetEvent(startupEvent);
	if(PostThreadMessage(gWaitThreadId, WM_USER+1, 0, 0) == 0)
		RAISE_SYSTEMERR("PostThreadMessage WaitThread");

	gHookThreadHandle = CreateThread(
		NULL,			// default security
		0,				// default stack size
		HookThreadProc, // name of the thread function
		startupEvent,	// the thread parameters
		0,				// default startup flags
		&gHookThreadId);
	switch(WaitForSingleObject(startupEvent, 3000))
	{
		case WAIT_TIMEOUT:
			RAISE_SYSTEMERR("WAIT_TIMEOUT for HookThread");
		case WAIT_OBJECT_0:
			break;
	}
	CloseHandle(startupEvent);

	Py_RETURN_NONE;
}


PyObject *
StopHooks(PyObject *self, PyObject *args)
// def StopHooks() => None
{
	//DEBUG("StopHooks");

	if (gHookThreadId != 0)
	{
		if(PostThreadMessage(gHookThreadId, WM_QUIT, 0, 0) == 0)
			RAISE_SYSTEMERR("PostThreadMessage HookThread");
		if(WaitForSingleObject(gHookThreadHandle, 3000) != WAIT_OBJECT_0)
			RAISE_SYSTEMERR("WaitForSingleObject HookThread");
		gHookThreadId = 0;
	}

	if (gWaitThreadId != 0)
	{
		if(PostThreadMessage(gWaitThreadId, WM_QUIT, 0, 0) == 0)
			RAISE_SYSTEMERR("PostThreadMessage WaitThread");
		if(WaitForSingleObject(gWaitThreadHandle, 3000) != WAIT_OBJECT_0)
			RAISE_SYSTEMERR("WaitForSingleObject WaitThread");
		gWaitThreadId = 0;
	}
	Py_RETURN_NONE;
}



