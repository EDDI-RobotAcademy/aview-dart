import os
import zipfile
from io import BytesIO

import requests
from dotenv import load_dotenv

import dart_fss as dart

load_dotenv()
dartApiKey = os.getenv('DART_API_KEY')

# 조회할 기업 리스트
CORP_LIST = ['삼성전자', 'LG에너지솔루션', 'SK하이닉스', 'NAVER', '삼성바이오로직스', '삼성전자우', '카카오',
             '삼성SDI', '현대차', 'LG화학', '기아', 'POSCO홀딩스', 'KB금융', '카카오뱅크', '셀트리온',
             '신한지주', '삼성물산', '현대모비스', 'SK이노베이션', 'LG전자', '카카오페이', 'SK', '한국전력',
             '크래프톤', '하나금융지주', 'LG생활건강', 'HMM', '삼성생명', '하이브', '두산중공업', 'SK텔레콤',
             '삼성전기', 'SK바이오사이언스', 'LG', 'S-Oil', '고려아연', 'KT&G', '우리금융지주', '대한항공',
             '삼성에스디에스', '현대중공업', '엔씨소프트', '삼성화재', '아모레퍼시픽', 'KT', '포스코케미칼',
             '넷마블', 'SK아이이테크놀로지', 'LG이노텍', '기업은행']


class CorpInfo:
    SEARCH_YEAR = 20240101
    SEARCH_DOC = 'A'  # A : 정기공시, B : 주요사항보고, C : 발행공시, D : 지분공시, E : 기타공시, F : 외부감사관련, G : 펀드공시, H : 자산유동화, I : 거래소공시, J : 공정위공시

    def __init__(self):
        dart.set_api_key(api_key=dartApiKey)
        self.__corpList = dart.get_corp_list()

    def getStockCode(self, searchCorpList):
        corpData = {}
        for name in searchCorpList:
            corp = self.__corpList.find_by_corp_name(name, exactly=True)  # 정확하게 이름으로 검색
            if isinstance(corp, list) and len(corp) > 0:  # 리스트인 경우 첫 번째 항목 선택
                corp = corp[0]

            if corp is not None and corp.stock_code:  # 주식코드가 있는지 확인
                corpData[corp.corp_name] = corp.stock_code

        return corpData

    def getCorpCode(self, searchCorpList):
        corpData = {}
        for name in searchCorpList:
            corp = self.__corpList.find_by_corp_name(name, exactly=True)  # 정확하게 이름으로 검색
            if isinstance(corp, list) and len(corp) > 0:  # 리스트인 경우 첫 번째 항목 선택
                # [TODO] 종목코드 불일치 -> 동일이름이 존재하여 발생함
                corp = corp[0]

            if corp is not None:
                corpData[corp.corp_name] = corp.corp_code

        return corpData

    def getCorpReceiptCode(self, corp_name, corpCode):
        try:
            corpReportList = dart.filings.search(corp_code=corpCode,
                                                 bgn_de=self.SEARCH_YEAR,
                                                 pblntf_ty=self.SEARCH_DOC).report_list

            corpReceiptCode = next((report.rcept_no
                                    for report in corpReportList
                                    if '사업보고서' in report.report_nm), None)

            return corpReceiptCode

        except Exception as e:
            print(f"[ERROR] {corp_name} -> \n {e}")
            pass

    def getCorpDocu(self, corp_name, receipt_code):
        url = 'https://opendart.fss.or.kr/api/document.xml'
        params = {
            'crtfc_key': dartApiKey,
            'rcept_no': receipt_code
        }
        response = requests.get(url, params=params)

        file = BytesIO(response.content)  # 바이너리 스트림형태로 메모리에 저장
        zfile = zipfile.ZipFile(file, 'r')
        corpDocuName = sorted(zfile.namelist(), key=lambda x: len(x))[0]

        with zfile.open(corpDocuName) as f:
            content = f.read()

        return content


if __name__ == '__main__':
    dartApiKey = os.getenv('DART_API_KEY')
    if not dartApiKey:
        raise ValueError('API Key가 준비되어 있지 않습니다!')

    corpInfo = CorpInfo()
    stockCodeDict = {
        '삼성전자': '005930', 'LG에너지솔루션': '373220', 'SK하이닉스': '000660', 'NAVER': '035420',
        '삼성바이오로직스': '207940', '삼성SDI': '006400', 'LG화학': '051910', 'POSCO홀딩스': '005490', 'KB금융': '105560',
        '카카오뱅크': '323410', '신한지주': '055550', '삼성물산': '000830', '현대모비스': '012330', 'SK이노베이션': '096770',
        'LG전자': '066570', '카카오페이': '377300', 'SK': '003600', '크래프톤': '259960', '하나금융지주': '086790',
        'LG생활건강': '051900', 'HMM': '011200', '삼성생명': '032830', '하이브': '352820', 'SK텔레콤': '017670',
        '삼성전기': '009150', 'SK바이오사이언스': '302440', 'LG': '003550', 'S-Oil': '010950', '고려아연': '010130',
        '우리금융지주': '053000', '대한항공': '003490', '삼성에스디에스': '018260', '엔씨소프트': '036570', '아모레퍼시픽': '090430',
        'SK아이이테크놀로지': '361610', 'LG이노텍': '011070', '기업은행': '024110'
    }

    corpReceiptCodeDict = {
        corp_name: corpInfo.getCorpReceiptCode(corp_name, stock_code)
        for corp_name, stock_code in stockCodeDict.items()
    }

    corpDocuDict = {
        corp_name: corpInfo.getCorpDocu(corp_name, receipt_code)
        for corp_name, receipt_code in corpReceiptCodeDict.items()
    }

    print(corpDocuDict)
