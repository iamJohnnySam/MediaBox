




    def finance(self, msg: Job):
        if msg.value == "":
            self.send_now("Please type the amount", chat=msg.chat_id, reply_to=msg.message_id)
            self.get_user_input(msg.chat_id, "finance", None)
            return

        try:
            amount = float(msg.value)
        except ValueError:
            self.send_now("Please type the amount in numbers only", chat=msg.chat_id, reply_to=msg.message_id)
            self.get_user_input(msg.chat_id, "finance", None)
            return

        if user_input and identifier is not None:
            sql_id = identifier
            query = f'UPDATE transaction_lkr SET amount = "{amount}" WHERE transaction_id = "{sql_id}"'
            sql_databases["finance"].run_sql(query)

        else:
            columns = 'transaction_by, amount'
            val = (msg.chat_id, amount)
            success, sql_id = sql_databases["finance"].insert('transaction_lkr', columns, val,
                                                              get_id=True,
                                                              id_column='transaction_id')

        prefix = str(sql_id) + ";"

        self.send_with_keyboard(job=f'[{sql_id}] Is LKR {msg.value} an income or expense?',
                                chat_id=msg.chat_id,
                                button_text=["Income", "Expense", "Invest", "Delete"],
                                button_cb=["finance", "finance", "finance", "finance"],
                                button_val=[prefix + "1;income",
                                                    prefix + "1;expense",
                                                    prefix + "1;invest",
                                                    prefix + "1;delete"],
                                arrangement=[3, 1],
                                reply_to=msg.message_id
                                )

    def sms_bill(self, msg: Job):
        if not self.check_command_value(msg, inquiry="sms received from bank"):
            return
        pass



    def baby_weight(self, msg: Job):
        if not self.check_command_value(msg, replace="kg", inquiry="weight of modules in kg", check_float=True):
            return
        weight = float(msg.value)

        key = datetime.now().strftime('%Y/%m/%d')

        query = 'SELECT date, weight FROM weight ORDER BY weight_id DESC LIMIT 1;'
        last_entry = sql_databases["modules"].run_sql(query=query)

        columns = "date, weight, added_by"
        val = (key, weight, str(msg.chat_id))
        sql_databases["modules"].insert('weight', columns, val)

        send_string = "\U0001F6BC \U0001F3C6 \n" + \
                      "modules Weight Added - " + msg.value + "kg. \nThat's a weight gain of " + \
                      "{:10.2f}".format(weight - last_entry[1]) + "kg since " + str(last_entry[0]) + "."

        logger.log(send_string)
        self.baby_weight_trend(msg, caption=send_string)


    # -------------- PHOTO FUNCTIONS --------------

    def finance_photo(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        if not os.path.exists(global_var.finance_images):
            os.makedirs(global_var.finance_images)

        columns = 'transaction_by, photo_id'
        val = (from_id, value)
        success, sql_id = sql_databases["finance"].insert('transaction_lkr', columns, val,
                                                          get_id=True,
                                                          id_column='transaction_id')
        shutil.move(os.path.join(global_var.telepot_image_dump, value),
                    os.path.join(global_var.finance_images, value))
        self.send_now("How much is the amount?", chat=from_id, reply_to=str(message_id))
        self.get_user_input(from_id, "finance", sql_id)

    # -------------- CALLBACK FUNCTIONS --------------



    def cb_finance(self, callback_id, query_id, from_id, value):
        message_id = self.update_in_line_buttons(callback_id)
        self.bot.answerCallbackQuery(query_id, text='Got it')

        data = value.split(";")
        if data[2].lower() == "delete":
            query = f'DELETE FROM transaction_lkr WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query, fetch_all=True)
            return

        if data[1] == "1":
            query = f'UPDATE transaction_lkr SET type = "{data[2]}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            d = datetime.now().strftime("%Y-%m-%d")
            query = f'UPDATE transaction_lkr SET date = "{d}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query)

            if data[2] == "invest":
                in_out = "income"
            else:
                in_out = data[2]

            query = f'SELECT DISTINCT type FROM categories WHERE in_out = "{in_out}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.job_keyboard_extractor(data[0], "2", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};2;Delete')
            arrangement.append(1)

            self.send_with_keyboard(job=f'[{data[0]}] What type of {data[2]} was it?',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "2":
            query = f'SELECT DISTINCT category FROM categories WHERE type = "{data[2]}"'
            result = list(sql_databases["finance"].run_sql(query, fetch_all=True))

            button_text, button_cb, button_value, arrangement = self.job_keyboard_extractor(data[0], "3", result, 'finance')
            button_text.append("Delete")
            button_cb.append("finance")
            button_value.append(f'{data[0]};3;Delete')
            arrangement.append(1)

            self.send_with_keyboard(job=f'[{data[0]}] What is the category of {data[2]}',
                                    chat_id=from_id,
                                    button_text=button_text,
                                    button_cb=button_cb,
                                    button_val=button_value,
                                    arrangement=arrangement,
                                    reply_to=message_id
                                    )
        elif data[1] == "3":
            query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
            cat_id = list(sql_databases["finance"].run_sql(query))[0]
            query = f'UPDATE transaction_lkr SET category_id = "{cat_id}" WHERE transaction_id = "{data[0]}"'
            sql_databases["finance"].run_sql(query, fetch_all=True)
            logger.log(f'Updated Transaction - {data[0]}')
            self.send_now(f'[{data[0]}] Transaction successfully updated', chat=from_id)
