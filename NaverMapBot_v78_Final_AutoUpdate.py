import sys
import os
import time
import random
import math
import requests
import pyperclip
import datetime
import traceback
import subprocess 

# -------------------------------------------------------------------------
# [필수] 구글 시트 연동 라이브러리
# -------------------------------------------------------------------------
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

import undetected_chromedriver as uc
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QGroupBox, QTextEdit, QMessageBox, QSpinBox, 
                             QCheckBox, QSplitter, QProgressBar, QMenu, QFrame, QFileDialog, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMutex, QWaitCondition, QSize, QTimer, QTime
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QAction, QColor, QPalette

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =================================================================================
# [자동 업데이트 설정]
# =================================================================================
CURRENT_VERSION = "1.0.0" # 현재 프로그램 버전
# [중요] 주인님의 GitHub 주소 (version.txt 앞부분까지)
GITHUB_REPO_URL = "https://raw.githubusercontent.com/jeonghun112/NaverMapBot_Update/refs/heads/main" 

def check_update():
    """
    프로그램 시작 시 GitHub에서 최신 버전을 확인하고 업데이트를 수행합니다.
    """
    try:
        # 배포된 실행 파일 환경(frozen)에서만 업데이트 체크
        if getattr(sys, 'frozen', False):
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚀 업데이트 확인 중... ({GITHUB_REPO_URL})")
            
            # 1. 서버 버전 확인
            response = requests.get(f"{GITHUB_REPO_URL}/version.txt", timeout=5)
            
            if response.status_code != 200:
                print(f"   ⚠️ 서버 연결 실패 (Status: {response.status_code}). 업데이트를 건너뜁니다.")
                return

            latest_version = response.text.strip()
            
            if latest_version != CURRENT_VERSION:
                print(f"   ✨ 새 버전({latest_version}) 발견! 업데이트를 시작합니다...")
                
                # 2. 새 실행 파일 다운로드
                exe_url = f"{GITHUB_REPO_URL}/Naver_Ghost_Protocol.exe"
                exe_res = requests.get(exe_url)
                
                if exe_res.status_code == 200:
                    with open("Naver_Ghost_Protocol_new.exe", "wb") as f:
                        f.write(exe_res.content)
                    
                    print("   ✅ 다운로드 완료. 재실행합니다.")

                    # 3. 교체 스크립트 실행 (배치 파일 생성)
                    with open("update.bat", "w") as bat:
                        bat.write(f"""
                        @echo off
                        timeout /t 2 > nul
                        del "Naver_Ghost_Protocol.exe"
                        ren "Naver_Ghost_Protocol_new.exe" "Naver_Ghost_Protocol.exe"
                        start Naver_Ghost_Protocol.exe
                        del "%~f0"
                        """)
                    
                    # 4. 업데이트 배치 실행 후 현재 프로그램 종료
                    subprocess.Popen("update.bat", shell=True)
                    sys.exit()
                else:
                    print("   ❌ 실행 파일 다운로드 실패.")
            else:
                print("   ✅ 현재 최신 버전입니다.")
        else:
            print("   ℹ️ 개발 환경(Python 스크립트)에서는 업데이트를 체크하지 않습니다.")
            
    except Exception as e:
        print(f"   ❌ 업데이트 확인 중 오류 발생: {e}")

# =================================================================================
# [설정] 크롬 경로
# =================================================================================
CHROME_BROWSER_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_DRIVER_PATH = r""  

# =================================================================================
# [워밍업 키워드 라이브러리]
# =================================================================================
DYNAMIC_KEYWORDS = [
    "오늘 날씨", "미세먼지 농도", "현재 교통상황", "뉴스 속보", "환율 조회", 
    "코스피 지수", "미국 증시", "금값 시세", "부동산 시세", "청약 일정",
    "로또 당첨번호", "연금복권", "주말 가볼만한곳", "고속도로 상황", "ktx 예매",
    "넷플릭스 영화 추천", "디즈니플러스 순위", "유튜브 인기동영상", "오늘의 운세", "MBTI 검사",
    "편의점 신상", "스타벅스 메뉴", "배달의민족 쿠폰", "아이폰 최신형", "갤럭시 출시일",
    "남자 코디 추천", "여자 향수 순위", "제주도 맛집", "강릉 여행 코스", "부산 핫플",
    "손흥민 경기 일정", "류현진 등판", "프로야구 순위", "프리미어리그 순위", "최신 영화 순위",
    "아이브", "뉴진스", "방탄소년단", "임영웅 콘서트", "나훈아 티켓팅",
    "맞춤법 검사기", "번역기", "단위 변환", "세계 시간", "타자 연습",
    "건강검진 대상자", "국민연금 예상수령액", "실업급여 신청", "여권 발급", "운전면허 갱신"
]

