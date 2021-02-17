import sys      #to get the input file name as the command line argument
import emulator #the RISC-V emulator
import hazard   #the module to calculate the timing of the instructions


if(len(sys.argv)!=2): #check for the correct use of the application and print usage instructions if incorrect
	print("usage:\"python[3] main.py <inputFileName>\"")
	print("input file shoud have RISC-V instructions (without pseudoinstructions, labels and empty lines)")
	sys.exit(-1)

#create an emulator object with instructions in the file given as a command line argument
mymac = emulator.machine(sys.argv[1])
try:
    mymac.run()
except Exception as e: #if the run returns by throwing, then print bug warning but do the rest of the tallying so the user can trace the bug 
    print("!!!!!!!!!!BUG!!!!!!!!!!!") 
    print(e)
    print("I will dump stuff up to here anyway:")

mymac.showprogram()		#first print the human-readable tokens fetched into the instruction memory of the machine
mymac.showdata()		#then print the data memory of the machine on a byte basis
mymac.showregs()		#then show the content of the 32 registers
#mymac.showdump()		#then maybe show the emulator trace or...
hazard.hazardDetector(mymac.dump)#call the timing simulator which writes timing data into the program trace dump and prints it beautifully

#finally, calculate and print the necessary statistics about the execution
print("\n\n**CLOCKS AND STALLS**")
print("Number of instructions executed: ", len(mymac.dump))
print("Number of clock cycles: ", mymac.dump[-1][5][0])
print("Number of stalls added: ", mymac.dump[-1][5][0] - len(mymac.dump) -4)
