from options import Options

class BColors:
	GREEN = '\033[92m'
	RED = '\033[91m'
	YELLOW = '\033[93m'
	MAGENTA = '\033[95m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'

def mark_to_colored(mark):
	if Options.EXCELLENT_MARK > mark > 0:
		return f'{BColors.RED}{mark}{BColors.ENDC}'
	else:
		return f'{BColors.GREEN}{mark}{BColors.ENDC}'
