import bs4
import requests

from Additions.mark import Mark

class Browser(object):
	def __init__(self):
		self.session = requests.session()
		self.page_content = None
		self.subjects_number = 0

	def login(self, student):
		payload = {'login':student.login, 'password':student.password}
		self.session.post('http://best.yos.kz/cabinet/', data=payload)

	def is_authorized(self):
		return self.page_content.find("div", {"class":"error"}) is None

	def setup_page_content(self):
		response = self.session.get('http://best.yos.kz/cabinet/?module=grades')
		self.page_content = bs4.BeautifulSoup(response.text, "html.parser")

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
