import pickle

DEFAULT_HIST = 'histfile'

def print_ordered_hist(hist):
    for k in sorted(hist.keys()):
        print(f"{k}, {hist[k]}")



class Command:
    def __init__(self, time=None, user=None, hostUUID=None, command=None, result=None):
        self.time = time
        self.user = user
        self.hostUUID = hostUUID
        self.command = command
        self.result = result

    def __str__(self):
        return f"{self.time}, {self.user}, {self.hostUUID}, {self.command}, {self.result}"





def main():
    hist = [] 
    with open(DEFAULT_HIST, 'rb') as infi:
        hist = pickle.load(infi)

    print_ordered_hist(hist)

    for k,v in hist.items():
        print(Command(k, *v))
    

if __name__=="__main__":
    main()
