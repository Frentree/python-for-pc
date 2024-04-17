import os
import errno
import ctypes
import traceback

class Dscs_dll():
  def __init__(self, log, dscsdll_file_name = "DSCSLink64.dll", dll_abspath = None):
    self.log = log
    if None == dll_abspath:
      systemroot = os.getenv('SystemRoot')
      self.dll_abspath = systemroot + os.sep + dscsdll_file_name
    else:
      self.dll_abspath = dll_abspath
    self.encoding = "cp949"

  @staticmethod
  def test_loadlib(log, target_path):
    dll_handle = ctypes.windll.LoadLibrary(target_path)
    log.info("Dscs_dll::test_loadlib() : " + str(dll_handle))

  @staticmethod
  def static_checkDSCSAgent(log, dscsdll_file_name):
    isInstalled = False
    isLogged = False

    systemroot = os.getenv('SystemRoot')
    dll_abspath = systemroot + os.sep + dscsdll_file_name

    isInstalled = os.path.isfile(dll_abspath)
    if False == isInstalled:
      retvalue = -1
      retstr = str(retvalue) + '(DS Client Agent가 설치되지 않은 상태)'
    else:
      dll_handle = ctypes.windll.LoadLibrary(dll_abspath)
      pfunc = dll_handle.DSCheckDSAgent
      pfunc.argtypes = []
      pfunc.restype = ctypes.c_uint16
      retvalue = dll_handle.DSCheckDSAgent()
      log.debug("Dscs_dll::DSCheckDSAgent() : " + Dscs_dll.retvalue2str("DSCheckDSAgent", retvalue))	

      if 0 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행되지 않은 상태)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그아웃 상태)'
      elif 2 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그인 상태)'

    return (retvalue, retstr)

  @staticmethod
  def static_DSCSIsEncryptedFile(log, dscsdll_file_name, filepath, encoding = "cp949"):
    (retvalue, retstr) = Dscs_dll.static_checkDSCSAgent(log, dscsdll_file_name)
    if -1 == retvalue:
      return None       # DSCSIsEncryptedFile is not Callable.
    else:
      pass              # DSCSIsEncryptedFile is Callable.

    systemroot = os.getenv('SystemRoot')
    dll_abspath = systemroot + os.sep + dscsdll_file_name
    dll_handle = ctypes.windll.LoadLibrary(dll_abspath)

    pfunc = dll_handle.DSCSIsEncryptedFile
    pfunc.argtypes = [ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p = filepath.encode(encoding)
    # NOTE 직접 문자열을 생성할 때는 다음과 같이 호출
    #p = create_string_buffer(b"C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\test.txt")
    retvalue = dll_handle.DSCSIsEncryptedFile(p)
    log.debug("Dscs_dll::DSCSIsEncryptedFile("+filepath+") : " + Dscs_dll.retvalue2str("DSCSIsEncryptedFile", retvalue))	
    if -1 == retvalue:
      retstr = str(retvalue) + '(C/S 연동 모듈 로드 실패)'
    elif 0 == retvalue:
      retstr = str(retvalue) + '(일반 문서)'
    elif 1 == retvalue:
      retstr = str(retvalue) + '(암호화된 문서)'
      return True

    return False

  def init(self, nGuide, lpszAcl, encoding = "cp949"):
    if False == os.path.isfile(self.dll_abspath):
      raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.dll_abspath)
    else:
      pass
    self.log.debug(self.dll_abspath + " exists")

    self.dll_handle = ctypes.windll.LoadLibrary(self.dll_abspath)
    self.encoding = encoding
    if 0 != len(lpszAcl):
      self.call_DSCSAddDac(nGuide, lpszAcl)
    self.call_DSCheckDSAgent()

  def isAvailable(self):
    ret = self.call_DSCheckDSAgent()
    if 2 == ret:
      return True
    else:
      return False

  def call_DSCSAddDac(self, nGuide, lpszAcl_ascii):
    pfunc = self.dll_handle.DSCSAddDac

    #lpszAcl = ctypes.create_string_buffer(b"1;1;0;0;1;1;0")
    #lpszAcl = ctypes.create_string_buffer(b"1;1;1;1;1;1;1")
    # lpszAcl_ascii = "1;1;1;1;1;1;1"
    # lpszAcl_ascii = "1;1;0;0;1;1;0"
    lpszAcl = bytes(lpszAcl_ascii.encode(self.encoding))

    pfunc.argtypes = [ctypes.c_long, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    #
    # 1st parameter(nGuide) : ex> 3
    # - 1: 개인 권한 설정 
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

    # nGuide = 3
    ret = self.dll_handle.DSCSAddDac(nGuide, lpszAcl)
    self.log.debug("Dscs_dll::call_DSCSAddDac() " + lpszAcl_ascii)

    return ret

  def call_DSCheckDSAgent(self):
    pfunc = self.dll_handle.DSCheckDSAgent
    #pfunc = getattr(dll_handle, 'DSCheckDSAgent')

    pfunc.argtypes = []
    pfunc.restype = ctypes.c_uint16
    ret = self.dll_handle.DSCheckDSAgent()
    self.log.debug("Dscs_dll::call_DSCheckDSAgent() : " + Dscs_dll.retvalue2str("DSCheckDSAgent", ret))	

    return ret

  # Return Value:
  #   retvalue2str 함수 참조
  def call_DSCSIsEncryptedFile(self, file_abspath):
    pfunc = self.dll_handle.DSCSIsEncryptedFile

    pfunc.argtypes = [ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p = file_abspath.encode(self.encoding)
    # NOTE 직접 문자열을 생성할 때는 다음과 같이 호출
    #p = create_string_buffer(b"C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\test.txt")
    ret = self.dll_handle.DSCSIsEncryptedFile(p)

    return ret

  def enc_then_remove(self, file_abspath, category_id, enc_type):
    try:
      if 'mac' == enc_type:
        ret = self.call_DSCSMacEncryptFile(file_abspath, category_id)
        self.log.info("Dscs_dll::call_DSCSMacEncryptFile("+file_abspath+") : " + Dscs_dll.retvalue2str("DSCSMacEncryptFile", ret))	
      else:
        ret = self.call_DSCSDacEncryptFileV2(file_abspath)
        self.log.info("Dscs_dll::call_DSCSDacEncryptFileV2("+file_abspath+") : " + Dscs_dll.retvalue2str("DSCSDacEncryptFileV2", ret))	
      os.remove(file_abspath)
    except Exception as e:
      import traceback
      self.log.error(traceback.format_exc())
      self.log.error(e)

  # region not used, for dev. -----------------------------------------------------
  def call_DSCSDacEncryptFileV2(self, file_abspath):
    pfunc = self.dll_handle.DSCSDacEncryptFileV2

    pfunc.argtypes = [ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p1 = file_abspath.encode(self.encoding)
    try:
      ret = self.dll_handle.DSCSDacEncryptFileV2(p1)
    except Exception as e:
      self.log.error(traceback.format_exc())

    return ret

  def call_DSCSForceDecryptFile(self, file_abspath, filedec_abspath):
    pfunc = self.dll_handle.DSCSForceDecryptFile

    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p1 = file_abspath.encode(self.encoding)
    p2 = filedec_abspath.encode(self.encoding)
    ret = self.dll_handle.DSCSForceDecryptFile(p1, p2)

    return ret

  def call_DSCSDecryptFileW(self, file_abspath, filedec_abspath):
    pfunc = self.dll_handle.DSCSDecryptFileW

    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p1 = file_abspath.encode(self.encoding)
    p2 = filedec_abspath.encode(self.encoding)
    ret = self.dll_handle.DSCSDecryptFileW(p1, p2)

    return ret
  # endregion -----------------------------------------------------

  def call_DSCSMacEncryptFile(self, file_abspath, macid):
    pfunc = self.dll_handle.DSCSMacEncryptFile

    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p1 = file_abspath.encode(self.encoding)
    p2 = macid.encode(self.encoding)
    try:
      ret = self.dll_handle.DSCSMacEncryptFile(p1, p2)
    except Exception as e:
      self.log.error(traceback.format_exc())
      self.log.error(e)

    return ret

  # region DSCSDecryptFile
  @staticmethod
  def get_decrypted_filepath(file_abspath, bAppendPostfix, postfix='_decrypted'):
    import ntpath
    import pathlib
    bname = ntpath.basename(file_abspath)
    pure_file_stem = pathlib.PurePath(bname).stem
    pure_file_ext  = pathlib.PurePath(bname).suffix
    filepath2 = ntpath.dirname(file_abspath) + os.sep + pure_file_stem + \
      (postfix if bAppendPostfix else "") + pure_file_ext
    return filepath2

  def decryptFile(self, file_abspath, bAppendPostfix, postfix='_decrypted'):
    filepath2 = Dscs_dll.get_decrypted_filepath(file_abspath, bAppendPostfix, postfix)
    ret = self.call_DSCSDecryptFile(file_abspath, filepath2)
    if 1 != ret:  # fail
      self.log.error("Dscs_dll::call_DSCSDecryptFile() : " + file_abspath + ", " + filepath2 + " " + str(ret))
    else:         # success
      self.log.debug("Dscs_dll::call_DSCSDecryptFile() : " + file_abspath + ", " + filepath2 + " " + str(ret))
    return ret

  def call_DSCSDecryptFile(self, file_abspath, filedec_abspath):
    pfunc = self.dll_handle.DSCSDecryptFile

    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p1 = file_abspath.encode(self.encoding)
    p2 = filedec_abspath.encode(self.encoding)
    ret = self.dll_handle.DSCSDecryptFile(p1, p2)

    return ret

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

if __name__ == '__main__':
  filepath_decrypted = Dscs_dll.get_decrypted_filepath("c:\한글테스트.txt", True)
  print(filepath_decrypted)