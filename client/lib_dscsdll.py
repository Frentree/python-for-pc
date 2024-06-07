import os
import errno
import ctypes
import traceback

# note : 클래스로 구조체 선언, 함수 관련 모음
class Dscs_dll():
  # note : 함수 초기 설정, dll 경로 등 최초 설정값을 불러오도록 세팅되어 있음.(각 함수마다 dll 경로는 재설정하도록 되어있음)
  def __init__(self, log, dscsdll_file_name = "DSCSLink64.dll", dll_abspath = None):
    # note : main 등에서 작성되고 있는 로그에 대해 이 소스에서도 불러올 수 있도록 세팅
    self.log = log
    # note : 초기화 하는 중 세팅된 경로가 없다면, 직접 설정해주도록. 해당 부분도 차후 소스 수정이나 조치 필요.
    if None == dll_abspath:
      systemroot = os.getenv('SystemRoot')
      self.dll_abspath = systemroot + os.sep + dscsdll_file_name
    else:
      self.dll_abspath = dll_abspath
    # note : 이전에 한글로 된 경로를 불러오지 못하거나, 소프트캠프에서 dll 빌드 시 인코딩 타입에 의해 문제 발생된 경우 있어, 수동으로 세팅
    self.encoding = "cp949"

  @staticmethod
  # note : dll 파일을 호출하였을 때 발생하던 frozen 에러에 대해 테스트 진행하기 위한 함수
  def test_loadlib(log, target_path):
    # note : 해당 dll에 대해 라이브러리 호출 시 발생되는 메세지 체크
    ## 정상일 때에는 별도의 에러가 발생하지 않음
    dll_handle = ctypes.windll.LoadLibrary(target_path)
    log.info("Dscs_dll::test_loadlib() : " + str(dll_handle))

  @staticmethod
  # note : DRM 설치 여부, 상태 체크하기 위한 함수
  def static_checkDSCSAgent(log, dscsdll_file_name):
    isInstalled = False
    isLogged = False

    # note : 호출되는 경로를 하드코딩으로 세팅, 현재 조치된 방법으로는 2020년도 생성된 dll 파일을 ftclient.dll(dscsdll_file_name)로 변경, 호출하도록 설정
    systemroot = os.getenv('SystemRoot')
    # note : python의 경우, 경로 구분자를 \\ 로 사용하고 있으나, 명확하게 보기 위해 os.sep으로 설정
    dll_abspath = systemroot + os.sep + dscsdll_file_name

    # note : 해당 경로에 파일이 있는 경우 true, 없으면 false로 출력
    isInstalled = os.path.isfile(dll_abspath)
    if False == isInstalled:
      # note : DRM이 설치되어 있지 않을 때
      retvalue = -1
      retstr = str(retvalue) + '(DS Client Agent가 설치되지 않은 상태)'
    else:
      # note : drm이 설치되어 있어 해당 라이브러리를 호출하는 경우. 대부분 이쪽으로 소스가 진행될 것이며, 위의 경우는 소스 수정이 필요
      # note : 라이브러리를 호출하여 해당 dll 파일 내 함수들을 메모리로 호출
      dll_handle = ctypes.windll.LoadLibrary(dll_abspath)
      # note : DRM 함수 중 DRM에이전트 상태 체크하는 함수 호출
      pfunc = dll_handle.DSCheckDSAgent
      # note : 변수는 빈 값으로
      pfunc.argtypes = []
      # note : 함수 리턴 타입을 int16으로 설정
      pfunc.restype = ctypes.c_uint16
      # note : 함수를 실행 시키고, 호출 결과를 retvalue에 기입
      retvalue = dll_handle.DSCheckDSAgent()
      # note : 로그로 출력.
      log.debug("Dscs_dll::DSCheckDSAgent() : " + Dscs_dll.retvalue2str("DSCheckDSAgent", retvalue))	

      # note : 결과값에 따른 메세지 출력
      if 0 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행되지 않은 상태)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그아웃 상태)'
      elif 2 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그인 상태)'

    return (retvalue, retstr)

  @staticmethod
  # note : 파일 암호화 여부 체크
  def static_DSCSIsEncryptedFile(log, dscsdll_file_name, filepath, encoding = "cp949"):
    # note : 에이전트 상태 체크 먼저 진행하고, DRM이 행, 랙걸리거나 설치가 안된 경우는 종료, 그 이외의 경우는 진행
    (retvalue, retstr) = Dscs_dll.static_checkDSCSAgent(log, dscsdll_file_name)
    if -1 == retvalue:
      return None       # DSCSIsEncryptedFile is not Callable.
    else:
      pass              # DSCSIsEncryptedFile is Callable.

    # note : 함수를 사용하기 위해 라이브러리 호출
    systemroot = os.getenv('SystemRoot')
    dll_abspath = systemroot + os.sep + dscsdll_file_name
    dll_handle = ctypes.windll.LoadLibrary(dll_abspath)

    # note : DRM 함수 DSCSIsEncryptedFile 함수를 호출
    pfunc = dll_handle.DSCSIsEncryptedFile
    # note : 암호화 방식에 대한 정보를 변수에 입력한 후 파일 경로를 호출시킨다.
    pfunc.argtypes = [ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    p = filepath.encode(encoding)
    # NOTE 직접 문자열을 생성할 때는 다음과 같이 호출
    #p = create_string_buffer(b"C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\test.txt")
    retvalue = dll_handle.DSCSIsEncryptedFile(p)
    # note : 결과값에 대해 로그에 출력하고,
    log.debug("Dscs_dll::DSCSIsEncryptedFile("+filepath+") : " + Dscs_dll.retvalue2str("DSCSIsEncryptedFile", retvalue))
    # note : 해당 데이터에 대해 리턴값을 보낸다. 1인 경우를 제외하고 나머지는 실패로 출력
    if -1 == retvalue:
      retstr = str(retvalue) + '(C/S 연동 모듈 로드 실패)'
    elif 0 == retvalue:
      retstr = str(retvalue) + '(일반 문서)'
    elif 1 == retvalue:
      retstr = str(retvalue) + '(암호화된 문서)'
      return True

    return False

  # note : 해당 라이브러리를 초기화 하기
  ### self : dscsdll 클래스, nGuide : 암호화 그룹, lpszAcl : 암호화 정책, encoding : 인코딩 타입, OS 환경에 따라 바뀔 필요가 있다.
  def init(self, nGuide, lpszAcl, encoding = "cp949"):
    # note : dll파일에 대해 존재 여부 체크
    if False == os.path.isfile(self.dll_abspath):
      raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.dll_abspath)
    else:
      pass
    self.log.debug(self.dll_abspath + " exists")

    # note : 라이브러리 호출, 인코딩 타입 세팅
    self.dll_handle = ctypes.windll.LoadLibrary(self.dll_abspath)
    self.encoding = encoding
    # note : DRM 정책 설정, 기준값은 warroom 계정에 대한 설정. 자세한 내용은 가이드 문서 또는 call_DSCSAddDac 함수 참고
    if 0 != len(lpszAcl):
      self.call_DSCSAddDac(nGuide, lpszAcl)
    # note : DRM 에이전트 상태 체크
    self.call_DSCheckDSAgent()

  # note : 사용 가능한 상태인지 체크하는 함수. 사용되는거 거의 본적 없음
  def isAvailable(self):
    ret = self.call_DSCheckDSAgent()
    if 2 == ret:
      return True
    else:
      return False

  # note : 정책 호출
  def call_DSCSAddDac(self, nGuide, lpszAcl_ascii):
    pfunc = self.dll_handle.DSCSAddDac

    #lpszAcl = ctypes.create_string_buffer(b"1;1;0;0;1;1;0")
    #lpszAcl = ctypes.create_string_buffer(b"1;1;1;1;1;1;1")
    # lpszAcl_ascii = "1;1;1;1;1;1;1"
    # lpszAcl_ascii = "1;1;0;0;1;1;0"
    lpszAcl = bytes(lpszAcl_ascii.encode(self.encoding))

    # note : 적용되어있는 정책에 대해 호출하는 부분
    pfunc.argtypes = [ctypes.c_long, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # DSCSAddDac 파라미터 참고
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

  # note : DRM 상태 체크값 호출
  def call_DSCheckDSAgent(self):
    # note : 체크 함수 호출
    pfunc = self.dll_handle.DSCheckDSAgent
    #pfunc = getattr(dll_handle, 'DSCheckDSAgent')

    # note : 호출된 값에 대해 변수 없이 값 세팅한 후 값 호출
    ## 변수 설정(null)
    pfunc.argtypes = []
    ## 리턴 타입 재선언
    pfunc.restype = ctypes.c_uint16
    ## 함수 호출
    ret = self.dll_handle.DSCheckDSAgent()
    ## 결과값 로그 출력
    self.log.debug("Dscs_dll::call_DSCheckDSAgent() : " + Dscs_dll.retvalue2str("DSCheckDSAgent", ret))	

    return ret

  # Return Value:
  #   retvalue2str 함수 참조
  # note : 암호화된 함수인지 체크
  def call_DSCSIsEncryptedFile(self, file_abspath):
    # note : DRM라이브러리를 통해 파일 암호화 여부 체크
    ## 핸들러에서 함수 호출
    pfunc = self.dll_handle.DSCSIsEncryptedFile
    ## 변수 설정
    pfunc.argtypes = [ctypes.c_char_p]
    ## 리턴 타입 재선언
    pfunc.restype = ctypes.c_uint16

    ## 경로에 대해 python용으로 재 인코딩 
    p = file_abspath.encode(self.encoding)
    # NOTE 직접 문자열을 생성할 때는 다음과 같이 호출
    #p = create_string_buffer(b"C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\test.txt")
    ## 세팅된 값으로 함수 실행
    ret = self.dll_handle.DSCSIsEncryptedFile(p)

    return ret

  # note : 파일 암호화 후 삭제(수정된 파일에 대해 복호화 한 후 스캔까지 완료되었을 떄 돌아가는 부분)
  ## self : 현재 로드되어있는 라이브러리, file_abspath : ??, category_id : s(Swing)/p(PS&M), enc_type : 설치되어있는 OS 종류. Mac은 사용하지 않는다.
  def enc_then_remove(self, file_abspath, category_id, enc_type):
    try:
      if 'mac' == enc_type:
        # note : 맥 용 암호화. 해당 기능은 사용하지 않음
        ret = self.call_DSCSMacEncryptFile(file_abspath, category_id)
        self.log.info("Dscs_dll::call_DSCSMacEncryptFile("+file_abspath+") : " + Dscs_dll.retvalue2str("DSCSMacEncryptFile", ret))	
      else:
        # note : 그 이외. 윈도우 암호화 시 사용
        ret = self.call_DSCSDacEncryptFileV2(file_abspath)
        self.log.info("Dscs_dll::call_DSCSDacEncryptFileV2("+file_abspath+") : " + Dscs_dll.retvalue2str("DSCSDacEncryptFileV2", ret))	
      # note : 암호화 후 파일 삭제 진행
      os.remove(file_abspath)
    except Exception as e:
      import traceback
      self.log.error(traceback.format_exc())
      self.log.error(e)

  # region not used, for dev. -----------------------------------------------------
  # note : 암호화 로직. 윈도우 암호화 할 때 쓰임
  def call_DSCSDacEncryptFileV2(self, file_abspath):
    # note : DRM 함수 호출
    pfunc = self.dll_handle.DSCSDacEncryptFileV2

    # note : 변수 및 리턴타입 지정한 후
    pfunc.argtypes = [ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # note : 경로 python용으로 설정
    p1 = file_abspath.encode(self.encoding)
    try:
      # note : 암호화 진행
      ret = self.dll_handle.DSCSDacEncryptFileV2(p1)
    except Exception as e:
      self.log.error(traceback.format_exc())

    return ret

  # note : 강제로 파일 복호화 진행
  def call_DSCSForceDecryptFile(self, file_abspath, filedec_abspath):
    # note : 핸들러에서 함수 호출
    pfunc = self.dll_handle.DSCSForceDecryptFile

    # note : 변수 세팅 및 리턴 타입 설정
    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # note : 강제로 파일 복호화 진행
    ## 암호화 된 파일
    p1 = file_abspath.encode(self.encoding)
    ## 복호화 된 파일
    p2 = filedec_abspath.encode(self.encoding)
    # note : 함수 실행
    ret = self.dll_handle.DSCSForceDecryptFile(p1, p2)

    return ret

  # note : 파일 복호화하여 해제하기
  def call_DSCSDecryptFileW(self, file_abspath, filedec_abspath):
    # note : DRM 함수 호출ㄱ
    pfunc = self.dll_handle.DSCSDecryptFileW

    # note : 파라미터 타입 선언, 결과 타입 재선언
    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # note : 암복호 파일 인코딩 변경 후 복호화 진행
    ## 암호화 된 파일
    p1 = file_abspath.encode(self.encoding)
    ## 복호화 될 파일명
    p2 = filedec_abspath.encode(self.encoding)
    ## 함수 실행
    ret = self.dll_handle.DSCSDecryptFileW(p1, p2)

    return ret
  # endregion -----------------------------------------------------

  # note : 맥 용 함수. 쓸 일 없을것으로 추정. 남겨만 놓자.
  def call_DSCSMacEncryptFile(self, file_abspath, macid):
    # note : DRM 함수 호출
    pfunc = self.dll_handle.DSCSMacEncryptFile

    # note : 변수 타입, 리턴 타입 재선언
    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # note : 암호화 할 파일 및 맥 전용 암호화 정책 설정
    p1 = file_abspath.encode(self.encoding)
    p2 = macid.encode(self.encoding)
    try:
      # note : 암호화 함수 실행
      ret = self.dll_handle.DSCSMacEncryptFile(p1, p2)
    except Exception as e:
      # note : 에러에 대한 로그 출력
      self.log.error(traceback.format_exc())
      self.log.error(e)

    return ret

  # region DSCSDecryptFile
  @staticmethod
  # note :  파일 복호화 시킬 파일 경로명 생성
  ## 암호화 파일명과 복호화 파일명이 같을 경우, 암호화 파일에 덮어써서 복호화 진행되기 때문에 복호화 파일명 뒤에는 _decrypted 텍스트 붙여서 구분하기 위함
  ## file_abspath : 암호화 된 파일의 절대경로, bAppendPostfix : 텍스트 붙일지 여부, postfix : 복호화 될 파일명의 뒤에 붙을 텍스트
  def get_decrypted_filepath(file_abspath, bAppendPostfix, postfix='_decrypted'):
    # note : 파일 경로 추출을 위한 라이브러리 임포트 시키기
    import ntpath
    import pathlib
    # note : 파일 명만 추리기
    bname = ntpath.basename(file_abspath)
    # note : 순수한 파일명만 추리고
    pure_file_stem = pathlib.PurePath(bname).stem
    # note : 확장자 추린 후
    pure_file_ext  = pathlib.PurePath(bname).suffix
    # note : 복호화할 파일 경로 명 생성하기
    filepath2 = ntpath.dirname(file_abspath) + os.sep + pure_file_stem + \
      (postfix if bAppendPostfix else "") + pure_file_ext
    return filepath2

  # note : 파일 복호화 시키기
  ## self : 호출할 라이브러리 핸들러, file_abspath : 복호화 할 파일의 절대경로, bAppendPostfix : 복호화 할 때 텍스트 붙일지 여부, postfix : 복호화 시 붙일 텍스트
  def decryptFile(self, file_abspath, bAppendPostfix, postfix='_decrypted'):
    # note : 복호화 할 파일 명 생성
    filepath2 = Dscs_dll.get_decrypted_filepath(file_abspath, bAppendPostfix, postfix)
    # note : 복호화 할 함수 실행
    ret = self.call_DSCSDecryptFile(file_abspath, filepath2)
    # note : 결과값에 따른 로그 생성
    if 1 != ret:  # fail
      self.log.error("Dscs_dll::call_DSCSDecryptFile() : " + file_abspath + ", " + filepath2 + " " + str(ret))
    else:         # success
      self.log.debug("Dscs_dll::call_DSCSDecryptFile() : " + file_abspath + ", " + filepath2 + " " + str(ret))
    return ret

  # note : DRM 복호화 함수 호출
  ## self : 호출할 라이브러리 핸들러, file_abspath : 복호화 할 암호화파일의 경로, filedec_abspath : 복호화 파일 경로
  def call_DSCSDecryptFile(self, file_abspath, filedec_abspath):
    # note : 핸들러에서 함수 호출
    pfunc = self.dll_handle.DSCSDecryptFile

    # note : 변수 타입 재설정, 리턴 타입 재설정
    pfunc.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    pfunc.restype = ctypes.c_uint16

    # note : 암복호화 할 경로 인코딩 변경
    ## 암호화 된 파일 경로 인코딩
    p1 = file_abspath.encode(self.encoding)
    ## 복호화 될 파일 경로 인코딩
    p2 = filedec_abspath.encode(self.encoding)
    ## 함수 실행
    ret = self.dll_handle.DSCSDecryptFile(p1, p2)

    return ret

  @staticmethod
  # note : 결과값에 대해 string으로 변환하는 소스
  ## funcname : 실행한 함수 명, retvalue : 실행된 함수의 결과값
  def retvalue2str(funcname, retvalue):
    # note : 기본 초기값을 설정, 돌아오는 값이 무엇이든 조건값 뒤에 undefined를 추가하여 출력하도록
    retstr = str(retvalue) + '(undefined)'
    # note : 암호화된 파일인지 체크하는 함수의 경우
    ## -1 : DRM 함수 로드 실패, 0 : 일반 문서, 1 : 암호화 된 문서
    if 'DSCSIsEncryptedFile' == funcname:
      if -1 == retvalue:
        retstr = str(retvalue) + '(C/S 연동 모듈 로드 실패)'
      elif 0 == retvalue:
        retstr = str(retvalue) + '(일반 문서)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(암호화된 문서)'

    # note : DRM 에이전트 상태 체크
    ## 0 : 에이전트가 실행되지 않은 경우, 1 : 에이전트는 실행되어있으나, 로그아웃, 2 : 에이전트가 실행되어있으며, 로그인상태
    if 'DSCheckDSAgent' == funcname:
      if 0 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행되지 않은 상태)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그아웃 상태)'
      elif 2 == retvalue:
        retstr = str(retvalue) + '(DS Client Agent가 실행상태이며 로그인 상태)'

    # note : DRM 암호파일 복호화 
    ## 0 : 복호화 실패, 1 : 복호화 성공, 2 : DRM 에이전트의 상태가 비정상일때, 4 : 입력된 변수가 문제가 있을 때
    if 'DSCSDecryptFile' == funcname:
      if 0 == retvalue:
        retstr = str(retvalue) + '(복호화 실패)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(복호화 성공)'
      elif 3 == retvalue:
        retstr = str(retvalue) + '(문서보안 로그아웃 상태이거나 실행되지 않은 상태)'
      elif 4 == retvalue:
        retstr = str(retvalue) + '(Parameter Error)'

    # note : DRM 파일 암호화 
    ## 맥 이외의 경우 해당 함수를 실행하게 되어있음
    ## 0 : 암호화 실패, 1 : 암호화 성공, 2 : 지원하지 않는 확장자를 암호화 할 때, 4 : DRM 로그아웃 상태
    if 'DSCSDacEncryptFileV2' == funcname:
      if 0 == retvalue:
        retstr = str(retvalue) + '(암호화 실패)'
      elif 1 == retvalue:
        retstr = str(retvalue) + '(암호화 성공)'
      elif 2 == retvalue:
        retstr = str(retvalue) + '(지원하지 않는 확장자)'
      elif 3 == retvalue:
        retstr = str(retvalue) + '(문서보안 클라이언트 아웃 상태)'

    # note : MacOS의 경우 파일 암호화
    ## 맥의 경우, 해당 OS를 통해 파일 암호화 진행
    ## 0 : 암호화 실패, 1 : 암호화 성공, 2 : 지원하지 않는 확장자를 암호화 할 때, 4 : DRM 로그아웃 상태
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

# note : lib_dscsdll 소스의 메인함수. 인코딩 타입 테스트를 위해 기입.
## 실제 해당 파일이 없는 경우도 있으나, 리턴값은 항상 출력하도록 설정되어있음.(단, 인코딩 타입이 맞아 한글이 정상적으로 호출될 때)
if __name__ == '__main__':
  filepath_decrypted = Dscs_dll.get_decrypted_filepath("c:\한글테스트.txt", True)
  print(filepath_decrypted)