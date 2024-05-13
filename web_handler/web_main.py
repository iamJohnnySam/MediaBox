def main(flag_stop):
    if params.is_module_available('web'):
        t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
        t_webapp.start()
        log(msg="Thread Started: Web app")
