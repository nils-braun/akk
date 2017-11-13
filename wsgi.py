from akk import create_app
application = create_app("config.py")

if __name__ == "__main__":
    application.run()
