#include <ntddk.h>
#include <wdf.h>


#pragma region offset
//#include <ntifs.h>
/*
typedef NTSTATUS(*NtQueryInformationProcess_t)(
	_In_	HANDLE				ProcessHandle,
	_In_	PROCESSINFOCLASS	ProcessInformationClass,
	_Out_	PVOID				ProcessInformation,
	_In_	ULONG				ProcessInformationLength,
	_Out_	PULONG				ReturnLength
	);
*/
#if (NTDDI_VERSION >= NTDDI_WIN2K)
NTKERNELAPI
NTSTATUS
ObOpenObjectByPointer(
	_In_ PVOID Object,
	_In_ ULONG HandleAttributes,
	_In_opt_ PACCESS_STATE PassedAccessState,
	_In_ ACCESS_MASK DesiredAccess,
	_In_opt_ POBJECT_TYPE ObjectType,
	_In_ KPROCESSOR_MODE AccessMode,
	_Out_ PHANDLE Handle
);
#endif

typedef __kernel_entry NTSTATUS (*NtQueryInformationProcess_t)(
	_In_            HANDLE           ProcessHandle,
	_In_            PROCESSINFOCLASS ProcessInformationClass,
	_Out_           PVOID            ProcessInformation,
	_In_            ULONG            ProcessInformationLength,
	_Out_			PULONG           ReturnLength
);

typedef struct _IMPORT_OFFSET
{
	int UniqueProcessid_off;
	int ActiveProcessLinks_off;
	int ImageFileName_off;
	int PEF_off;
} IMPORT_OFFSET;

IMPORT_OFFSET iOffset;
const char szSystem[] = "System";
const wchar_t szNtQueryInformationProcess[] = L"NtQueryInformationProcess";
#pragma endregion

#define USE_DEVICE_ADD

DRIVER_INITIALIZE DriverEntry;
VOID DriverUnload(IN PDRIVER_OBJECT pDriverObject);

typedef DRIVER_UNLOAD *PDRIVER_UNLOAD;
PVOID g_hRegistration = NULL;

#ifdef USE_DEVICE_ADD
// NOTE : creating driver is unnecessary for developping.
EVT_WDF_DRIVER_DEVICE_ADD KmdfHelloWorldEvtDeviceAdd;
#endif

#define PROCESS_TERMINATE       0x0001	// TerminateProcess
#define PROCESS_VM_OPERATION    0x0008	// VirtualProtect, WriteProcessMemory
#define PROCESS_VM_READ         0x0010	// ReadProcessMemory
#define PROCESS_VM_WRITE        0x0020	// WriteProcessMemory

