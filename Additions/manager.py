import statistics

from Additions.browser import Browser
from Additions.student import Student
from Utils import bcolors
from Utils.bcolors import BColors
from Utils.table import Table

class Manager(object):
	def __init__(self, student: Student):
		self.student = student
		self.browser = Browser()
		self.view = None

		self.browser.login(self.student)
		self.browser.setup_page_content()
		if not self.browser.is_authorized():
			self.error_auth()
			exit()

		self.setup_student_name()
		self.setup_student_marks()
		self.setup_view()

	def setup_student_name(self):
		self.student.name = self.browser.get_student_name()

	def setup_student_marks(self):
		self.student.marks = self.browser.get_student_marks()

	def setup_view(self):
		table = Table(['Предмет', 'Оценки', 'Кол-во оценок', 'Средний балл', 'До допуска'])

		means = []
		counter = 0

		for mark in self.student.marks:
			mark.gen_view()
			if mark.mean != 0:
				means.append(mark.mean)
				counter += 1
			table.add_row([mark.view_subject, mark.view_marks, mark.view_marks_number, mark.view_mean, mark.view_access])

		self.view = f'{BColors.BOLD}Ученик: {BColors.GREEN}{self.student.name}{BColors.ENDC}\n{BColors.BOLD}Средний балл среди предметов: {BColors.GREEN}{bcolors.mark_to_colored(round(statistics.mean(means), 2))}\n{table}'

	@staticmethod
	def error_auth():
		print(f'{BColors.RED}{BColors.BOLD}Ошибка авторизации: "Неверный логин или пароль"!{BColors.ENDC}')
