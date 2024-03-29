// SilentInstaller.cpp : Defines the entry point for the application.
//

#include "framework.h"
#include "SilentInstaller.h"
#include <Psapi.h>

#define MAX_LOADSTRING 100

// Global Variables:
HINSTANCE hInst;                                // current instance
WCHAR szTitle[MAX_LOADSTRING];                  // The title bar text
WCHAR szWindowClass[MAX_LOADSTRING];            // the main window class name

// Forward declarations of functions included in this code module:
ATOM                MyRegisterClass(HINSTANCE hInstance);
BOOL                InitInstance(HINSTANCE, int);
LRESULT CALLBACK    WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK    About(HWND, UINT, WPARAM, LPARAM);




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
        //printf("CreateProcess failed (%d).\n", GetLastError());
        return GetLastError();
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    if (!GetExitCodeProcess(pi.hProcess, &rc))
        rc = 0;

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    return rc;
}


int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

    TCHAR szBuffer[MAX_PATH] = _T("");

    TCHAR szImagePath[MAX_PATH] = { 0, };
    ZeroMemory(szImagePath, sizeof(szImagePath));
    GetProcessImageFileName(GetCurrentProcess(), szImagePath, (sizeof(szImagePath) / sizeof(TCHAR)));
    {
        
        TCHAR* filePart = _tcsrchr(szImagePath, '\\');
        if (filePart) // strip off the leading device\path information
            _tcscat_s(szBuffer, filePart + 1);
        if (0 == _tcscmp(TEXT("install.exe"), szBuffer))
        {
            RunSilentEx(TEXT("package.exe"), TEXT(""), TRUE);
        }
        if (0 == _tcscmp(TEXT("uninstall.exe"), szBuffer))
        {
            RunSilentEx(TEXT("package.exe"), TEXT(" _remove"), TRUE);
        }
    }

    return 0;

    // TODO: Place code here.

    // Initialize global strings
    LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
    LoadStringW(hInstance, IDC_SILENTINSTALLER, szWindowClass, MAX_LOADSTRING);
    MyRegisterClass(hInstance);

    // Perform application initialization:
    if (!InitInstance (hInstance, nCmdShow))
    {
        return FALSE;
    }

    HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_SILENTINSTALLER));

    MSG msg;

    // Main message loop:
    while (GetMessage(&msg, nullptr, 0, 0))
    {
        if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
        {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return (int) msg.wParam;
}



//
//  FUNCTION: MyRegisterClass()
//
//  PURPOSE: Registers the window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEXW wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style          = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra     = 0;
    wcex.cbWndExtra     = 0;
    wcex.hInstance      = hInstance;
    wcex.hIcon          = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_SILENTINSTALLER));
    wcex.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
    wcex.lpszMenuName   = MAKEINTRESOURCEW(IDC_SILENTINSTALLER);
    wcex.lpszClassName  = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassExW(&wcex);
}

//
//   FUNCTION: InitInstance(HINSTANCE, int)
//
//   PURPOSE: Saves instance handle and creates main window
//
//   COMMENTS:
//
//        In this function, we save the instance handle in a global variable and
//        create and display the main program window.
//
BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   hInst = hInstance; // Store instance handle in our global variable

   HWND hWnd = CreateWindowW(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW,
      CW_USEDEFAULT, 0, CW_USEDEFAULT, 0, nullptr, nullptr, hInstance, nullptr);

   if (!hWnd)
   {
      return FALSE;
   }

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

   return TRUE;
}

//
//  FUNCTION: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  PURPOSE: Processes messages for the main window.
//
//  WM_COMMAND  - process the application menu
//  WM_PAINT    - Paint the main window
//  WM_DESTROY  - post a quit message and return
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_COMMAND:
        {
            int wmId = LOWORD(wParam);
            // Parse the menu selections:
            switch (wmId)
            {
            case IDM_ABOUT:
                DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
                break;
            case IDM_EXIT:
                DestroyWindow(hWnd);
                break;
            default:
                return DefWindowProc(hWnd, message, wParam, lParam);
            }
        }
        break;
    case WM_PAINT:
        {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hWnd, &ps);
            // TODO: Add any drawing code that uses hdc here...
            EndPaint(hWnd, &ps);
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

// Message handler for about box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}