void ProtectNotepad(POB_PRE_OPERATION_INFORMATION pOperationInformation)
{
	char szProcName[16] = { 0, };
	strcpy_s(szProcName, (rsize_t)16, (const char* )((DWORD64)pOperationInformation->Object + iOffset.ImageFileName_off));
	if (!_strnicmp(szProcName, "notepad.exe", 16))
	{
		if ((pOperationInformation->Operation == OB_OPERATION_HANDLE_CREATE))
		{
			if ((pOperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_TERMINATE) == PROCESS_TERMINATE)
				pOperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_TERMINATE;
			if ((pOperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_VM_READ) == PROCESS_VM_READ)
				pOperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_VM_READ;
			if ((pOperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_VM_OPERATION) == PROCESS_VM_OPERATION)
				pOperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_VM_OPERATION;
			if ((pOperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_VM_WRITE) == PROCESS_VM_WRITE)
				pOperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_VM_WRITE;
		}
	}
}
OB_PREOP_CALLBACK_STATUS ObjectPreCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_PRE_OPERATION_INFORMATION OperationInformation)
{
	UNREFERENCED_PARAMETER(RegistrationContext);
	UNREFERENCED_PARAMETER(OperationInformation);

	ProtectNotepad(OperationInformation);
	DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] ObjectPreCallback called");
	/*
	PREGCONTEXT RegContext = (PREGCONTEXT)RegistrationContext;

	ULONG CurrentPid = (ULONG)PsGetProcessId((PERPROCESS)(OperationInformation->Object));

	if (Regcontext->ulProtectPid == CurrentPid && RegContext->ulMyPid != (ULONG)PsGetCurrentProcessId())
	{
		if (OperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_TERMINATE)
		{
			OperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_TERMINATE;
		}
	}
	*/
	return OB_PREOP_SUCCESS;
}
BOOLEAN GetPebOffset()
{
	int LinkOffset = iOffset.ActiveProcessLinks_off;
	//int ProcName = iOffset.ImageFileName_off;
	BOOLEAN success = FALSE;
	PEPROCESS Process = PsGetCurrentProcess();
	UNICODE_STRING routineName = { 0, };
	
	RtlInitUnicodeString(&routineName, szNtQueryInformationProcess);
	NtQueryInformationProcess_t NtQueryInformationProcess = (NtQueryInformationProcess_t)MmGetSystemRoutineAddress(&routineName);

	for (int i = 0; i < 0x10; i++)
	{
		PROCESS_BASIC_INFORMATION ProcessInformation = { 0, };
		PLIST_ENTRY ListEntry = (PVOID)((PCHAR)Process + LinkOffset);
		Process = (PEPROCESS)((PCHAR)ListEntry->Flink - LinkOffset);
		HANDLE Key = NULL;

		if (ObOpenObjectByPointer(Process, 0, NULL, 0, *PsProcessType, KernelMode, &Key) == STATUS_SUCCESS)
		{
			ULONG ulRet = 0;
			if (NULL != Key)
			{
				NtQueryInformationProcess(Key, ProcessBasicInformation, &ProcessInformation, sizeof(ProcessInformation), &ulRet);
				ZwClose(Key);
			}
		}

		if (ProcessInformation.PebBaseAddress)
		{
			for (int j = iOffset.ActiveProcessLinks_off; j < PAGE_SIZE - 0x10; j += 4)
			{
				if (*(PHANDLE)((PCHAR)Process + j) == ProcessInformation.PebBaseAddress)
				{
					iOffset.PEF_off = j;
					success = TRUE;
					return success;
				}
			}
		}
	}
	return success;
}
BOOLEAN GetOffset(IN PEPROCESS Process)
{
	BOOLEAN success = FALSE;
	HANDLE PID = PsGetCurrentProcessId();
	PLIST_ENTRY ListEntry = { 0, };
	PLIST_ENTRY NextEntry = { 0, };

	for (int i = 0x80; i < PAGE_SIZE - 0x10; i += 4)
	{
		if (*(PHANDLE)((PCHAR)Process + i) == PID)
		{
			ListEntry = (PLIST_ENTRY)((PCHAR)Process + i + 0x8);
			if (MmIsAddressValid(ListEntry) && MmIsAddressValid(ListEntry->Flink))
			{
				NextEntry = ListEntry->Flink;
				if (ListEntry == NextEntry->Blink)
				{
					iOffset.UniqueProcessid_off = i;
					iOffset.ActiveProcessLinks_off = i + 8;
					success = TRUE;
					break;
				}
			}
		}
	}
	if (!success)
	{
		DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] Can't find Offset");
		return FALSE;
	}

	success = FALSE;
	for (int i = iOffset.ActiveProcessLinks_off; i < PAGE_SIZE; i++)
	{
		if (!strncmp((PCHAR)Process + i, szSystem, 6))
		{
			iOffset.ImageFileName_off = i;
			success = TRUE;
			break;
		}
	}
	if (!success)
	{
		DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] Can't find Offset");
		return FALSE;
	}
	if (!GetPebOffset())
	{
		return success;
	}
	return success;
}
VOID ObjectPostCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_POST_OPERATION_INFORMATION OperationInformation)
{
	UNREFERENCED_PARAMETER(RegistrationContext);
	UNREFERENCED_PARAMETER(OperationInformation);

	DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] ObjectPostCallback called");

	PLIST_ENTRY pListEntry = { 0, };
	char szProcName[16] = { 0, };
	strcpy_s(szProcName, 16, (const char*)((DWORD64)OperationInformation->Object + iOffset.ImageFileName_off));
	if (!_strnicmp(szProcName, "notepad.exe", 16))
	{
		pListEntry = (PLIST_ENTRY)((DWORD64)OperationInformation->Object + iOffset.ActiveProcessLinks_off);
		if (pListEntry->Flink != NULL && pListEntry->Blink != NULL)
		{
			pListEntry->Flink->Blink = pListEntry->Blink;
			pListEntry->Blink->Flink = pListEntry->Flink;

			pListEntry->Flink = 0;
			pListEntry->Blink = 0;
		}
	}
	/*
	PERPROCESS pEprocess;
	PLIST_ENTRY pListEntry;

	PREGCONTEXT RegContext = (PREGCONTEXT)RegistrationContext;
	ULONG CurrentPid = (ULONG)PsGetProcessId((PERPROCESS)(OperationInformation->Object));

	if (Regcontext->ulProtectPid == CurrentPid && RegContext->ulMyPid != (ULONG)PsGetCurrentProcessId())
	{
		pEprocess = (PERPROCESS)(OperationInformation->Object);
		pListEntry = (PLIST_ENTRY)((Ulong)pEprocess + EPROCESS_ActiveProcessLinks_Offset);
		if (pListEntry->Flink == NULL || pListEntry->Blink == NULL)
		{
			return;
		}
		pListEntry->Flink->Blink = pListEntry->Blink;
		pListEntry->Blink->Flink = pListEntry->Flink;

		pListEntry->Flink = NULL;
		pListEntry->Blink = NULL;
	}
	*/
}
NTSTATUS ObReg()
{
	OB_OPERATION_REGISTRATION opRegistration = { 0, };
	OB_CALLBACK_REGISTRATION obRegistration = { 0, };

	opRegistration.ObjectType = PsProcessType;
	opRegistration.Operations = OB_OPERATION_HANDLE_CREATE;// | OB_OPERATION_HANDLE_DUPLICATE;
	opRegistration.PreOperation = ObjectPreCallback;
	opRegistration.PostOperation = ObjectPostCallback;

	//obRegistration.Altitude = usAltitude;
	RtlInitUnicodeString(&obRegistration.Altitude, L"33333");

	obRegistration.Version = ObGetFilterVersion();
	obRegistration.OperationRegistrationCount = 1;
	obRegistration.RegistrationContext = NULL;//(PVOID)&g_RegContext;
	obRegistration.OperationRegistration = &opRegistration;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] ObReg\n"));

	return ObRegisterCallbacks(&obRegistration, &g_hRegistration);
}
NTSTATUS DriverEntry(_In_ PDRIVER_OBJECT pDriverObject, _In_ PUNICODE_STRING RegistryPath)
{
	NTSTATUS status = STATUS_SUCCESS;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] DriverEntry\n"));

	pDriverObject->DriverUnload = DriverUnload;
