

def unpack():
    path = r"C:\Users\mbynmr\OneDrive - The University of Nottingham\Documents\Non-shared folder\Misc\awbw\base damage.txt"
    with open(path, 'r') as file:
        table = []
        for line in file:
            l = line.replace('-', "0")
            l = l.replace('\n', "")
            l = l.split(' \t')
            table.append(list(map(int, l)))
        print(table)
