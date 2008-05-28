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
#include <windows.h>
#include <stdio.h>
#include <tchar.h>

#define MAX_KEY_LENGTH 255
#define MAX_VALUE_NAME 16383
 
PyObject *
RegEnumKeysAndValues(PyObject *self, PyObject *args)
{ 
    HKEY hKey;
	
	PyObject *pyKeyNameList;
	PyObject *pyValueNameList;
    PyObject *pyTemp;

	TCHAR    achKey[MAX_KEY_LENGTH];   // buffer for subkey name
    DWORD    cbName;                   // size of name string 
    TCHAR    achClass[MAX_PATH] = TEXT("");  // buffer for class name 
    DWORD    cchClassName = MAX_PATH;  // size of class string 
    DWORD    cSubKeys=0;               // number of subkeys 
    DWORD    cbMaxSubKey;              // longest subkey size 
    DWORD    cchMaxClass;              // longest class string 
    DWORD    cValues;              // number of values for key 
    DWORD    cchMaxValue;          // longest value name 
    DWORD    cbMaxValueData;       // longest value data 
	DWORD	 cType;
	DWORD	 cSubSubValues, cSubSubKeys;
	HKEY	 hSubKey;

    DWORD i, retCode; 
 
    TCHAR  achValue[MAX_VALUE_NAME]; 
    DWORD cchValue = MAX_VALUE_NAME; 
 
	if (!PyArg_ParseTuple(args, "k", &hKey))
        return NULL;

    // Get the class name and the value count. 
    retCode = RegQueryInfoKey(
        hKey,                    // key handle 
        achClass,                // buffer for class name 
        &cchClassName,           // size of class string 
        NULL,                    // reserved 
        &cSubKeys,               // number of subkeys 
        &cbMaxSubKey,            // longest subkey size 
        &cchMaxClass,            // longest class string 
        &cValues,                // number of values for this key 
        &cchMaxValue,            // longest value name 
        &cbMaxValueData,         // longest value data 
        NULL,					 // security descriptor 
        NULL);					 // last write time 
 
    // Enumerate the subkeys, until RegEnumKeyEx fails.
    
	pyKeyNameList = PyList_New(cSubKeys);

    if (cSubKeys)
    {
        for (i=0; i<cSubKeys; i++) 
        { 
            cbName = MAX_KEY_LENGTH;
            retCode = RegEnumKeyEx(
				hKey, 
				i,
                achKey, 
                &cbName, 
                NULL, 
                NULL, 
                NULL, 
                NULL); 
            if (retCode == ERROR_SUCCESS) 
            {
				retCode = RegOpenKeyEx(hKey, achKey, 0, KEY_READ, &hSubKey);
				retCode = RegQueryInfoKey(
					hSubKey,        // key handle 
					NULL,           // buffer for class name 
					NULL,           // size of class string 
					NULL,           // reserved 
					&cSubSubKeys,   // number of subkeys 
					NULL,           // longest subkey size 
					NULL,           // longest class string 
					&cSubSubValues, // number of values for this key 
					NULL,           // longest value name 
					NULL,           // longest value data 
					NULL,           // security descriptor 
					NULL);          // last write time 
				RegCloseKey(hSubKey);
				pyTemp = Py_BuildValue("(sll)", achKey, cSubSubKeys, cSubSubValues);
				PyList_SET_ITEM(pyKeyNameList, i, pyTemp);
            }
        }
    } 
 
    // Enumerate the key values. 

	pyValueNameList = PyList_New(cValues);

	if (cValues) 
    {
        for (i=0, retCode=ERROR_SUCCESS; i<cValues; i++) 
        { 
            cchValue = MAX_VALUE_NAME; 
            achValue[0] = '\0'; 
            retCode = RegEnumValue(
				hKey, 
				i, 
                achValue, 
                &cchValue, 
                NULL, 
                &cType,
                NULL,
                NULL);
 
            if (retCode == ERROR_SUCCESS ) 
            { 
				pyTemp = Py_BuildValue("(si)", achValue, cType);
				PyList_SET_ITEM(pyValueNameList, i, pyTemp);
            } 
        }
    }
	return Py_BuildValue("(OO)", pyKeyNameList, pyValueNameList);
}




