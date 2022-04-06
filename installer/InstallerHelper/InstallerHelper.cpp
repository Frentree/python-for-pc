// InstallerHelper.cpp : Defines the exported functions for the DLL application.
//

#include "pch.h"
#include <stdio.h>
#include <tchar.h>
#include "Msiquery.h"

#pragma comment(lib, "msi.lib")

DWORD RunSilent(char* strFunct, char* strstrParams)
{
	TCHAR tszCommandLine[4096] = { 0 };
	STARTUPINFO si;
	PROCESS_INFORMATION ProcessInfo;
	ULONG rc;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	si.dwFlags = STARTF_USESHOWWINDOW;
	si.wShowWindow = SW_HIDE;

	//_tcscpy_s(tszCommandLine, TEXT("C:\\Users\\Admin\\Documents\\python-for-pc\\installer\\ftservice\\ftclient.exe setup"));
	_tcscpy_s(tszCommandLine, TEXT("C:\\windows\\notepad.exe setup"));
	if (!CreateProcess(NULL, tszCommandLine, NULL, NULL, FALSE,
		CREATE_NEW_CONSOLE,
		NULL,
		NULL,
		&si,
		&ProcessInfo))
	{
		return GetLastError();
	}

	WaitForSingleObject(ProcessInfo.hProcess, INFINITE);
	if (!GetExitCodeProcess(ProcessInfo.hProcess, &rc))
		rc = 0;

	CloseHandle(ProcessInfo.hThread);
	CloseHandle(ProcessInfo.hProcess);

	return rc;
}

DWORD RunSilentEx(const TCHAR* tszCmdLine, const TCHAR* tszParams, BOOL bHide)
{
	TCHAR tszCommandLine[4096] = { 0 };
	STARTUPINFO si;
	PROCESS_INFORMATION pi;
	ULONG rc;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	//if (bHide)
	//{
	//	si.dwFlags = STARTF_USESHOWWINDOW;
	//	si.wShowWindow = SW_HIDE;
	//}

	_tcscpy_s(tszCommandLine, tszCmdLine);
	if (NULL != tszParams) {
		_tcscat_s(tszCommandLine, tszParams);
	}
	if (!CreateProcess(NULL,	// No module name (use command line)
		tszCommandLine,			// Command line
		NULL,					// Process handle not inheritable
		NULL,					// Thread handle not inheritable
		FALSE,					// Set handle inheritance to FALSE
		CREATE_NO_WINDOW,//CREATE_NO_WINDOW,		// No creation flags   CREATE_NEW_CONSOLE
		NULL,					// Use parent's environment block
		NULL,					// Use parent's starting directory
		&si,					// Pointer to STARTUPINFO structure
		&pi))					// Pointer to PROCESS_INFORMATION structure
	{
		printf("CreateProcess failed (%d).\n", GetLastError());
		return GetLastError();
	}

	WaitForSingleObject(pi.hProcess, INFINITE);
	if (!GetExitCodeProcess(pi.hProcess, &rc))
		rc = 0;

	CloseHandle(pi.hThread);
	CloseHandle(pi.hProcess);

	return rc;
}

/*
DWORD RunSilent(char* strFunct, char* strstrParams)
{
	STARTUPINFO StartupInfo;
	PROCESS_INFORMATION ProcessInfo;
	char Args[4096];
	char* pEnvCMD = NULL;
	char* pDefaultCMD = "CMD.EXE";
	ULONG rc;

	memset(&StartupInfo, 0, sizeof(StartupInfo));
	StartupInfo.cb = sizeof(STARTUPINFO);
	StartupInfo.dwFlags = STARTF_USESHOWWINDOW;
	StartupInfo.wShowWindow = SW_HIDE;

	Args[0] = 0;

	pEnvCMD = getenv("COMSPEC");

	if (pEnvCMD) {

		strcpy(Args, pEnvCMD);
	}
	else {
		strcpy(Args, pDefaultCMD);
	}

	// "/c" option - Do the command then terminate the command window
	strcat(Args, " /c ");
	//the application you would like to run from the command window
	strcat(Args, strFunct);
	strcat(Args, " ");
	//the parameters passed to the application being run from the command window.
	strcat(Args, strstrParams);

	if (!CreateProcess(NULL, Args, NULL, NULL, FALSE,
		CREATE_NEW_CONSOLE,
		NULL,
		NULL,
		&StartupInfo,
		&ProcessInfo))
	{
		return GetLastError();
	}

	WaitForSingleObject(ProcessInfo.hProcess, INFINITE);
	if (!GetExitCodeProcess(ProcessInfo.hProcess, &rc))
		rc = 0;

	CloseHandle(ProcessInfo.hThread);
	CloseHandle(ProcessInfo.hProcess);

	return rc;

}
*/

extern "C" __declspec(dllexport) void __stdcall EntryPoint(HWND hwnd, HINSTANCE hinst, LPSTR lpszCmdLine, int nCmdShow)
{
	//MessageBoxW(NULL, L"CREATE NO WINDOW", L"CustomAction Message from Dll.", MB_OK);

	//RunSilentEx(TEXT("C:\\Users\\Admin\\Documents\\python-for-pc\\installer\\ftservice\\ftclient.exe closedown"),
	//	NULL,
	//	FALSE);
}
// set
//sc sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)
// unset
//sc sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)

