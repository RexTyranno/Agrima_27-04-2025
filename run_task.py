from tasks import add

if __name__ == '__main__':
    # task is added to the queue
    result = add.delay(7, 8)
    print(f"Dispatched add(7, 8) → task id: {result.id!r}")