# =================================================================================
# [디자인] UI 스타일
# =================================================================================
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; color: #ffffff; }
QGroupBox {
    background-color: #252526; border: 1px solid #3e3e42; border-radius: 6px;
    margin-top: 22px; font-family: 'Malgun Gothic'; font-weight: bold; font-size: 13px;
    color: #00acc1; padding-top: 15px;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; background-color: #1e1e1e; }
QLabel { color: #cccccc; font-size: 12px; font-family: 'Malgun Gothic'; font-weight: normal; }
QLineEdit, QSpinBox {
    border: 1px solid #3e3e42; border-radius: 4px; padding: 8px; 
    background-color: #333337; color: #ffffff; font-family: 'Malgun Gothic'; font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus { border: 1px solid #00acc1; background-color: #3e3e42; }
QPushButton { 
    border-radius: 4px; padding: 8px 15px; font-family: 'Malgun Gothic'; font-size: 13px; font-weight: bold; 
    border: none; color: #ffffff; background-color: #454545;
}
QPushButton:hover { background-color: #505050; }
QPushButton#btn_start { background-color: #00796b; font-size: 14px; padding: 10px; }
QPushButton#btn_start:hover { background-color: #00897b; }
QPushButton#btn_pause { background-color: #ff8f00; color: #000000; font-size: 14px; padding: 10px; }
QPushButton#btn_pause:hover { background-color: #ffa000; }
QPushButton#btn_stop { background-color: #c62828; font-size: 14px; padding: 10px; }
QPushButton#btn_stop:hover { background-color: #d32f2f; }
QPushButton#btn_clear { background-color: #546e7a; font-size: 12px; padding: 10px; }
QPushButton#btn_clear:hover { background-color: #607d8b; }
QTableWidget {
    background-color: #1e1e1e; border: 1px solid #3e3e42; gridline-color: #3e3e42; 
    color: #ffffff; font-family: 'Malgun Gothic'; font-size: 13px;
}
QTableWidget::item { padding: 5px; }
QTableWidget::item:selected { background-color: #00acc1; color: #000000; }
QHeaderView::section {
    background-color: #333337; padding: 5px; border: none; border-bottom: 1px solid #00acc1;
    color: #00acc1; font-weight: bold; font-size: 12px;
}
QTextEdit#log_area {
    background-color: #1e1e1e; border: 1px solid #3e3e42; border-radius: 4px;
    color: #80deea; font-family: 'Consolas', 'Malgun Gothic'; font-size: 12px; line-height: 150%;
}
QCheckBox { color: #e0e0e0; font-family: 'Malgun Gothic'; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #666; background: #333; border-radius: 3px; }
QCheckBox::indicator:checked { background-color: #00acc1; border: 1px solid #00acc1; }
"""

class GhostMouse:
    def __init__(self, driver):
        self.driver = driver
        self.action = ActionChains(driver)

    def move_to_element(self, element):
        try:
            self.action.move_to_element(element).perform()
            time.sleep(random.uniform(0.1, 0.3))
        except: pass

    def random_scroll(self, min_px=200, max_px=600):
        try:
            if random.random() < 0.2:
                self.driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
                time.sleep(random.uniform(0.5, 1.0))
            scroll_amount = random.randint(min_px, max_px)
            step = random.randint(30, 70)
            current = 0
            while current < scroll_amount:
                self.driver.execute_script(f"window.scrollBy(0, {step});")
                current += step
                time.sleep(random.uniform(0.01, 0.05)) 
            time.sleep(random.uniform(0.5, 1.2))
        except: pass

class ClipboardTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.verticalHeader().setDefaultSectionSize(35)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste): self.paste_from_clipboard()
        elif event.key() == Qt.Key.Key_Delete: self.delete_selected_rows()
        else: super().keyPressEvent(event)

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        if not text: return
        rows = text.strip().split('\n')
        c_row = max(0, self.currentRow())
        if c_row + len(rows) > self.rowCount(): self.setRowCount(c_row + len(rows))
        for r_idx, row_data in enumerate(rows):
            cols = row_data.split('\t')
            for c_idx, cell_data in enumerate(cols):
                if c_idx < self.columnCount():
                    item = QTableWidgetItem(cell_data.strip())
                    item.setForeground(QColor("#FFFFFF"))
                    self.setItem(c_row + r_idx, c_idx, item)

    def delete_selected_rows(self):
        rows = sorted(set(idx.row() for idx in self.selectedIndexes()), reverse=True)
        for row in rows: self.removeRow(row)

    def show_context_menu(self, pos):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #2D2D2D; color: #FFF; }")
        menu.addAction("붙여넣기", self.paste_from_clipboard)
        menu.addAction("삭제", self.delete_selected_rows)
        menu.exec(self.viewport().mapToGlobal(pos))

class BotWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, config, accounts, keywords):
        super().__init__()
        self.config = config
        self.accounts = accounts 
        self.keywords = keywords
        self.is_running = True
        self.is_paused = False
        self.driver = None
        self.ghost = None
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.current_ip = "Unknown"
        self.rank_checked_today = False 

    def stop(self):
        self.is_running = False
        self.resume()
        if self.driver:
            try: self.driver.quit()
            except: pass
            self.driver = None

    def pause(self):
        self.is_paused = True
        self.log_signal.emit(f"[{self.get_time()}] ⏸️ 일시정지 (PAUSED)")
        self.status_signal.emit("일시정지 중...")

    def resume(self):
        self.is_paused = False
        self.wait_condition.wakeAll()
        self.log_signal.emit(f"[{self.get_time()}] ▶ 작업 재개 (RESUMED)")
        self.status_signal.emit("작업 재개...")

    def check_status(self):
        if self.is_paused:
            self.mutex.lock()
            self.wait_condition.wait(self.mutex)
            self.mutex.unlock()
        if not self.is_running: raise InterruptedError()

    def get_time(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def log(self, msg):
        self.log_signal.emit(f"[{self.get_time()}] {msg}")

    def safe_sleep(self, sec):
        if random.random() < 0.15: 
            delay = random.uniform(1.5, 3.5)
            self.log(f"(사람처럼 멍 때리는 중... +{delay:.1f}초)")
            sec += delay
        end = time.time() + sec
        while time.time() < end:
            self.check_status()
            time.sleep(0.1)

    def get_my_ip(self):
        try: return requests.get("https://api.ipify.org", timeout=5).text.strip()
        except: return "Error"

    def wait_for_ip_change(self):
        self.log("🛡️ [보안] IP 변경 확인 중...")
        self.status_signal.emit("IP 변경 대기 중...")
        start_ip = self.current_ip
        while self.is_running:
            new_ip = self.get_my_ip()
            if new_ip != "Error" and new_ip != start_ip:
                self.log(f" ✅ IP 변경 완료: {new_ip}")
                self.current_ip = new_ip
                return True
            self.safe_sleep(0.5) 
        return False

    def kill_chrome_process(self):
        try:
            self.log("🧹 [시스템] 좀비 프로세스 정리 중...")
            if os.name == 'nt': 
                subprocess.call("taskkill /F /IM chrome.exe /T", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.call("taskkill /F /IM chromedriver.exe /T", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            time.sleep(1)
        except: pass

    def start_browser(self):
        self.kill_chrome_process()
        self.log("🚀 [모바일 모드] 브라우저 실행 중...")
        options = uc.ChromeOptions()
        options.add_argument('--no-first-run')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled') 
        options.add_argument('--disable-gpu')
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        options.add_argument(f'--user-agent={mobile_ua}')
        
        if self.config['incognito']: options.add_argument('--incognito')
        if CHROME_BROWSER_PATH and os.path.exists(CHROME_BROWSER_PATH):
            options.binary_location = CHROME_BROWSER_PATH

        try:
            if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
                self.driver = uc.Chrome(options=options, driver_executable_path=CHROME_DRIVER_PATH, use_subprocess=True)
            else:
                self.driver = uc.Chrome(options=options, use_subprocess=True, version_main=131)

            if not self.driver:
                raise Exception("드라이버 초기화 실패")

            self.ghost = GhostMouse(self.driver)
            try: self.driver.set_window_size(430, 932)
            except: pass
            
            return True
        except Exception as e:
            self.log(f"❌ 브라우저 실행 실패: {e}")
            try:
                self.log("🔄 브라우저 재시도 (버전 자동 매칭)...")
                self.driver = uc.Chrome(options=options, use_subprocess=True)
                self.ghost = GhostMouse(self.driver)
                self.driver.set_window_size(430, 932)
                return True
            except Exception as e2:
                self.log(f"❌ 재시도 실패: {e2}")
                return False

    def perform_login(self, uid, upw):
        self.log(f" 🔑 로그인 시도: {uid}")
        try:
            self.driver.get("https://nid.naver.com/nidlogin.login")
            self.safe_sleep(1.5)
            elem_id = self.driver.find_element(By.ID, "id")
            elem_id.click(); pyperclip.copy(uid); elem_id.send_keys(Keys.CONTROL, 'v'); self.safe_sleep(0.5)
            elem_pw = self.driver.find_element(By.ID, "pw")
            elem_pw.click(); pyperclip.copy(upw); elem_pw.send_keys(Keys.CONTROL, 'v'); self.safe_sleep(0.5)
            self.driver.find_element(By.ID, "log.login").click()
            self.safe_sleep(2)
        except: pass

    def mobile_real_warmup(self):
        self.log("🔥 [리얼 워밍업] 사람처럼 행동하기")
        try:
            self.driver.get("https://m.naver.com")
            self.safe_sleep(random.uniform(2.0, 4.0))
            if random.random() < 0.7:
                try:
                    tabs = ["뉴스", "스포츠", "연예", "경제", "쇼핑", "리빙"]
                    target_tab_text = random.choice(tabs)
                    self.log(f"   -> 심심해서 '{target_tab_text}' 구경 중")
                    tab_elem = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{target_tab_text}')]/ancestor::a")
                    tab_elem.click()
                    self.safe_sleep(random.uniform(2.5, 5.0))
                    for _ in range(random.randint(2, 5)):
                        self.ghost.random_scroll(100, 400)
                        self.safe_sleep(0.8)
                    self.driver.get("https://m.naver.com")
                    self.safe_sleep(1.5)
                except: pass

            keyword = random.choice(DYNAMIC_KEYWORDS)
            self.log(f"   -> 워밍업 검색: {keyword}")
            try:
                search_btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, "MM_SEARCH_FAKE")))
                search_btn.click()
                self.safe_sleep(0.8)
            except: pass
            
            real_input = self.driver.find_element(By.ID, "query")
            for char in keyword:
                real_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.4))
            
            time.sleep(0.5) 
            real_input.send_keys(Keys.ENTER)
            self.safe_sleep(3)
            
            for _ in range(random.randint(3, 6)):
                self.ghost.random_scroll(200, 500)
                self.safe_sleep(random.uniform(1.0, 2.0))
            
            if random.random() < 0.6:
                try:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, "div.api_txt_lines")
                    if posts:
                        target = random.choice(posts[:3])
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                        time.sleep(1)
                        target.click()
                        self.log("   -> 게시글 읽는 척 체류...")
                        self.safe_sleep(random.uniform(5.0, 10.0))
                        self.ghost.random_scroll(100, 300)
                        self.driver.back()
                        self.safe_sleep(2)
                except: pass
            
            try:
                top_search = self.driver.find_element(By.ID, "nx_query")
                top_search.click()
                top_search.clear()
                self.safe_sleep(1)
            except: 
                self.driver.get("https://m.naver.com")
                self.safe_sleep(2)
        except Exception as e:
            self.log(f" ⚠️ 워밍업 패스: {e}")

    def check_and_log_rank(self):
        if not GOOGLE_SHEETS_AVAILABLE:
            self.log("⚠️ 구글 시트 라이브러리 미설치로 패스")
            return
        
        if not self.config.get('sheet_json') or not self.config.get('sheet_name'):
            self.log("⚠️ 구글 시트 설정 누락으로 패스")
            return

        self.log("📊 [일일 순위 체크] 구글 시트 기록 시작...")
        
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.config['sheet_json'], scope)
            client = gspread.authorize(creds)
            
            sheet_input = self.config['sheet_name']
            if "docs.google.com" in sheet_input:
                sheet = client.open_by_url(sheet_input).sheet1
            else:
                sheet = client.open(sheet_input).sheet1
            
            if not sheet.row_values(1):
                sheet.append_row(["날짜", "시간", "키워드", "순위", "타겟업체"])

            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cur_time = datetime.datetime.now().strftime("%H:%M:%S")

            for keyword in self.keywords:
                self.log(f"   📊 '{keyword}' 순위 확인 중...")
                rank = self.get_rank_for_keyword(keyword, self.config['target_name'])
                
                rank_str = f"{rank}위" if rank > 0 else "순위 밖"
                self.log(f"   ✅ 결과: {rank_str}")
                
                sheet.append_row([today, cur_time, keyword, rank_str, self.config['target_name']])
                self.safe_sleep(3)
            
            self.rank_checked_today = True
            self.log("📊 [순위 체크] 완료 및 저장됨")

        except Exception as e:
            self.log(f"❌ 구글 시트 연동 오류: {e}")

    def get_rank_for_keyword(self, keyword, target_name):
        self.driver.get("https://m.naver.com")
        self.safe_sleep(2)
        try:
            self.driver.find_element(By.ID, "MM_SEARCH_FAKE").click()
            input_box = self.driver.find_element(By.ID, "query")
            input_box.send_keys(keyword)
            input_box.send_keys(Keys.ENTER)
            self.safe_sleep(3)

            found_more = False
            more_xpaths = [
                f"//a[contains(., '{keyword} 더보기')]",
                "//div[contains(@class, 'place_section')]//a[contains(@class, 'more')]"
            ]
            for xpath in more_xpaths:
                try:
                    btns = self.driver.find_elements(By.XPATH, xpath)
                    for btn in btns:
                        if btn.is_displayed() and "펼쳐서" not in btn.text:
                            btn.click()
                            found_more = True
                            break
                except: pass
                if found_more: break
            
            if not found_more: return -1 
            self.safe_sleep(3)

            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), '목록보기')]").click()
                self.safe_sleep(2)
            except: pass

            target_clean = target_name.replace(" ", "")
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()

            for scroll_cnt in range(50): 
                items = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'UEzoS')] | //div[contains(@class, 'place_bluelink')]")
                
                for idx, item in enumerate(items):
                    try:
                        if target_clean in item.text.replace(" ", ""):
                            return idx + 1 
                    except: pass
                
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
            
            return 0 

        except: return -1

    def search_and_find_place(self, keyword):
        self.log(f" 🔎 통합검색 시작: {keyword}")
        try:
            try: input_box = self.driver.find_element(By.ID, "nx_query")
            except:
                try:
                    self.driver.find_element(By.ID, "MM_SEARCH_FAKE").click()
                    input_box = self.driver.find_element(By.ID, "query")
                except:
                    self.driver.get("https://m.naver.com")
                    self.safe_sleep(2)
                    self.driver.find_element(By.ID, "MM_SEARCH_FAKE").click()
                    input_box = self.driver.find_element(By.ID, "query")
            
            input_box.click()
            input_box.clear()
            for char in keyword:
                input_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            try:
                search_btn = self.driver.find_element(By.CSS_SELECTOR, "button.sch_btn_search")
                search_btn.click()
            except:
                input_box.send_keys(Keys.ENTER)
            self.safe_sleep(3)
            
            self.log(f" 🕵️ '{keyword}' 더보기 탐색 중...")
            
            more_xpaths = [
                f"//a[contains(., '{keyword} 더보기')]",
                f"//span[contains(text(), '{keyword} 더보기')]/ancestor::a",
                "//div[contains(@class, 'place_section')]//a[contains(@class, 'more')]",
                "//div[contains(@class, 'place_section')]//a[@role='button' and contains(., '더보기')]",
                "//div[contains(@class, 'api_more_bundle')]//a",
            ]

            for attempt in range(3):
                if attempt > 0:
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    self.safe_sleep(2)

                found_btn = False
                for _ in range(15): 
                    for xpath in more_xpaths:
                        try:
                            btns = self.driver.find_elements(By.XPATH, xpath)
                            for btn in btns:
                                if btn.is_displayed():
                                    if "펼쳐서" in btn.text: continue 

                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    time.sleep(1.0)
                                    self.driver.execute_script("arguments[0].style.border='3px solid red'", btn)
                                    clicked_text = btn.text.strip()
                                    self.human_click(btn)
                                    
                                    self.log(f"   ✅ 버튼 클릭 성공: {clicked_text}")
                                    self.safe_sleep(4) 
                                    return True 
                        except: pass
                    
                    if found_btn: break
                    self.ghost.random_scroll(min_px=300, max_px=600)
                    self.safe_sleep(0.5) 

            self.log(" ❌ '더보기' 버튼 찾기 실패")
            return False
            
        except Exception as e:
            self.log(f" ❌ 검색 오류: {e}")
            return False

    def find_target_in_place_list(self, target_name):
        self.log("📱 [플레이스 리스트] 진입 확인 중...")
        
        try:
            list_view_xpaths = [
                "//span[contains(text(), '목록보기')]",
                "//a[contains(., '목록보기')]",
                "//button[contains(., '목록보기')]"
            ]
            for xpath in list_view_xpaths:
                try:
                    list_btn = self.driver.find_element(By.XPATH, xpath)
                    if list_btn.is_displayed():
                        self.log("   🗺️ 지도 화면 감지 -> [목록보기] 클릭")
                        list_btn.click()
                        self.safe_sleep(2.5) 
                        break
                except: pass
        except: pass

        self.log("   📜 천천히 리스트 스캔 시작 (Physical Scroll)...")
        target_clean = target_name.replace(" ", "")
        
        scroll_limit = 500 
        last_height = 0
        no_change_count = 0
        
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
        except: pass

        for i in range(scroll_limit):
            self.check_status()
            
            try:
                items = self.driver.find_elements(By.XPATH, """
                    //div[contains(@class, 'place_bluelink')] | 
                    //span[contains(@class, 'place_bluelink')] | 
                    //span[contains(@class, 'YwYLL')] |
                    //div[contains(@class, 'YouOG')] |
                    //div[contains(@class, 'TIT')] 
                """)
                
                for item in items:
                    try:
                        name = item.text.replace(" ", "")
                        if target_clean in name:
                            self.log(f" 🎯 타겟 발견! [{item.text}]")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                            self.driver.execute_script("arguments[0].style.border='3px solid red'", item)
                            time.sleep(1.5)
                            item.click()
                            return True
                    except: pass
            except: pass
            
            try:
                for _ in range(random.randint(5, 8)):
                    body.send_keys(Keys.ARROW_DOWN)
                    time.sleep(random.uniform(0.15, 0.4))
                
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(random.uniform(1.5, 2.5))
                
            except Exception as e:
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2.0)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                no_change_count += 1
                self.log(f"   ⚠️ 높이 변화 없음 ({no_change_count}/10)")
                
                if no_change_count > 10:
                    self.log(" 🔚 정말 더 이상 데이터가 없습니다. (탐색 종료)")
                    break
                
                if no_change_count % 3 == 0:
                     self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                     time.sleep(2)
                else:
                    body.send_keys(Keys.END)
                    time.sleep(2)
            else:
                no_change_count = 0
                
            last_height = new_height
            
            if i % 3 == 0: self.log(f"   ⬇️ 리스트 내리는 중... ({i}회)")

        self.log(" ❌ 리스트 끝까지 탐색했으나 타겟 없음")
        return False

    def human_click(self, element):
        try:
            self.ghost.move_to_element(element)
            self.driver.execute_script("arguments[0].click();", element)
        except: pass

    def run(self):
        self.current_ip = self.get_my_ip()
        self.log(f"📡 현재 IP: {self.current_ip}")
        if self.config['auto_ip']: self.wait_for_ip_change()
        
        # [수정] 프로그램 시작 직후 업데이트 확인
        check_update()

        if not self.start_browser():
            self.log("❌ 브라우저 실행 실패로 작업 종료")
            self.finished_signal.emit()
            return

        try:
            target_loop = self.config['loop_count']
            loop_cnt = 1
            
            while True:
                if target_loop > 0 and loop_cnt > target_loop:
                    self.log(f"✅ 설정된 {target_loop}회 반복 완료. 작업을 종료합니다.")
                    break

                now = datetime.datetime.now()
                if now.hour == 9 and not self.rank_checked_today:
                    wait_min = random.randint(0, 30)
                    self.log(f"⏰ [순위 체크 대기] 9시 감지. {wait_min}분 후 시작합니다...")
                    self.safe_sleep(wait_min * 60)
                    self.check_and_log_rank()
                
                if now.hour == 0 and self.rank_checked_today:
                    self.rank_checked_today = False

                self.log(f"\n📌 [루프] {loop_cnt}회차 진행 중...")
                
                if self.config['auto_ip'] and loop_cnt > 1: self.wait_for_ip_change()

                for acc in self.accounts:
                    user_id = acc.get('id', 'Guest')
                    user_pw = acc.get('pw', '')
                    self.driver.get("about:blank")
                    self.driver.delete_all_cookies()

                    if user_id == 'Guest' or not user_pw: self.log(f"\n👤 [Guest] 모드")
                    else: self.log(f"\n👤 [User] {user_id}"); self.perform_login(user_id, user_pw)

                    if self.config['warmup']: self.mobile_real_warmup()
                    else: self.driver.get("https://m.naver.com")

                    for keyword in self.keywords:
                        self.check_status()
                        
                        if not self.search_and_find_place(keyword): continue
                        
                        if self.find_target_in_place_list(self.config['target_name']):
                            self.log(" 🏠 상세 페이지 체류 시작")
                            self.safe_sleep(3)
                            self.mobile_stay_action()
                        else:
                            self.log(f" ❌ '{keyword}' 실패")

                        self.safe_sleep(random.randint(5, 10))

                loop_cnt += 1
                self.safe_sleep(5)

        except InterruptedError: self.log("🛑 중단됨")
        except Exception as e: 
            self.log(f"❌ 오류: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass
            self.finished_signal.emit(); self.status_signal.emit("작업 종료")

    def mobile_stay_action(self):
        stay_time = random.randint(self.config['min_time'], self.config['max_time'])
        self.log(f" ⏳ {stay_time}초 체류...")
        end = time.time() + stay_time
        safe_tabs = ["홈", "소식", "리뷰", "사진"]
        while time.time() < end:
            self.check_status()
            if random.random() < 0.4:
                try:
                    tab = random.choice(safe_tabs)
                    xpath = f"//span[text()='{tab}']/ancestor::a"
                    elems = self.driver.find_elements(By.XPATH, xpath)
                    for e in elems:
                        if e.is_displayed():
                            self.driver.execute_script("arguments[0].click();", e)
                            self.log(f" 👆 {tab} 탭 터치")
                            self.safe_sleep(3)
                            break
                except: pass
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
            self.safe_sleep(random.randint(3, 6))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NAVER MAP BOT v78.0 (Final Fix + Auto Update)")
        self.resize(1200, 900)
        self.setStyleSheet(STYLESHEET)
        
        # [신규] 프로그램 시작 시 업데이트 확인 (UI 뜨기 전 체크)
        check_update()
        
        self.init_ui()
        
        self.rank_timer = QTimer(self)
        self.rank_timer.timeout.connect(self.check_time_for_rank)
        self.rank_timer.start(60000)
        
        # 아이콘 적용 (2번 컴퓨터에서도 되도록)
        if os.path.exists("my_new_icon.ico"):
            self.setWindowIcon(QIcon("my_new_icon.ico"))

    def check_time_for_rank(self):
        pass

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)
        header = QLabel("GHOST PROTOCOL : FINAL FIX")
        header.setStyleSheet("font-size: 26px; font-weight: bold; color: #00acc1; margin: 15px 0; font-family: 'Malgun Gothic';")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(header)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); left_layout.setSpacing(15)
        
        gb_target = QGroupBox("작업 설정"); v_target = QVBoxLayout(); v_target.setSpacing(10)
        self.input_target = QLineEdit("법무법인 진심파트너스 부산지점")
        h_time = QHBoxLayout()
        self.spin_min = QSpinBox(); self.spin_min.setValue(40); self.spin_min.setRange(10, 3600)
        self.spin_max = QSpinBox(); self.spin_max.setValue(80); self.spin_max.setRange(10, 3600)
        h_time.addWidget(QLabel("최소 체류:")); h_time.addWidget(self.spin_min)
        h_time.addWidget(QLabel("최대 체류:")); h_time.addWidget(self.spin_max)
        
        h_loop = QHBoxLayout()
        self.spin_loop = QSpinBox()
        self.spin_loop.setRange(0, 9999)
        self.spin_loop.setValue(0)
        self.spin_loop.setToolTip("0으로 설정하면 무한 반복합니다.")
        h_loop.addWidget(QLabel("반복 횟수 (0=무한):")); h_loop.addWidget(self.spin_loop)

        self.chk_incognito = QCheckBox("시크릿 모드 (필수)"); self.chk_incognito.setChecked(True)
        self.chk_warmup = QCheckBox("리얼 워밍업 (랜덤 패턴)"); self.chk_warmup.setChecked(True)
        self.chk_auto_ip = QCheckBox("IP 변경 대기"); self.chk_auto_ip.setChecked(True)
        
        v_target.addWidget(QLabel("타겟 업체명:")); v_target.addWidget(self.input_target)
        v_target.addLayout(h_time)
        v_target.addLayout(h_loop)
        v_target.addWidget(self.chk_incognito); v_target.addWidget(self.chk_warmup)
        v_target.addWidget(self.chk_auto_ip)
        gb_target.setLayout(v_target)
        
        gb_rank = QGroupBox("구글 시트 순위 체크 (09시)"); v_rank = QVBoxLayout()
        self.input_json = QLineEdit(); self.input_json.setPlaceholderText("JSON 키 파일 경로")
        self.btn_json = QPushButton("파일 찾기"); self.btn_json.clicked.connect(self.load_json)
        h_json = QHBoxLayout(); h_json.addWidget(self.input_json); h_json.addWidget(self.btn_json)
        
        self.input_sheet = QLineEdit("https://docs.google.com/spreadsheets/d/1rwY4bZuFbURLG8SX3fZLXIKdr8dybCeF3HON7dqxTlU/edit#gid=0")
        self.input_sheet.setPlaceholderText("구글 시트 이름 또는 URL 입력")
        
        v_rank.addLayout(h_json); v_rank.addWidget(self.input_sheet)
        gb_rank.setLayout(v_rank)

        gb_data = QGroupBox("데이터 입력"); v_data = QVBoxLayout()
        gb_data.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 

        self.table_kwd = ClipboardTable(15, 1); self.table_kwd.horizontalHeader().setVisible(False)
        self.table_kwd.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table_acc = ClipboardTable(10, 2); self.table_acc.setHorizontalHeaderLabels(["ID", "PW"])
        self.table_acc.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_data.addWidget(QLabel("검색 키워드 (Ctrl+V):"))
        v_data.addWidget(self.table_kwd)
        v_data.addWidget(QLabel("계정 목록:"))
        v_data.addWidget(self.table_acc)
        gb_data.setLayout(v_data)

        left_layout.addWidget(gb_target); left_layout.addWidget(gb_rank); left_layout.addWidget(gb_data)
        
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
        
        self.btn_cls_kwd = QPushButton("키워드 삭제"); self.btn_cls_kwd.setObjectName("btn_clear")
        self.btn_cls_kwd.clicked.connect(lambda: self.table_kwd.setRowCount(0) or self.table_kwd.setRowCount(15))
        
        self.btn_cls_acc = QPushButton("계정 삭제"); self.btn_cls_acc.setObjectName("btn_clear")
        self.btn_cls_acc.clicked.connect(lambda: self.table_acc.setRowCount(0) or self.table_acc.setRowCount(10))
        
        self.btn_start = QPushButton("작업 시작"); self.btn_start.setObjectName("btn_start"); self.btn_start.clicked.connect(self.start)
        self.btn_pause = QPushButton("일시 정지"); self.btn_pause.setObjectName("btn_pause"); self.btn_pause.clicked.connect(self.pause); self.btn_pause.setEnabled(False)
        self.btn_stop = QPushButton("작업 종료"); self.btn_stop.setObjectName("btn_stop"); self.btn_stop.clicked.connect(self.stop); self.btn_stop.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start, 2)
        btn_layout.addWidget(self.btn_pause, 1)
        btn_layout.addWidget(self.btn_stop, 1)
        btn_layout.addWidget(self.btn_cls_kwd, 1)
        btn_layout.addWidget(self.btn_cls_acc, 1)
        
        left_layout.addLayout(btn_layout)

        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.status_label = QLabel("시스템 대기 중"); self.status_label.setStyleSheet("color: #00acc1; font-weight: bold; font-size: 14px;"); self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.log_area = QTextEdit(); self.log_area.setObjectName("log_area"); self.log_area.setReadOnly(True)
        right_layout.addWidget(self.status_label); right_layout.addWidget(self.log_area)
        
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 5) 
        main_splitter.setStretchFactor(1, 5) 
        
        layout.addWidget(main_splitter)

    def load_json(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'JSON 키 파일 선택', '', 'JSON Files (*.json)')
        if fname: self.input_json.setText(fname)

    def log(self, msg): self.log_area.append(msg); sb = self.log_area.verticalScrollBar(); sb.setValue(sb.maximum())
    def update_status(self, msg): self.status_label.setText(msg)
    
    def start(self):
        kw = [self.table_kwd.item(i, 0).text().strip() for i in range(self.table_kwd.rowCount()) if self.table_kwd.item(i, 0) and self.table_kwd.item(i, 0).text().strip()]
        if not kw: QMessageBox.warning(self, "경고", "키워드 입력 필요"); return
        
        final_acc = []
        for i in range(self.table_acc.rowCount()):
            uid = self.table_acc.item(i, 0).text().strip() if self.table_acc.item(i, 0) else ""
            upw = self.table_acc.item(i, 1).text().strip() if self.table_acc.item(i, 1) else ""
            if uid: final_acc.append({'id': uid, 'pw': upw})
        if not final_acc: final_acc = [{'id': 'Guest', 'pw': ''}]

        cfg = {
            'target_name': self.input_target.text().strip(), 
            'min_time': self.spin_min.value(), 
            'max_time': self.spin_max.value(),
            'loop_count': self.spin_loop.value(), 
            'incognito': self.chk_incognito.isChecked(), 
            'warmup': self.chk_warmup.isChecked(),
            'auto_ip': self.chk_auto_ip.isChecked(),
            'sheet_json': self.input_json.text().strip(),
            'sheet_name': self.input_sheet.text().strip()
        }
        
        self.worker = BotWorker(cfg, final_acc, kw)
        self.worker.log_signal.connect(self.log); self.worker.status_signal.connect(self.update_status); self.worker.finished_signal.connect(self.finish)
        self.worker.start(); self.btn_start.setEnabled(False); self.btn_pause.setEnabled(True); self.btn_stop.setEnabled(True); self.status_label.setText("실행 중...")

    def pause(self):
        if self.worker:
            if self.worker.is_paused: self.worker.resume(); self.btn_pause.setText("일시 정지")
            else: self.worker.pause(); self.btn_pause.setText("작업 재개")
    def stop(self):
        if hasattr(self, 'worker'): self.worker.stop(); self.status_label.setText("중지 중...")
    def finish(self):
        self.btn_start.setEnabled(True); self.btn_pause.setEnabled(False); self.btn_stop.setEnabled(False)
        self.log("--- 작업 종료 ---"); self.status_label.setText("대기 상태")

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Malgun Gothic", 10)); win = MainWindow(); win.show(); sys.exit(app.exec())