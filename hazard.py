
def hazardDetector(instructions):
	# Lists of types to be used to add stalls
	branchType = ["beq", "bne", "blt", "bge", "bltu", "bgeu", "jal", "jalr"]
	loadType = ["lb", "lh", "lw", "lbu", "lhu"]

	# Initializing counter variables
	clockCounter = 4
	instructionCounter = 0

	print("\n\n*******EXECUTION******")
	print("arguments and results are as (register,value) with register being -1 for not a register")
	print("\n%10s%10s%10s%10s%10s%10s"%("PC&order","inst.","result","arg1","arg2","clk&stall"))
	print("-"*60)
	#  Following executed iterations one by one
	for inst in instructions:
		# HANDLING CONTROL HAZARDS
		# If we have a branch type instruction we have two cases.
		# If this branch instruction is dependent to the destination register of previous instruction we add TWO STALLS,
		# otherwise we only add ONE STALL.
		if inst[1] in branchType:
			if not instructions[instructionCounter - 1][1] in branchType and (
                    	(inst[3][0] == instructions[instructionCounter - 1][2][0] and
                     	inst[3][0] != 0 and inst[3][0] != -1) or
                    	(inst[4][0] == instructions[instructionCounter - 1][2][0] and
                     	inst[4][0] != 0 and inst[4][0] != -1)):
				clockCounter += 3
				inst[5] = (clockCounter, 2)
			else:
				clockCounter += 2
				inst[5] = (clockCounter, 1)

		# HANDLING DATA HAZARDS
		# If we have a load type instruction, and also if next instruction needs to use the register that is supposed to
		# change in this load instruction we add ONE STALL.
		elif inst[1] in loadType:
			if inst[2][0] == instructions[instructionCounter + 1][3][0] or \
					inst[2][0] == instructions[instructionCounter + 1][4][0]:
				clockCounter += 2
				inst[5] = (clockCounter, 1)
			else:
				clockCounter += 1
				inst[5] = (clockCounter, 0)
		#  If there is no hazard we just add one cycle and continue with our instructions. The number of stalls will be 0.
		else:
			clockCounter += 1
			inst[5] = (clockCounter, 0)
		instructionCounter += 1
		res = ""
		for j in inst:
			res += "%10s" % (str(j))
		print(res)
	return 0
