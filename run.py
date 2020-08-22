from app import create_app


app = create_app()
# app.run(use_reloader=False, debug=False)
app.app_context().push()