#if 1
	if (GetOffset(PsGetCurrentProcess()))
	{
		status = ObReg();

		if (status == STATUS_SUCCESS)
		{
			DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[+] Success Registeration\n");
		}
		else
		{
			DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[!] Failed Registration %X\n", status);
		}
	}
	else
	{
		DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[!] Failed Get EPROCESS Offsets\n");
	}
#endif

#ifdef USE_DEVICE_ADD
	// Create the driver object
	// NOTE : creating driver is unnecessary for developping.
	WDF_DRIVER_CONFIG config;
	memset(&config, 0, sizeof(config));
	WDF_DRIVER_CONFIG_INIT(&config, KmdfHelloWorldEvtDeviceAdd);
	status = WdfDriverCreate(pDriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES, &config, WDF_NO_HANDLE);
#endif

	return status;
}

VOID DriverUnload(IN PDRIVER_OBJECT pDriverObject)
{
	UNREFERENCED_PARAMETER(pDriverObject);

	if (g_hRegistration)
	{
		ObUnRegisterCallbacks(g_hRegistration);
	}
	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] DriverUnload\n"));
}

#ifdef USE_DEVICE_ADD
// NOTE : creating driver is unnecessary for developping.
NTSTATUS KmdfHelloWorldEvtDeviceAdd(_In_ WDFDRIVER Driver, _Inout_ PWDFDEVICE_INIT DeviceInit)
{
	UNREFERENCED_PARAMETER(Driver);

	ObReg();

	NTSTATUS status;
	WDFDEVICE hDevice;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] KmdfHelloWorldEvtDeviceAdd\n"));

	status = WdfDeviceCreate(&DeviceInit, WDF_NO_OBJECT_ATTRIBUTES, &hDevice);

	return status;
}
#endif