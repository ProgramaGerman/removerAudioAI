from app.presenters.main_presenter import MainPresenter
from app.views.main_window import MainWindow


def main() -> None:
    presenter = MainPresenter()
    window = MainWindow(presenter)
    window.build()
    window.run()


if __name__ == "__main__":
    main()
