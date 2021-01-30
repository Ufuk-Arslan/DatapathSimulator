//sa
//as

#ifndef DEATAPATH_H_INCLUDED
#define DATAPATH_H_INCLUDED

#include <iostream>
#include <vector>
using namespace std;


//*******we should be tallying stalls******** 
//TODO: This section is unfinished.
class Stall{
public:
	int instNo;
};
class StallTally{
public:
	vector<Stall> list;

};
//*******************************************


//HAZARD POLICY: IF, IN DECODE STAGE, HAZARD DETECTOR DETECTS AN HAZARD, DECODE UNIT  
//PUSHES A ZERO INSTRUCTION TO THE REST OF THE PIPELINE UNTIL THE HAZARD IS RESOLVED

class IFIDClass{//Classes may need constructors to set the fields to zero to avoid unexpected behavior 
public:
	long long instNo_i;	//number of instruction at this scate of pipeline for tallying and debug
	long long instNo_o;

	unsigned int instruction_i : 32;//bit field is used
	unsigned int instruction_o : 32;

	IFIDClass();

	void clock(void){
		instNo_o=instNo_i;
		instruction_o=instruction_i;
	}

	void display(void){
		cout<<"-----IF/ID Pipeline Register----"<<endl;
		cout<<"---Input:--"<<endl;
		cout<<"    #instruction index:"<<instNo_i<<endl;
		cout<<"         instruction_i:"<<instruction_i<<endl;
		cout<<"---Output:--"<<endl;
		cout<<"    #instruction index:"<<instNo_o<<endl;
		cout<<"         instruction_o:"<<instruction_o<<endl;
		cout<<"--------------------------------"<<endl<<endl<<endl;
	}
};

class IDEXClass{
public:
	long long instNo_i;
	long long instNo_o;

	unsigned int operand1_i:32;
	unsigned int operand1_o:32;

	unsigned int operand2_i:32;
	unsigned int operand2_o:32;

	unsigned int destReg_i:5;
	unsigned int destReg_o:5;

	unsigned int src1Reg_i:5;
	unsigned int src2Reg_i:5;
	unsigned int src1Reg_o:5;
	unsigned int src2Reg_o:5;

	unsigned int OPCode_i:6;
	unsigned int OPCode_o:6;

	unsigned int ALUOPCode_i:6;
	unsigned int ALUOPCode_o:6;

	IDEXClass();

	void clock(void){
		instNo_o=instNo_i;
		operand1_o=operand1_i;
		operand2_o=operand2_i;
		destReg_o=destReg_i;
		src1Reg_o=src1Reg_i;
		src2Reg_o=src2Reg_i;
		OPCode_o=OPCode_i;
		ALUOPCode_o=ALUOPCode_i;
	}

	void display(void){
		cout<<"-----ID/EX Pipeline Register----"<<endl;
		cout<<"---Input:--"<<endl;
		cout<<"    #instruction index:"<<instNo_i<<endl;
		cout<<"         operand1_i:"<<operand1_i<<endl;
		cout<<"         operand2_i:"<<operand2_i<<endl;
		cout<<"          destReg_i:"<<destReg_i<<endl;
		cout<<"          src1Reg_i:"<<src1Reg_i<<endl;
		cout<<"          src2Reg_i:"<<src2Reg_i<<endl;
		cout<<"           OPCode_i:"<<OPCode_i<<endl;
		cout<<"        ALUOPCode_i:"<<ALUOPCode_i<<endl;
		cout<<"---Output:--"<<endl;
		cout<<"    #instruction index:"<<instNo_o<<endl;
		cout<<"         operand1_o:"<<operand1_o<<endl;
		cout<<"         operand2_o:"<<operand2_o<<endl;
		cout<<"          destReg_o:"<<destReg_o<<endl;
		cout<<"          src1Reg_o:"<<src1Reg_o<<endl;
		cout<<"          src2Reg_o:"<<src2Reg_o<<endl;
		cout<<"           OPCode_o:"<<OPCode_o<<endl;
		cout<<"        ALUOPCode_o:"<<ALUOPCode_o<<endl;
		cout<<"--------------------------------"<<endl<<endl<<endl;
	}
};

class EXMEMClass{
public:
	long long instNo_i;
	long long instNo_o;

	unsigned int result_i:32;
	unsigned int result_o:32;

	unsigned int destReg_i:5;
	unsigned int destReg_o:5;

	unsigned int OPCode_i:6;
	unsigned int OPCode_o:6;

	EXMEMClass();

	void clock(void){
		instNo_o=instNo_i;
		result_o=result_i;
		destReg_o=destReg_i;
		OPCode_o=OPCode_i;
	}

	void display(void){
		cout<<"-----EX/MEM Pipeline Register----"<<endl;
		cout<<"---Input:--"<<endl;
		cout<<"    #instruction index:"<<instNo_i<<endl;
		cout<<"           result_i:"<<result_i<<endl;
		cout<<"          destReg_i:"<<destReg_i<<endl;
		cout<<"           OPCode_i:"<<OPCode_i<<endl;
		cout<<"---Output:--"<<endl;
		cout<<"    #instruction index:"<<instNo_o<<endl;
		cout<<"           result_o:"<<result_o<<endl;
		cout<<"          destReg_o:"<<destReg_o<<endl;
		cout<<"           OPCode_o:"<<OPCode_o<<endl;
		cout<<"--------------------------------"<<endl<<endl<<endl;
	}

};

class MEMWBClass{
public:
	long long instNo_i;
	long long instNo_o;

	unsigned int result_i:32;
	unsigned int result_o:32;

	unsigned int destReg_i:5;
	unsigned int destReg_o:5;

	void clock(void){
		instNo_o=instNo_i;
		result_o=result_i;
		destReg_o=destReg_i;
	}

	void display(void){
		cout<<"-----EX/MEM Pipeline Register----"<<endl;
		cout<<"---Input:--"<<endl;
		cout<<"    #instruction index:"<<instNo_i<<endl;
		cout<<"           result_i:"<<result_i<<endl;
		cout<<"          destReg_i:"<<destReg_i<<endl;
		cout<<"---Output:--"<<endl;
		cout<<"    #instruction index:"<<instNo_o<<endl;
		cout<<"           result_o:"<<result_o<<endl;
		cout<<"          destReg_o:"<<destReg_o<<endl;
		cout<<"--------------------------------"<<endl<<endl<<endl;
	}
};

class InstructionMemoryClass;
class DataMemoryClass;
class RegistersClass;

class Datapath{
public:

	long long clockCount;
	IFIDClass IFID;
	IDEXClass IDEX;
	EXMEMClass EXMEM;
	MEMWBClass MEMWB;

	InstructionMemoryClass instructionMemory;//may be initialized in constructor using text input
	DataMemoryClass dataMemory;
	RegistersClass registers;

	Datapath(){
		clockCount=0;
	}

	//TODO: implement all of these
	void fetch(void); //may include PC as static?
	void decode(void);
	void execute(void);
	void memory(void);
	void writeback(void);

	void cycle(void){
		fetch();
		decode();
		execute();
		memory();
		writeback();
		IFID.clock();
		IDEX.clock();
		EXMEM.clock();
		MEMWB.clock();
		clockCount++;
	}

	void display(void){
		cout<<endl<<endl<<"*******************************************"<<endl;
		cout<<"SITUATION AT CYCLE "<<clockCount<<endl;
		cout<<"*******************************************"<<endl;
		//print programCounter
		IFID.display();
		IDEX.display();
		EXMEM.display();
		MEMWB.display();
		cout<<"*******************************************"<<endl<<endl<<endl;
	}
};

#endif