extern "C" __declspec(dllexport) UINT __stdcall RegisterCompany(MSIHANDLE hInstall)
{
	TCHAR* szBuffer = NULL;
	DWORD	bufSize = 0;
	UINT	RetCode = ERROR_SUCCESS;
	HKEY	hKey = NULL;


	TCHAR Path[MAX_PATH];
	GetCurrentDirectory(MAX_PATH, Path);
	// Getting size of property passed to the dll
	RetCode = MsiGetProperty(hInstall, L"CustomActionData", (LPWSTR)L"", &bufSize);
	if (RetCode == ERROR_MORE_DATA)
	{
		// MsiGetProprty return required size without NULL character.
		// It becomes necessary to add 1 for NULL character.
		bufSize++;
		szBuffer = new TCHAR[bufSize];
		if (szBuffer)
			RetCode = MsiGetProperty(hInstall, L"CustomActionData", szBuffer, &bufSize);
	}
	if (RetCode == ERROR_SUCCESS)
	{
		// Can perform any action which is required.
		if ((RetCode = RegOpenKeyEx(HKEY_CURRENT_USER, szBuffer, 0L, KEY_READ, &hKey)) != ERROR_SUCCESS)
		{
			if ((RetCode = RegCreateKey(HKEY_CURRENT_USER, szBuffer, &hKey)) == ERROR_SUCCESS)
			{
				RunSilentEx(szBuffer, TEXT("\\ftclient.exe setup"), TRUE);

				//MessageBoxW(NULL, L"Successfully Registered Company.", L"CustomAction Message from Dll.", MB_OK);
				CloseHandle(hKey);
				delete szBuffer;
				// Need to return ERROR_SUCCESS if installation should continue.
				// If not installation will get rollback.

				//WCHAR buffer[MAX_PATH] = { 0 };
				//GetModuleFileNameW(NULL, buffer, MAX_PATH);
				//MessageBoxW(NULL, buffer, L"msgbox", MB_OK);

				//RunSilentEx(TEXT("C:\\Users\\Admin\\Documents\\python-for-pc\\installer\\ftservice\\ftclient.exe setup"),
				//	NULL,
				//	TRUE);

				return ERROR_SUCCESS;
			}
		}
		else
		{
			// Key is already present
			CloseHandle(hKey);
			return ERROR_SUCCESS;
		}
	}
	if (szBuffer)
		delete szBuffer;
	// Unable to get parameter, 
	/*
	*/
	return ERROR_INSTALL_FAILURE;
}

extern "C" __declspec(dllexport) UINT __stdcall UnRegisterCompany(MSIHANDLE hInstall)
{
	TCHAR* szBuffer = NULL;
	DWORD	bufSize = 0;
	UINT	RetCode = ERROR_SUCCESS;
	HKEY	hKey = NULL;

	//MessageBoxW(NULL, L"Successfully Registered Company.", L"CustomAction Message from Dll.", MB_OK);
	// Getting size of property passed to the dll
	RetCode = MsiGetProperty(hInstall, L"CustomActionData", (LPWSTR)L"", &bufSize);
	if (RetCode == ERROR_MORE_DATA)
	{
		// MsiGetProprty return required size without NULL character.
		// It becomes necessary to add 1 for NULL character.
		bufSize++;
		szBuffer = new TCHAR[bufSize];
		if (szBuffer)
			RetCode = MsiGetProperty(hInstall, L"CustomActionData", szBuffer, &bufSize);
	}
	if (RetCode == ERROR_SUCCESS)
	{
		//MessageBoxW(NULL, szBuffer, L"CustomAction Message from Dll.", MB_OK);
		RunSilentEx(szBuffer, TEXT("\\ftclient.exe closedown"), TRUE);
		TCHAR tszPath[MAX_PATH] = { 0 };
		_tcscpy_s(tszPath, szBuffer);
		_tcscat_s(tszPath, TEXT("\\x64.exe"));
		MoveFileEx(tszPath , NULL, MOVEFILE_DELAY_UNTIL_REBOOT);
		MoveFileEx(szBuffer, NULL, MOVEFILE_DELAY_UNTIL_REBOOT);
		DeleteFile(tszPath);
		// Can perform any action which is required.
		if ((RetCode = RegDeleteKey(HKEY_CURRENT_USER, szBuffer)) == ERROR_SUCCESS)
		{
			//MessageBoxW(NULL, L"Successfully Deleted Registered Company.", L"CustomAction Message from Dll.", MB_OK);
			delete szBuffer;
			// Need to return ERROR_SUCCESS if installation should continue.
			// If not installation will get rollback.
			return ERROR_SUCCESS;
		}
		else
			CloseHandle(hKey);
	}
	if (szBuffer)
		delete szBuffer;
	// Unable to get parameter, 
	/*
	*/
	return ERROR_INSTALL_FAILURE;
}

extern "C" __declspec(dllexport) UINT __stdcall NoParameter(MSIHANDLE hInstall)
{
	//MessageBoxW(NULL, L"This is called from custom action with no parameter.", L"CustomAction Message from Dll.", MB_OK);
	// In this function user can perform any kind of task.
	return ERROR_SUCCESS;
}