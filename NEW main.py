from controller.controller import Controller


if __name__ == '__main__':
    controller = Controller()
    controller.register()

    while True:
        controller.update_arena()
