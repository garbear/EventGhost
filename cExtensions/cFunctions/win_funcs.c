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

#define UNICODE
#include "Python.h"
#define _WIN32_WINNT 0x501
#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#include <tlhelp32.h>

BOOL CALLBACK 
EnumAllWindowsProc(HWND hwnd, LPARAM lParam)
{
	PyObject *item;
	item = PyLong_FromVoidPtr(hwnd);
	PyList_Append((PyObject *) lParam, item);
	Py_DECREF(item); 
	return TRUE;
}


BOOL CALLBACK
EnumVisibleWindowsProc(HWND hwnd, LPARAM lParam)
{
	if (IsWindowVisible(hwnd))
	{	
		PyObject *item;

		item = PyLong_FromVoidPtr(hwnd);
		PyList_Append((PyObject *) lParam, item);
		Py_DECREF(item); 
	}
	return TRUE;
}


PyObject *
GetTopLevelWindowList(PyObject *self, PyObject *args)
{ 
	PyObject *pyWindowList;
	BOOL invisible=TRUE;

	if (!PyArg_ParseTuple(args, "|B", &invisible))
		return NULL;
	pyWindowList = PyList_New(0);
	if (invisible)
		EnumWindows((WNDENUMPROC) EnumAllWindowsProc, (LPARAM) pyWindowList);
	else
		EnumWindows((WNDENUMPROC) EnumVisibleWindowsProc, (LPARAM) pyWindowList);
	return Py_BuildValue("O", pyWindowList);
}


PyObject *
GetWindowChildsList(PyObject *self, PyObject *args)
{ 
	PyObject *pyWindowList;
	BOOL invisible=TRUE;
	HWND hWndParent;

	if (!PyArg_ParseTuple(args, "l|B", &hWndParent, &invisible))
		return NULL;
	pyWindowList = PyList_New(0);
	if (invisible)
		EnumChildWindows(
			hWndParent, 
			(WNDENUMPROC) EnumAllWindowsProc, 
			(LPARAM) pyWindowList);
	else
		EnumChildWindows(
			hWndParent, 
			(WNDENUMPROC) EnumVisibleWindowsProc, 
			(LPARAM) pyWindowList);
	return Py_BuildValue("O", pyWindowList);
}


PyObject *
PyWin_GetWindowText(PyObject *self, PyObject *args)
{
    HWND hwnd;
    int len;
	TCHAR buffer[512];

	if (!PyArg_ParseTuple(args, "l", &hwnd))
		return NULL;
    Py_BEGIN_ALLOW_THREADS
    len = GetWindowText(hwnd, buffer, sizeof(buffer)/sizeof(TCHAR));
    Py_END_ALLOW_THREADS
	return PyUnicode_FromWideChar(buffer, len);
}


PyObject *
PyWin_GetClassName(PyObject *self, PyObject *args)
{
    HWND hwnd;
    int len;
	TCHAR buffer[512];

	if (!PyArg_ParseTuple(args, "l", &hwnd))
		return NULL;
    Py_BEGIN_ALLOW_THREADS
	len = GetClassName(hwnd, buffer, 512);
    Py_END_ALLOW_THREADS
	return PyUnicode_FromWideChar(buffer, len);
}


PyObject *
GetProcessName(PyObject *self, PyObject *args)
{
	HANDLE hProcessSnap;
	PROCESSENTRY32 pe32;
	DWORD pid;

	if (!PyArg_ParseTuple(args, "k", &pid))
		return NULL;

	// Take a snapshot of all processes in the system.
	hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
	if(hProcessSnap == INVALID_HANDLE_VALUE)
	{
		PyErr_SetFromWindowsErrWithFilename(0, "CreateToolhelp32Snapshot");
		return NULL;
	}

	// Set the size of the structure before using it.
	pe32.dwSize = sizeof(PROCESSENTRY32);

	// Retrieve information about the first process,
	// and exit if unsuccessful
	if(!Process32First(hProcessSnap, &pe32))
	{
		CloseHandle(hProcessSnap);          // clean the snapshot object
		PyErr_SetFromWindowsErrWithFilename(0, "Process32First");
		return NULL;
	}

	// Now walk the snapshot of processes
	do
	{
		if(pe32.th32ProcessID == pid)
		{
			CloseHandle(hProcessSnap);
			return PyUnicode_FromWideChar(pe32.szExeFile, wcslen(pe32.szExeFile));
		}
	}while(Process32Next(hProcessSnap, &pe32));

	CloseHandle(hProcessSnap);
	return Py_BuildValue("s", "<not found>");
}
