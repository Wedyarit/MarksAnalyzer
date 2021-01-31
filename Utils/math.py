import statistics

def access(values):
	mean = statistics.mean(values)
	access_value = 0

	while mean < 8:
		values.append(9)
		mean = statistics.mean(values)
		access_value += 1

	return access_value
