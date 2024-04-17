# python-for-pc

# installation
1. 방법1 - install.exe를 실행한다.
2. 방법2 - package.exe를 실행한다.

# uninstall
1. 방법1 - install.exe를 실행한다.
2. 방법2 - package.exe _remove를 실행한다.

# 설치파일 구성
* install.exe : silent installer - 별도의 command창을 실행하지 않음
* uninstall.exe : silent uninstaller - 별도의 command창을 실행하지 않음
* package.exe : 설치되는 실행파일 본체
* configuration.json : 초기설정값을 저장하는 json형식의 파일

# configurations
* SVC_DESCRIPTION: 서비스 설명
* SVC_NAME: 서비스 이름
* SVC_DISPLAY_NAME: 서비스 표시 이름
* SVC_HIDE: 서비스 보호 기능 사용 여부 ('True' or 'False')

# 로깅
1. 로그파일의 경로
    * %systemdrive%\Program Files (x86)\Ground Labs\Enterprise Recon 2\20220621.txt
2. 로그파일의 최대 크기와 갯수
    * 로그파일의 크기가 최대 크기 설정값 'LOGFILE_MAXBYTES'를 넘지 않는다.
    * 로그파일의 수는 설정값 'LOGFILE_BACKUPCOUNT'의 수만큼 생성된다.
    * 따라서, 로그파일들의 최대 용량은 ('LOGFILE_MAXBYTES' X 'LOGFILE_BACKUPCOUNT') bytes이다.

# 서비스 프로세스 보호기능
* 설정값 'SVC_HIDE'를 'True'로 설정하면 서비스 프로세스 보호기능을 사용한다.
* 서비스 프로세스 보호기능을 켰을 경우에는 services.msc에서 서비스를 조회할 수 없다.
* 'SVC_HIDE'를 'False'로 설정하면 서비스를 services.msc에서 확인할 수 있다.

# 서비스 이름
* 'SVC_NAME'값을 변경하면 서비스 이름을 변경할 수 있다.

# API Server - TEST PAGE 
* API Server IP를 사용하여 다음과 같은 주소로 web browser를 이용하여 TEST PAGE를 사용할 수 있다.
* http://183.107.9.230:11119/

# API Server - run_cmd
* client 가 설치된 컴퓨터를 hostname으로 식별하여 명령을 실행할 수 있다.
* 다음 예시에서 명령 실행이 성공 시에 해당 컴퓨터에서 mspaint가 실행된다.
```
{
    "is_success": "true",
    "result": [
        {
            "index": "1152",
            "hostname": "DESKTOP-K316RAH",
            "path": "c:\\windows\\system32\\mspaint.exe",
            "type": "run_cmd",
            "category_no": "p",
            "done": "1",
            "success": "1",
            "result": ""
        }
    ]
}
```

# 시험서 - 
## Enterprise Recon 2 Agent
some seconds 후에 다시 running상태가 됨을 확인한다.

## 모든 파일 traversing
* install 후 traversing을 실행 - install package의 configuration.json의 내용을 다음과 같이 저장하고 실행하면 traversing을 실행한다.
```
{
    ......
    "DSCS_ALL_FILES_TRAVERSED": "False",
    ......
}
```

* install 후 traversing을 실행하지 않음 - install package의 configuration.json의 내용을 다음과 같이 저장하고 실행하면 traversing을 실행하지 않는다.
```
{
    ......
    "DSCS_ALL_FILES_TRAVERSED": "True",
    ......
}
```

