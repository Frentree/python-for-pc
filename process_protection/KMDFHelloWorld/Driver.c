#include <ntddk.h>
#include <wdf.h>

DRIVER_INITIALIZE DriverEntry;
EVT_WDF_DRIVER_DEVICE_ADD KmdfHelloWorldEvtDeviceAdd;

/*
ObjectPreCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_PRE_OPERATION_INFORMATION OperationInformation)
{
	PREGCONTEXT RegContext = (PREGCONTEXT)RegistrationContext;

	ULONG CurrentPid = (ULONG)PsGetProcessId((PERPROCESS)(OperationInformation->Object));

	if (Regcontext->ulProtectPid == CurrentPid && RegContext->ulMyPid != (ULONG)PsGetCurrentProcessId())
	{
		if (OperationInformation->Parameters->CreateHandleInformation.OriginalDesiredAccess & PROCESS_TERMINATE)
		{
			OperationInformation->Parameters->CreateHandleInformation.DesiredAccess &= ~PROCESS_TERMINATE;
		}
	}
	return OB_PREOP_SUCCESS;
}
VOID ObjectPostCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_PRE_OPERATION_INFORMATION OperationInformation)
{
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
}
*/
void foo()
{
	OB_OPERATION_REGISTRATION oor = { 0, };
	OB_CALLBACK_REGISTRATION ocr = { 0, };

	oor.ObjectType = PsProcessType;
	oor.Operations = OB_OPERATION_HANDLE_CREATE | OB_OPERATION_HANDLE_DUPLICATE;
	oor.PreOperation = ObjectPreCallback;
	oor.PostOperation = ObjectPostCallback;

	RtlInitUnicodeString(&ocr.Altitude, _T("33333"));
	g_RegContext.ulMyPid = 55555;
	g_RegContext.ulProtectPid = 55555;

	//ocr.Version = ObGetFilterVersion();
	ocr.Version = OB_FLT_REGISTRATION_VERSION;
	ocr.OperationRegistrationCount = 1;
	ocr.Altitude = usAltitude;
	ocr.RegistrationContext = (PVOID)&g_RegContext;
	ocr.OperationRegistration = &oor;

	ntStatus = ObRegisterCallbacks(&ocr, &g_RegHandle);
}

NTSTATUS DriverEntry(_In_ PDRIVER_OBJECT DriverObject, _In_ PUNICODE_STRING RegistryPath)
{
	NTSTATUS status = STATUS_SUCCESS;

	WDF_DRIVER_CONFIG config;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "KmdfHelloWorld: DriverEntry\n"));

	WDF_DRIVER_CONFIG_INIT(&config, KmdfHelloWorldEvtDeviceAdd);

	memset(&config, 0, sizeof(config));
	// Create the driver object
	status = WdfDriverCreate(DriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES, &config, WDF_NO_HANDLE);

	return status;
}

NTSTATUS KmdfHelloWorldEvtDeviceAdd(_In_ WDFDRIVER Driver, _Inout_ PWDFDEVICE_INIT DeviceInit)
{
	UNREFERENCED_PARAMETER(Driver);

	foo();

	NTSTATUS status;
	WDFDEVICE hDevice;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "KmdfHelloWorld: KmdfHelloWorldEvtDeviceAdd\n"));

	status = WdfDeviceCreate(&DeviceInit, WDF_NO_OBJECT_ATTRIBUTES, &hDevice);

	return status;
}