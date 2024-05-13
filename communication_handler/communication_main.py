from shared_tools.logger import log


def main(flag_stop):
    if params.is_module_available('telepot'):
        channel_control.init_channel()

    if params.is_module_available('socket'):
        channel_control.init_socket()

    log(msg="Ready to Run...")
    channel_control.send_message(Message("--- iamJohnnySam ---\n"
                                         "Version 2.1\n\n"
                                         f"Program Started on {global_variables.host}..."))