import threading
lock = []
        
def add_lock():
    lock.append(threading.Event())
    print("lock add:" + str(len(lock)-1))
    return (len(lock)-1)

def thread_lock(lock_id):
    lock[lock_id].clear()
    lock[lock_id].wait()

def release_lock(lock_id):
    lock[lock_id].set()
    print("lock release:" + str(lock_id))

def clear_lock():
    try:
        while len(lock) > 0:
            lock.pop()
        print("lock clear - success")
    except:
        print("lock clear - fail")
        pass
    

