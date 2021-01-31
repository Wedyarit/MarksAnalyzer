from options import Options

class BColors:
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def mark_to_colored(mark):
    if Options.EXCELLENT_MARK > mark > 0:
        return f'{BColors.RED}{mark}{BColors.ENDC}'
    else:
        return f'{BColors.GREEN}{mark}{BColors.ENDC}'