## scanning 파일 queue 확인
* 다음과 같이 실행하여 현재 저장된 file Queue 리스트를 확인할 수 있다.
```
C:\Users\Admin\Desktop\python-for-pc_v2\00.RELEASE>package.exe _dbg_list_sqlite_db
2022:06:21 21:20:38.552 [26348] INFO     main.py              proc_cmdline         480 ['package.exe', '_dbg_list_sqlite_db']
2022:06:21 21:20:38.552 [26348] DEBUG    lib_sqlite3.py       __init__             10 DB : C:\Program Files (x86)\Ground Labs\Enterprise Recon 2\DRM\state.db
2022:06:21 21:20:38.554 [26348] INFO     main.py              proc_cmdline         515  == QUEUE list ==
2022:06:21 21:20:38.555 [26348] INFO     main.py              proc_cmdline         520 (1, 'C:\\Users\\Admin\\Desktop\\1119\\디자인수정정리.pptx', None, 58784924, 'queued', None, None)
2022:06:21 21:20:38.555 [26348] INFO     main.py              proc_cmdline         520 (2, 'C:\\Users\\Admin\\Desktop\\1119\\최종_1110_폰트\\기획서\\211105_수정사항_1차.pptx', None, 6394076, 'queued', None, None)
2022:06:21 21:20:38.555 [26348] INFO     main.py              proc_cmdline         520 (3, 'C:\\Users\\Admin\\Desktop\\1119\\최종_1110_폰트\\기획서\\211105_수정사항_1차_ver2.pptx', None, 8170556, 'queued', None, None)
2022:06:21 21:20:38.555 [26348] INFO     main.py              proc_cmdline         520 (4, 'C:\\Users\\Admin\\Desktop\\1119\\최종_1110_폰트\\기획서\\온라인전시관_개요도_1101.pptx', None, 12970908, 'queued', None, None)
2022:06:21 21:20:38.555 [26348] INFO     main.py              proc_cmdline         520 (5, 'C:\\Users\\Admin\\Desktop\\1119\\최종_1110_폰트\\기획서\\참가신청관련자료.xlsx', None, 23244, 'queued', None, None)
2022:06:21 21:20:38.556 [26348] INFO     main.py              proc_cmdline         520 (6, 'C:\\Users\\Admin\\Desktop\\1119\\최종_1110_폰트\\기획서\\참가신청관련자료_decrypted.xlsx', None, 23276, 'queued', None, None)
2022:06:21 21:20:38.556 [26348] INFO     main.py              proc_cmdline         520 (7, 'C:\\Users\\Admin\\Desktop\\2.xlsx', None, 11084, 'queued', None, None)
2022:06:21 21:20:38.556 [26348] INFO     main.py              proc_cmdline         520 (8, 'C:\\Users\\Admin\\Desktop\\2021.05.16.txt', None, 1980, 'queued', None, None)
2022:06:21 21:20:38.556 [26348] INFO     main.py              proc_cmdline         520 (9, 'C:\\Users\\Admin\\Desktop\\2021.05.16_decrypted.txt', None, 1996, 'queued', None, None)
2022:06:21 21:20:38.556 [26348] INFO     main.py              proc_cmdline         520 (10, 'C:\\Users\\Admin\\Desktop\\2022.03.03_kuiper_backup\\bbbbb\\2022.03.21_인생네컷_견적서양식_양선.xlsx', None, 17420, 'queued', None, None)
2022:06:21 21:20:38.557 [26348] INFO     main.py              proc_cmdline         520 (11, 'C:\\Users\\Admin\\Desktop\\2022.03.03_kuiper_backup\\bbbbb\\2022.03.21_인생네컷_견적서양식_양선_decrypted.xlsx', None, 17452, 'queued', None, None)
2022:06:21 21:20:38.557 [26348] INFO     main.py              proc_cmdline         520 (12, 'C:\\Users\\Admin\\Desktop\\2_decrypted.xlsx', None, 11116, 'queued', None, None)
2022:06:21 21:20:38.557 [26348] INFO     main.py              proc_cmdline         520 (13, 'C:\\Users\\Admin\\Desktop\\a.txt', None, 35356, 'queued', None, None)
2022:06:21 21:20:38.557 [26348] INFO     main.py              proc_cmdline         520 (14, 'C:\\Users\\Admin\\Desktop\\aaa\\10.txt', None, 1756, 'queued', None, None)
2022:06:21 21:20:38.557 [26348] INFO     main.py              proc_cmdline         520 (15, 'C:\\Users\\Admin\\Desktop\\aaa\\7.txt', None, 1676, 'queued', None, None)
2022:06:21 21:20:38.558 [26348] INFO     main.py              proc_cmdline         520 (16, 'C:\\Users\\Admin\\Desktop\\ai\\Adobe Creative Suite CS5 Master Collection\\Adobe Creative Suite CS5 Master Collection\\설치법.txt', None, 2620, 'queued', None, None)
2022:06:21 21:20:38.558 [26348] INFO     main.py              proc_cmdline         520 (17, 'C:\\Users\\Admin\\Desktop\\coever\\example.csv', None, 17648684, 'queued', None, None)
2022:06:21 21:20:38.558 [26348] INFO     main.py              proc_cmdline         520 (18, 'C:\\Users\\Admin\\Desktop\\coever\\양불예시 - 복사본.csv', None, 17648684, 'queued', None, None)
2022:06:21 21:20:38.558 [26348] INFO     main.py              proc_cmdline         520 (19, 'C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\testdec.txt', None, 1452, 'queued', None, None)
2022:06:21 21:20:38.558 [26348] INFO     main.py              proc_cmdline         520 (20, 'C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\Debug\\한글.txt', None, 1516, 'queued', None, None)
2022:06:21 21:20:38.559 [26348] INFO     main.py              proc_cmdline         520 (21, 'C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\x64\\Debug\\test.txt', None, 1516, 'queued', None, None)
2022:06:21 21:20:38.559 [26348] INFO     main.py              proc_cmdline         520 (22, 'C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\x64\\Debug\\test1.txt', None, 1468, 'queued', None, None)
2022:06:21 21:20:38.559 [26348] INFO     main.py              proc_cmdline         520 (23, 'C:\\Users\\Admin\\Desktop\\DLLProject\\dllproject\\x64\\Debug\\한글.txt', None, 1516, 'queued', None, None)
2022:06:21 21:20:38.559 [26348] INFO     main.py              proc_cmdline         520 (24, 'C:\\Users\\Admin\\Desktop\\electron-xls-app\\example.xlsx', None, 8028, 'queued', None, None)
2022:06:21 21:20:38.559 [26348] INFO     main.py              proc_cmdline         520 (25, 'C:\\Users\\Admin\\Desktop\\logs.txt', None, 1468, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (26, 'C:\\Users\\Admin\\Desktop\\README.txt', None, 2236, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (27, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\1.txt', None, 1484, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (28, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\a.txt', None, 1868, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (29, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\python-evtx\\LICENSE.TXT', None, 13004, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (30, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\skt_drm_scanning_table - 복사본 - 복사본.xlsx', None, 12460, 'queued', None, None)
2022:06:21 21:20:38.560 [26348] INFO     main.py              proc_cmdline         520 (31, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\skt_drm_scanning_table - 복사본.xlsx', None, 12444, 'queued', None, None)
2022:06:21 21:20:38.561 [26348] INFO     main.py              proc_cmdline         520 (32, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (10).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.561 [26348] INFO     main.py              proc_cmdline         520 (33, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (11).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.561 [26348] INFO     main.py              proc_cmdline         520 (34, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (2).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.561 [26348] INFO     main.py              proc_cmdline         520 (35, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (3).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.562 [26348] INFO     main.py              proc_cmdline         520 (36, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (4).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.565 [26348] INFO     main.py              proc_cmdline         520 (37, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (5).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.565 [26348] INFO     main.py              proc_cmdline         520 (38, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (6).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.566 [26348] INFO     main.py              proc_cmdline         520 (39, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (7).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.566 [26348] INFO     main.py              proc_cmdline         520 (40, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (8).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.566 [26348] INFO     main.py              proc_cmdline         520 (41, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (9).txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.566 [26348] INFO     main.py              proc_cmdline         520 (42, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본.txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.566 [26348] INFO     main.py              proc_cmdline         520 (43, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt', None, 1660, 'queued', None, None)
2022:06:21 21:20:38.567 [26348] INFO     main.py              proc_cmdline         520 (44, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣12.txt', None, 1740, 'queued', None, None)
2022:06:21 21:20:38.567 [26348] INFO     main.py              proc_cmdline         520 (45, 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\시험설명서111.docx', None, 1309884, 'queued', None, None)
2022:06:21 21:20:38.567 [26348] INFO     main.py              proc_cmdline         520 (46, 'C:\\Users\\Admin\\Desktop\\repos\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt', None, 1564, 'queued', None, None)
2022:06:21 21:20:38.567 [26348] INFO     main.py              proc_cmdline         520 (47, 'C:\\Users\\Admin\\Desktop\\vbox_shared\\u.txt', None, 1628, 'queued', None, None)
2022:06:21 21:20:38.567 [26348] INFO     main.py              proc_cmdline         520 (48, 'C:\\Users\\Admin\\Desktop\\기타\\1.xlsx', None, 11564, 'queued', None, None)
2022:06:21 21:20:38.568 [26348] INFO     main.py              proc_cmdline         520 (49, 'C:\\Users\\Admin\\Desktop\\기타\\diamonds.csv', None, 568444, 'queued', None, None)
2022:06:21 21:20:38.568 [26348] INFO     main.py              proc_cmdline         520 (50, 'C:\\Users\\Admin\\Desktop\\기타\\evtx_list.txt', None, 35452, 'queued', None, None)
2022:06:21 21:20:38.568 [26348] INFO     main.py              proc_cmdline         520 (51, 'C:\\Users\\Admin\\Desktop\\기타\\faq.txt', None, 2284, 'queued', None, None)
2022:06:21 21:20:38.568 [26348] INFO     main.py              proc_cmdline         520 (52, 'C:\\Users\\Admin\\Desktop\\기타\\mongodb_dump_parsers.txt', None, 55004, 'queued', None, None)
2022:06:21 21:20:38.568 [26348] INFO     main.py              proc_cmdline         520 (53, 'C:\\Users\\Admin\\Desktop\\기타\\passbucket_paths.txt', None, 1596, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (54, 'C:\\Users\\Admin\\Desktop\\기타\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt', None, 2364, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (55, 'C:\\Users\\Admin\\Desktop\\기타\\vim.txt', None, 1628, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (56, 'C:\\Users\\Admin\\Desktop\\기타\\복사본 수식(1).xlsx', None, 11948, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (57, 'C:\\Users\\Admin\\Desktop\\기타\\제작일정.xlsx', None, 12332, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (58, 'C:\\Users\\Admin\\Desktop\\기타\\통합 문서2.xlsx', None, 11692, 'queued', None, None)
2022:06:21 21:20:38.569 [26348] INFO     main.py              proc_cmdline         520 (59, 'C:\\Users\\Admin\\Documents\\irisweb.docx', None, 19884, 'queued', None, None)
2022:06:21 21:20:38.570 [26348] INFO     main.py              proc_cmdline         520 (60, 'C:\\Users\\Admin\\Documents\\점수계산.xlsx', None, 13164, 'queued', None, None)
2022:06:21 21:20:38.570 [26348] INFO     main.py              proc_cmdline         522  == Exception list ==

C:\Users\Admin\Desktop\python-for-pc_v2\00.RELEASE>
```

## 개발팁
* vscode에서 다음과 같이 코드를 접어서 보면 개괄적인 코드의 내용을 한눈에 볼 수 있다.
![](/img/vcode_folded_main.png)




# 99. 테스트 절차
## 99.1. ER서버
* iptables -A IN_public_allow -i eth0 -p tcp --dport 8339 -j ACCEPT
* iptables -L
* ifdown eth0
* ifup eth0
* rdate -s time.bora.net
* date
* ip addr | grep inet 

## 99.2. test directory for scanning
* C:\Users

