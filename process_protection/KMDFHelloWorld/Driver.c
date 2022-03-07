#include <ntddk.h>
#include <wdf.h>

#define USE_DEVICE_ADD

DRIVER_INITIALIZE DriverEntry;

PVOID g_hRegistration = NULL;

#ifdef USE_DEVICE_ADD
// NOTE : creating driver is unnecessary for developping.
EVT_WDF_DRIVER_DEVICE_ADD KmdfHelloWorldEvtDeviceAdd;
#endif

OB_PREOP_CALLBACK_STATUS ObjectPreCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_PRE_OPERATION_INFORMATION OperationInformation)
{
	UNREFERENCED_PARAMETER(RegistrationContext);
	UNREFERENCED_PARAMETER(OperationInformation);

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
VOID ObjectPostCallback(
	_In_ PVOID RegistrationContext,
	_In_ POB_POST_OPERATION_INFORMATION OperationInformation)
{
	UNREFERENCED_PARAMETER(RegistrationContext);
	UNREFERENCED_PARAMETER(OperationInformation);

	DbgPrintEx(DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] ObjectPostCallback called");
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
NTSTATUS DriverEntry(_In_ PDRIVER_OBJECT DriverObject, _In_ PUNICODE_STRING RegistryPath)
{
	NTSTATUS status = STATUS_SUCCESS;

	KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL, "[F] DriverEntry\n"));

	// Create the driver object
	UNREFERENCED_PARAMETER(DriverObject);
	UNREFERENCED_PARAMETER(RegistryPath);
#ifdef USE_DEVICE_ADD
	// NOTE : creating driver is unnecessary for developping.
	WDF_DRIVER_CONFIG config;
	memset(&config, 0, sizeof(config));
	WDF_DRIVER_CONFIG_INIT(&config, KmdfHelloWorldEvtDeviceAdd);
	status = WdfDriverCreate(DriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES, &config, WDF_NO_HANDLE);
#endif

	return status;
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