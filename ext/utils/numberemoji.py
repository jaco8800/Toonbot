numdict = {0:"0⃣",1:"1⃣",2:"2⃣",3:"3⃣",4:"4⃣",
	5:"5⃣",6:"6⃣",7:"7⃣",8:"8⃣",9:"9⃣"}

def emojinumbers(list):
	reacts = []
	fields = []
	for i in range(len(list)):
		reacts.append(numdict[i])
		fields.append(f"{numdict[i]} {list[i]}")
	return reacts,fields