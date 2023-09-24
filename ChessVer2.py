try:
	from selenium import webdriver
	from selenium.webdriver.common.by import By
	from selenium.webdriver.common.keys import Keys
	from selenium.webdriver import ActionChains
	from win32com.client import Dispatch
	import os, re, time, subprocess, numpy as np, json
	import requests
except:
	import os
	# Cài đặt thư viện cần thiết
	os.system('py -m pip install requests selenium==3.14.0 pywin32 numpy==1.24.3')


class AutoChess(object):
	"""docstring for ClassName"""
	def __init__(self, username, password, time=100, isStockFishEngine=False, stockfish_path=""):
		self.account_id = username
		self.account_password = password
		self.time = time
		self.isStockFishEngine = isStockFishEngine
		self.stockfish_path = stockfish_path
		
		options = webdriver.ChromeOptions()
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument('--ignore-certificate-errors')
		options.add_argument('--log-level=3')
		options.add_experimental_option("excludeSwitches", ["enable-logging"])
		options.add_argument('--no-sandbox')

		try:
			self.driver = webdriver.Chrome(executable_path='./chromedriver/chromedriver.exe', options=options)
		except:
			print('No installation "chromedriver" found.')
			self.install_chromedriver(self.check_chrome_version())
			self.driver = webdriver.Chrome(executable_path='./chromedriver/chromedriver.exe', options=options)
			# ...

	def login(self):
		self.driver.get("https://www.chess.com/login_and_go?returnUrl=https://www.chess.com/home")

		# find the username and password fields
		username = self.driver.find_element_by_id("username")
		password = self.driver.find_element_by_id("password")

		# enter your username and password
		username.send_keys(self.account_id)
		time.sleep(1)
		password.send_keys(self.account_password)

		# submit the form
		time.sleep(1)
		password.send_keys(Keys.RETURN)

	def Solve(self, FEN):
		response = requests.get(f'https://minhhoang.info/api/chess/getbestmove?fen={FEN}&time={self.time}')
	
		if response.status_code == 200:
			return response.json()['bestMove']

		else:
			return None

	def Solve_stockfish(self, FEN):
		stockfish_path = self.stockfish_path
		cmd = [stockfish_path]

		stockfish = subprocess.Popen(
			cmd, universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE
		)

		stockfish.stdin.write("ucinewgame\n")
		stockfish.stdin.flush()

		stockfish.stdin.write(f"position fen {FEN}\n")
		stockfish.stdin.flush()

		stockfish.stdin.write(f"go movetime {self.time}\n")
		stockfish.stdin.flush()

		best_move = None

		for line in stockfish.stdout:
			if line.startswith("bestmove"):
				best_move = line.split()[1]
				break

		stockfish.stdin.write("quit\n")
		stockfish.stdin.flush()
		stockfish.wait()

		return best_move 

	def get_codeFEN(self, matrix):
		FEN = ''
		count_FEN = 0
		for i in range(7, -1, -1):
			for j in range(0, 8, 1):
				if matrix[i][j] == ' ':
					count_FEN += 1
					if count_FEN == 8:
						FEN += str(count_FEN)
						count_FEN = 0
				else:
					if count_FEN != 0:
						FEN += str(count_FEN)
					count_FEN = 0
					piece = [chess for chess in matrix[i][j].split(' ') if len(chess) == 2][0]
					if piece[0] == 'w':
						FEN += piece[1].upper()
					else:
						FEN += piece[1]
			if count_FEN != 0:
				FEN += str(count_FEN)
				count_FEN = 0
			if i != 0:
				FEN += '/'
		return FEN

	def getMatrixBoard(self):
		try:
			# Find the elements representing the chess pieces
			pieces = self.driver.find_elements(by=By.CSS_SELECTOR, value=("wc-chess-board .piece"))
			if not pieces:
				return []

			# create matrix 8 8 with numpy
			matrix = np.empty((8, 8), dtype=object)
			matrix[:] = " "

			for piece in pieces:
				chess_piece = [ch for ch in piece.get_attribute('outerHTML').replace('"','').split(' ') if 'square-' in ch or len(ch) == 2]
				if not chess_piece:
					continue
				square = [chess for chess in chess_piece if 'square-' in chess][0][-2:]
				if not square:
					continue
				pos = [chess for chess in chess_piece if len(chess) == 2]
				if not pos:
					continue
				matrix[8-int(square[1])][8-int(square[0])] = ' '.join(chess_piece)

			# print(matrix)
			return matrix
		except:
			return None

	def gameHint(self, side):
		count = 1 if side == 'black' else 0
		while True:
			matrix = self.getMatrixBoard()
			if not list(matrix):
				return None

			if count % 2 != 0:
				# move
				if side == 'black':
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' b')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' b'))

				else:
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' w')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' w'))

				print(f'best move: {move}')

			if self.check_turn(self.getMatrixBoard()):
				break

			count += 1 

	def solvePuzzles(self):
		while True:
			side = ''
			try:
				gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "Black to Move"]')
				side = 'black'
				print("You're Black")
			except:
				try:
					gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "Black to move"]')
					side = 'black'
					print("You're Black")
				except:
					try:
						gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "White to Move"]')
						side = 'white'
						print("You're White")
					except:
						try:
							gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "White to move"]')
							side = 'white'
							print("You're White")
						except:
							return None

			try:
				time.sleep(1)
				matrix = self.getMatrixBoard()
				if not list(matrix):
					return None

				# move
				if side == 'black':
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' b')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' b'))
					step_x =  (ord(move[2])-96) - (ord(move[0])-96)
					step_y = int(move[3]) - int(move[1])

				else:
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' w')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' w'))
					step_x =  (ord(move[0])-96) - (ord(move[2])-96)
					step_y = int(move[1]) - int(move[3])

				print(f'best move: {move}')

				element = self.driver.find_element(By.XPATH, f'//*[@class="piece {matrix[int(move[1])-1][ord(move[0])-97]}"]')
				ActionChains(self.driver).drag_and_drop_by_offset(element, step_x*(-80), step_y*(80)).perform()
			except:
				return None

			if self.check_turn(self.getMatrixBoard()):
				break

	def gameplay(self, side):
		while True:
			matrix = self.getMatrixBoard()
			if not list(matrix):
				return None

			try:
				# move
				if side == 'black':
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' b')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' b'))
					step_x =  (ord(move[2])-96) - (ord(move[0])-96)
					step_y = int(move[3]) - int(move[1])

				else:
					# Rotate the matrix by 90 degrees
					matrix = np.fliplr(np.flipud(matrix))

					move = str(self.Solve(self.get_codeFEN(matrix)+' w')) if self.isStockFishEngine == False else str(self.Solve_stockfish(self.get_codeFEN(matrix)+' w'))
					step_x =  (ord(move[0])-96) - (ord(move[2])-96)
					step_y = int(move[1]) - int(move[3])

				print(f'best move: {move}')
				
				element = self.driver.find_element(By.XPATH, f'//*[@class="piece {matrix[int(move[1])-1][ord(move[0])-97]}"]')
				ActionChains(self.driver).drag_and_drop_by_offset(element, step_x*(-70), step_y*(70)).perform()
			except:
				return None

			if self.check_turn(self.getMatrixBoard()):
				break

	def isGameOver(self):
		try:
			gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "You Won!"]')
			print("Game Over")
			return True
		except:
			try:
				gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "Game Aborted"]')
				print("Game Over")
				return True
			except:
				try:
					gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "White Won"]')
					print("Game Over")
					return True
				except:
					try:
						gameOver = self.driver.find_element(By.XPATH, '//*[ text() = "Black Won"]')
						print("Game Over")
						return True
					except:
						return False

	def check_turn(self, last_matrix):
		while str(self.getMatrixBoard()) == str(last_matrix):
			if self.isGameOver():
				return True
		return False

	def isGameStart(self):
		count_dot = 0
		getSide = self.driver.find_elements(by=By.CSS_SELECTOR, value=(".live-game-start-component span a"))
		while not getSide:
			print(f'Waiting for game {count_dot*"."}', end='\r')
			time.sleep(1)
			if count_dot == 3:
				count_dot = 0
			else:
				count_dot += 1
			getSide = self.driver.find_elements(by=By.CSS_SELECTOR, value=(".live-game-start-component span a"))

		if getSide[len(getSide)-2].get_attribute('innerHTML') == self.account_id:
			side = 'white'
		else:
			side = 'black'
		
		print(f'you are {side}')
		return side

	def check_chrome_version(self):
		paths = [r"C:/Program Files/Google/Chrome/Application/chrome.exe",
				r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"]
		parser = Dispatch("Scripting.FileSystemObject")
		# Get the version of Google Chrome installed on your machine
		for path in paths:
			try:
				version = parser.GetFileVersion(path)
				return version
			except:
				continue

	def find_chorme_version(self):
		# Send a GET request to the website
		response = requests.get("https://chromedriver.chromium.org/downloads")
		# Get the content of the response
		content = response.content.decode("utf-8")
		# Extract the available versions of ChromeDriver from the content using regex
		versions = re.findall(r'ChromeDriver \d+\.\d+\.\d+.\d+', content)
		# Remove the prefix "ChromeDriver " from the versions
		versions = [version.replace("ChromeDriver ", "") for version in versions]
		return versions

	def find_chorme_testing_version(self, chrome_version):
		rs = requests.get('https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json').json()
		version_ls = [r for r in rs['versions'] if chrome_version.split('.')[0] in r['version']]
		return [dl for dl in version_ls[len(version_ls)-1]['downloads']['chromedriver'] if dl['platform'] == 'win32'][0]['url']

	def install_chromedriver(self, chrome_version):
		print('Chrome version: '+chrome_version)
		if chrome_version:
			if int(chrome_version.split('.')[0]) < 115:
				for ver in self.find_chorme_version():
					if chrome_version.split('.')[0] == ver.split('.')[0]:
						# Install the compatible version of ChromeDriver for the installed version of Google Chrome
						os.system(f"curl https://chromedriver.storage.googleapis.com/{ver}/chromedriver_win32.zip -o chromedriver.zip")
						subprocess.run(["powershell.exe", "-Command", "Expand-Archive chromedriver.zip -Force"])
						os.remove("chromedriver.zip")
						print(f"ChromeDriver version {ver} installed.")
						return None
			else:
				# Install the compatible version of ChromeDriver for the installed version of Google Chrome
				os.system(f"curl {self.find_chorme_testing_version(chrome_version)} -o chromedriver.zip")
				subprocess.run(["powershell.exe", "-Command", "Expand-Archive chromedriver.zip -Force"])
				os.remove("chromedriver.zip")
				subprocess.run(["powershell.exe", "-Command", f"Move-Item -Path './chromedriver/chromedriver-win32/*' -Destination './chromedriver'"])
				subprocess.run(["powershell.exe", "-Command", "Remove-Item -Path './chromedriver/chromedriver-win32' -Force -Recurse"])
				print(f"ChromeDriver version {chrome_version} installed.")
				return None
		else:
			print("No chromedriver was found that matches your google version")


# load config
import json

with open('./config.json') as f:
    config = json.load(f)

account = config["account"]
setting = config["chess"]


# Run
chess = AutoChess(account["username"], account["password"], setting["go_move_time"], setting["use_local_engine"], setting["path"])
chess.login()
while True:
	print('==============================')
	print('1. Normal mode')
	print('2. Hint mode')
	print('3. Solve Puzzles')
	print('4. Free mode')
	while True:
		try:
			option = int(input('You chose: '))
			break
		except:
			print('1')

	if option == 1:
		side = chess.isGameStart()
		chess.gameplay(side)
	elif option == 2:
		side = chess.isGameStart()
		chess.gameHint(side)
	elif option == 3:
		chess.solvePuzzles()
	elif option == 4:
		side = input('chose your side: ')
		chess.gameplay(side)