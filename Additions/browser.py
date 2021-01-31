import bs4
from mechanicalsoup import StatefulBrowser

from Additions.mark import Mark

class Browser(object):
	def __init__(self):
		self.browser = StatefulBrowser()
		self.page_content = None
		self.subjects_number = 0

	def login(self, student):
		self.browser.open("http://best.yos.kz/cabinet/")
		self.browser.select_form('form[method="post"]')
		self.browser['login'] = student.login
		self.browser['password'] = student.password

		self.browser.submit_selected()

	def is_authorized(self):
		return bs4.BeautifulSoup(str(self.browser.get_current_page()), "html.parser").find("div", {"class":"error"}) is None

	def setup_page_content(self):
		self.browser.open_relative('http://best.yos.kz/cabinet/?module=grades')
		self.page_content = bs4.BeautifulSoup(str(self.browser.get_current_page()), "html.parser")

	def get_student_name(self):
		return self.page_content.find_all("div", {"class":"top-panel-name"})[0].getText()

	def setup_student_subjects_number(self):
		subjects_number = 0
		while True:
			try:
				float(self.page_content.find_all("tr", {"class":"cl-row"})[subjects_number].find_all('td')[0].getText())
				subjects_number += 1
			except ValueError:
				break

		self.subjects_number = subjects_number

	def get_student_marks(self):
		self.setup_student_subjects_number()

		marks = []
		i = 0
		for tr in self.page_content.find_all("tr", {"class":"cl-row"})[self.subjects_number:self.subjects_number * 2]:
			mark = Mark(self.page_content.find_all("tr", {"class":"cl-row"})[i].find_all('td')[1].getText())
			i += 1
			for td in tr.find_all('td'):
				if td.find('span') is not None and len(td.find('span')) != 0:
					mark.add_mark(td.find('span').getText())
			marks.append(mark)

		return marks
