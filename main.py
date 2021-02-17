import sys
import emulator
import hazard


if(len(sys.argv)!=2):
	print("usage:\"python[3] main.py <inputFileName>\"")
	print("input file shoud have RISC-V instructions (without pseudoinstructions, labels and empty lines)")
	sys.exit(-1)


mymac = emulator.machine(sys.argv[1])
try:
    mymac.run()
except Exception as e:
    print("!!!!!!!!!!BUG!!!!!!!!!!!")
    print(e)
    print("I will dump stuff up to here anyway:")

mymac.showprogram()
mymac.showdata()
mymac.showregs()
#mymac.showdump()
hazard.hazardDetector(mymac.dump)

print("\n\n**CLOCKS AND STALLS**")
print("Number of instructions executed: ", len(mymac.dump))
print("Number of clock cycles: ", mymac.dump[-1][5][0])
print("Number of stalls added: ", mymac.dump[-1][5][0] - len(mymac.dump) -4)
