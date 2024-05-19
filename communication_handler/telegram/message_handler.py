try:
    in_queue = bots[channel].waiting_user_input.keys()
except KeyError as e:
    self.channel_error(e, channel)
    return



if get_input and self._job.chat_id in in_queue:
    log(job_id=self._job.job_id, msg="Chats in Queue: " + str(in_queue))
    queues.message_q.put(message)

else:
    try:
        bots[self._job.telepot_account].send_now(message=message)
    except KeyError as e:
        self.channel_error(e, channel)
        return

    if get_input:
        try:
            bots[self._job.telepot_account].get_user_input(job=self._job, index=index)
        except KeyError as e:
            self.channel_error(e, channel)
            return



    def channel_error(self, e, channel):
        if params.is_module_available('telepot'):
            log(job_id=self._job.job_id, error_code=10003, msg=str(e))
            raise InvalidParameterException
        else:
            log(job_id=self._job.job_id, log_type="warn",
                msg=f"Unable to send message. Channel, {channel} may not be available due not in operation mode.")