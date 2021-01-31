import statistics

from Utils.bcolors import BColors
from options import Options
from Utils.math import access

class Mark(object):
	def __init__(self, subject):
		self.subject = subject
		self.values = []

		self.marks_number = 0
		self.mean = 0
		self.access = 0

		self.view_subject = ''
		self.view_marks = ''
		self.view_mean = format(0, '.2f')
		self.view_marks_number = '0'
		self.view_access = ''

		self.gen_view()

	def add_mark(self, mark):
		self.values.append(int(mark))
		self.calculate()

	def calculate(self):
		self.marks_number = len(self.values)
		self.mean = round(statistics.mean(self.values), 2)

	def gen_view(self):
		if self.mean != 0 and self.mean < Options.EXCELLENT_MARK:
			self.view_subject = f'{BColors.RED}{self.subject}{BColors.ENDC}'
			self.view_mean = f'{BColors.RED}{format(self.mean, ".2f")}{BColors.ENDC}'
		else:
			self.view_subject = f'{BColors.GREEN}{self.subject}{BColors.ENDC}'
			self.view_mean = f'{BColors.GREEN}{format(self.mean, ".2f")}{BColors.ENDC}'

		for value in self.values:
			if value == Options.MAX_MARK:
				self.view_marks += f'{BColors.MAGENTA}{str(value)}{BColors.ENDC} '
			elif value < Options.EXCELLENT_MARK:
				self.view_marks += f'{BColors.RED}{str(value)}{BColors.ENDC} '
			else:
				self.view_marks += f'{BColors.GREEN}{str(value)}{BColors.ENDC} '

		if self.mean < Options.EXCELLENT_MARK and len(self.values) > 0:
			self.access = access(self.values)

		if self.access != 0:
			self.view_access = f'{BColors.RED}{self.access}{BColors.ENDC}'
		else:
			self.view_access = f'{BColors.GREEN}{self.access}{BColors.ENDC}'

		self.view_marks_number = f'{BColors.GREEN}{self.marks_number}{BColors.ENDC}'
