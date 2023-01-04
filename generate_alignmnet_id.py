from openpecha.core.ids import get_alignment_id

for i in range(0,1000):
    with open("alignmnet_ids.txt","a") as file:
        id  = get_alignment_id()
        file.write(id+"\n")