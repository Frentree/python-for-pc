from lib_logging import *
from ctypes import windll, create_string_buffer

#import ttutil_ctypes
import errno
import os
import os.path
import ctypes

class Dscs_dll():
	def __init__(self, dll_abspath = None):
		self.dll_abspath = dll_abspath
		if None == dll_abspath:
			# Get environment variables
			systemroot = os.getenv('SystemRoot')
			self.dll_abspath = systemroot + os.sep + "DSCSLink64.dll"

		# file exist check
		if False == os.path.isfile(self.dll_abspath):
			raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.dll_abspath)

		self.dll_handle = Dscs_dll.LoadLibrary(self.dll_abspath)
		log.debug("Dscs_dll::constructor() DLL path: " + self.dll_abspath)

		self.call_DSCSAddDac()

		self.call_DSCheckDSAgent()

	def call_DSCSAddDac(self):
		pfunc = self.dll_handle.DSCSAddDac

		#lpszAcl = create_string_buffer(b"1;1;0;0;1;1;0")
		lpszAcl = create_string_buffer(b"1;1;1;1;1;1;1")
		lpszAcl_ascii = "1;1;1;1;1;1;1"
		lpszAcl = bytes(lpszAcl_ascii.encode('utf-8'))

		pfunc.argtypes = [ctypes.c_long, ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		#
		# 1st parameter(nGuide) : ex> 3
		#   - 1: 개인 권한 설정 
		#	- 2: 그룹 권한 설정 
		#	- 3: 최상위 그룹 권한 설정
		# 2nd parameter(lpszAcl) : ex > "1;1;1;1;1;1;1"
		#	- 1번째: 읽기(1: 허용 0: 차단) 
		#	- 3번째: 편집(1: 허용 0: 차단) 
		#	- 5번째: 해제(1: 허용 0: 차단) 
		#	- 7번째: 반출(1: 허용 0: 차단) 
		#	- 9번째: 인쇄(1: 허용 0: 차단) 
		#	- 11번째: 마킹(1: 마킹 함 0: 마킹 안함) 
		#	- 13번째: 권한변경(1: 허용 0: 차단)

		nGuide = 3
		ret = self.dll_handle.DSCSAddDac(nGuide, lpszAcl)
		log.debug("Dscs_dll::call_DSCSAddDac() " + lpszAcl_ascii)

		return ret

	def call_DSCheckDSAgent(self):
		pfunc = self.dll_handle.DSCheckDSAgent
		#pfunc = getattr(dll_handle, 'DSCheckDSAgent')

		pfunc.argtypes = []
		pfunc.restype = ctypes.c_uint16
		ret = self.dll_handle.DSCheckDSAgent()
		log.debug("Dscs_dll::call_DSCheckDSAgent() : " + Dscs_dll.retvalue2str("DSCheckDSAgent", ret))	

		return ret

	# Return Value:
	#   retvalue2str 함수 참조
	def call_DSCSIsEncryptedFile(self, file_abspath):
		pfunc = self.dll_handle.DSCSIsEncryptedFile

		pfunc.argtypes = [ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p = file_abspath.encode('euc-kr')
		# NOTE 직접 문자열을 생성할 때는 다음과 같이 호출
		#p = create_string_buffer(b"C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\test.txt")
		ret = self.dll_handle.DSCSIsEncryptedFile(p)

		return ret

	def call_DSCSMacEncryptFile(self, file_abspath, macid):
		pfunc = self.dll_handle.DSCSMacEncryptFile

		pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p1 = file_abspath.encode('euc-kr')
		p2 = macid.encode('euc-kr')
		try:
			ret = self.dll_handle.DSCSMacEncryptFile(p1, p2)
		except Exception as e:
			log.error(traceback.format_exc())

		return ret

	def call_DSCSDacEncryptFileV2(self, file_abspath):
		pfunc = self.dll_handle.DSCSDacEncryptFileV2

		pfunc.argtypes = [ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p1 = file_abspath.encode('euc-kr')
		try:
			ret = self.dll_handle.DSCSDacEncryptFileV2(p1)
		except Exception as e:
			log.error(traceback.format_exc())

		return ret

	def call_DSCSDecryptFile(self, file_abspath, filedec_abspath):
		pfunc = self.dll_handle.DSCSDecryptFile

		pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p1 = file_abspath.encode('euc-kr')
		p2 = filedec_abspath.encode('euc-kr')
		ret = self.dll_handle.DSCSDecryptFile(p1, p2)

		return ret

	def call_DSCSForceDecryptFile(self, file_abspath, filedec_abspath):
		pfunc = self.dll_handle.DSCSForceDecryptFile

		pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p1 = file_abspath.encode('euc-kr')
		p2 = filedec_abspath.encode('euc-kr')
		ret = self.dll_handle.DSCSForceDecryptFile(p1, p2)

		return ret

	def call_DSCSDecryptFileW(self, file_abspath, filedec_abspath):
		pfunc = self.dll_handle.DSCSDecryptFileW

		pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
		pfunc.restype = ctypes.c_uint16

		p1 = file_abspath.encode('euc-kr')
		p2 = filedec_abspath.encode('euc-kr')
		ret = self.dll_handle.DSCSDecryptFileW(p1, p2)

		return ret

	@staticmethod
	def LoadLibrary(dll_abspath):
	    dll_handle = windll.LoadLibrary(dll_abspath)
	    return dll_handle

	@staticmethod
	def retvalue2str(funcname, retvalue):
		retstr = str(retvalue) + '(undefined)'
		if 'DSCSIsEncryptedFile' == funcname:
			if -1 == retvalue:
				retstr = str(retvalue) + '(C/S 연동 모듈 로드 실패)'
			elif 0 == retvalue:
				retstr = str(retvalue) + '(일반 문서)'
			elif 1 == retvalue:
				retstr = str(retvalue) + '(암호화된 문서)'

		if 'DSCheckDSAgent' == funcname:
			if 0 == retvalue:
				retstr = str(retvalue) + '(DS Client Agent가 실행되지 않은 상태)'
			elif 1 == retvalue:
				retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그아웃 상태)'
			elif 2 == retvalue:
				retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그인 상태)'

		if 'DSCSDecryptFile' == funcname:
			if 0 == retvalue:
				retstr = str(retvalue) + '(복호화 실패)'
			elif 1 == retvalue:
				retstr = str(retvalue) + '(복호화 성공)'
			elif 3 == retvalue:
				retstr = str(retvalue) + '(문서보안 로그아웃 상태이거나 실행되지 않은 상태)'
			elif 4 == retvalue:
				retstr = str(retvalue) + '(Parameter Error)'

		if 'DSCSDacEncryptFileV2' == funcname:
			if 0 == retvalue:
				retstr = str(retvalue) + '(암호화 실패)'
			elif 1 == retvalue:
				retstr = str(retvalue) + '(암호화 성공)'
			elif 2 == retvalue:
				retstr = str(retvalue) + '(지원하지 않는 확장자)'
			elif 3 == retvalue:
				retstr = str(retvalue) + '(문서보안 클라이언트 아웃 상태)'

		if 'DSCSMacEncryptFile' == funcname:
			if 0 == retvalue:
				retstr = str(retvalue) + '(암호화 실패)'
			elif 1 == retvalue:
				retstr = str(retvalue) + '(암호화 성공)'
			elif 2 == retvalue:
				retstr = str(retvalue) + '(지원하지 않는 확장자)'
			elif 3 == retvalue:
				retstr = str(retvalue) + '(문서보안 클라이언트 아웃 상태)'


		return retstr

