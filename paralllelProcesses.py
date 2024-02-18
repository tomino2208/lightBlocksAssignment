from subprocess import Popen



if __name__ == '__main__':
    function = "connectToNetwork.py"
    commands = []
    range_blocks = list(range(0, 210000, 10000))

    for pos in range(len(range_blocks)-1):
        start = range_blocks[pos]+1
        if start==1:
            start = 0
        end = range_blocks[pos+1]
        linuxCommand = f"python {function} {start} {end}"
        commands += [linuxCommand]
    procs = [Popen(i.split()) for i in commands]
    for p in procs:
        p.wait()
    print('Hello')