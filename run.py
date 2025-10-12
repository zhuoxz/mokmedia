from app import create_app

app = create_app("develop")
# app = create_app("product")

if __name__ == '__main__':
    # # Production
    # app.run()

    # Development
    app.run(host='0.0.0.0', debug=True, port=5000)
