# from controller.controller import Controller
from controller.temp import Controller


if __name__ == '__main__':
    controller = Controller()
    controller.register()

    controller.start()
