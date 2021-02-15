import ctypes as t

def opadd(a,b):
	return t.c_uint32(a+b).value
def opsub(a,b):
	return t.c_uint32(a-b).value
def opxor(a,b):
	return t.c_uint32(a^b).value
def opor(a,b):
	return t.c_uint32(a|b).value
def opand(a,b):
	return t.c_uint32(a&b).value
def opsll(a,b):
	return t.c_uint32(a<<b).value
def opsrl(a,b):
	return t.c_uint32(t.c_uint32(a).value>>b).value
def opsra(a,b):
	return t.c_uint32(a>>b).value
def opslt(a,b):
	return t.c_uint32(t.c_int32(a).value<t.c_int32(b).value).value
def opsltu(a,b):
	return t.c_uint32(t.c_uint32(a).value<t.c_uint32(b).value).value


def oplb(mem,idx):
	return t.c_int8(mem.get(idx)).value
def oplbu(mem,idx):
	return t.c_uint8(mem.get(idx)).value
def oplh(mem,idx):
	return t.c_int16(mem.gethalf(idx)).value
def oplhu(mem,idx):
	return t.c_uint16(mem.gethalf(idx)).value
def oplw(mem,idx):
	return t.c_uint32(mem.getword(idx)).value


def opsb(mem,idx,data):
	mem.write(idx,data)
	return oplb(mem,idx) #this is returned to be able to spot bugs
def opsh(mem,idx,data):
	mem.writehalf(idx,data)
	return oplh(mem,idx)
def opsw(mem,idx,data):
	mem.writeword(idx,data)
	return oplw(mem,idx)


def opbeq(a,b,immoffset):
	if(a==b):
		return immoffset
	else:
		return 4
def opbne(a,b,immoffset):
	if(a!=b):
		return immoffset
	else:
		return 4
def opblt(a,b,immoffset):
	if(t.c_int32(a).value < t.c_int32(b).value):
		return immoffset
	else:
		return 4
def opbge(a,b,immoffset):
	if(t.c_int32(a).value >= t.c_int32(b).value):
		return immoffset
	else:
		return 4
def opbltu(a,b,immoffset):
	if(t.c_uint32(a).value < t.c_uint32(b).value):
		return immoffset
	else:
		return 4
def opbgeu(a,b,immoffset):
	if(t.c_uint32(a).value >= t.c_uint32(b).value):
		return immoffset
	else:
		return 4
