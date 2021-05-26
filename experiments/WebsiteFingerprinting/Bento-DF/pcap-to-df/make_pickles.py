import pickle
import sys

x_train_file = sys.argv[1]
y_train_file = sys.argv[2]


# Load the x_train_file
x_train = open(x_train_file, 'rb')
xa = pickle.load(x_train, encoding='iso-8859-1')
x_train.close()

# Load the y_train_file
y_train = open(y_train_file, 'rb')
ya = pickle.load(y_train, encoding='iso-8859-1')
y_train.close()

# Ensure that len(xa) == len(ya)
if len(xa) != len(ya):
	print("[!] Lengths of the training files don't match.")
	sys.exit(1)

# Normalized per the DF paper
test_len = int(len(ya) * 0.125)

x_test_file = x_train_file + "-test"
y_test_file = y_train_file + "-test"

# Dump the testing file
x_test = open(x_test_file, 'wb')
pickle.dump(xa[:test_len], x_test)
x_test.close()

y_test = open(y_test_file, 'wb')
pickle.dump(ya[:test_len], y_test)
y_test.close()


# Dump the validation file
x_valid_file = x_train_file + "-valid"
y_valid_file = y_train_file + "-valid"

# Dump the testing file
x_valid = open(x_valid_file, 'wb')
pickle.dump(xa[:test_len], x_valid)
x_valid.close()

y_valid = open(y_valid_file, 'wb')
pickle.dump(ya[:test_len], y_valid)
y_valid.close()

print("[+] Done")
