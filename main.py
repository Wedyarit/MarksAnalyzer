from Additions.manager import Manager
from options import Options
from Additions.student import Student

if __name__ == '__main__':
	manager = Manager(Student(login=Options.LOGIN, password=Options.PASSWORD))
	print(manager.view)
