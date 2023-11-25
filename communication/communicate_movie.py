import os
import feedparser
from communication import communicator


class CommunicateMovie:
    movie_search = False
    movie_search_id = ""
    movie_selected = False
    selected_movie = 0
    movie_log = []
    movie_images = []

    def __init__(self, telepot_account, chat_id):
        self.telepot_account = telepot_account
        self.chat_id = chat_id
        communicator.send_message(self.telepot_account, self.chat_id, "Enter the name of a movie")

    def handle(self, comm):
        if comm.lower() == "/download" and self.movie_selected:
            self.movie_selected = False
            communicator.send_message(self.telepot_account, self.chat_id, "Movie will be added to queue \n" +
                                      "Send /exit or type another movie")
            communicator.send_to_master(self.telepot_account, self.movie_images[self.selected_movie] + "\n" +
                                        self.movie_log[self.selected_movie])
            os.system("transmission-remote -a " + self.movie_log[self.selected_movie])

        elif comm.isdigit() and (int(comm) <= len(self.movie_log)):
            communicator.send_message(self.telepot_account, self.chat_id, self.movie_images[int(comm) - 1] +
                                      "\n send /download to download this movie. If not continue search")
            self.movie_selected = True
            self.selected_movie = int(comm) - 1

        else:
            self.movie_selected = False
            c = comm.lower().replace(" ", "%20")
            c = c.lower().replace("/", "")
            search_string = "https://yts.mx/rss/" + c + "/720p/all/0/en"
            communicator.send_to_master(self.telepot_account, "Searching " + search_string)
            movie_feed = feedparser.parse(search_string)

            self.movie_log = []
            self.movie_images = []
            i = 1
            for x in movie_feed.entries:
                self.movie_log.append(x.links[1].href)

                image_string = x.summary_detail.value
                sub1 = 'src="'
                idx1 = image_string.index(sub1)
                idx2 = image_string.index('" /></a>')
                self.movie_images.append(image_string[idx1 + len(sub1): idx2])

                communicator.send_message(self.telepot_account, self.chat_id,
                                          str(i) + "\n" + x.title + " - " + x.link)
                i = i + 1

            communicator.send_message(self.telepot_account, self.chat_id,
                                      "Tell me the number of Movie you want to download")
