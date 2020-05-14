import sys
import time


def out(string):
    sys.stdout.write(string + '\n')
    sys.stdout.flush()


if __name__ == '__main__':
    out("Output test start")
    for itr in range(20):
        time.sleep(2)
        out("Output test: iteration #%d" % itr)
    time.sleep(2)
    out("Output test end")
