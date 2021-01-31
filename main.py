from Additions.manager import Manager
from Additions.student import Student
from options import Options

if __name__ == '__main__':
	manager = Manager(Student(login=Options.LOGIN, password=Options.PASSWORD))
	print(manager.view)
