import datetime
import os
import settings
from communication import communicator
import logger
from cctv.image_classifier import ImageClassifier
from communication.email_manager import EmailManager


class CCTVChecker:
    last_detect_A02 = None
    last_detect_A01 = None

    def __init__(self):
        self.outlook = None
        self.cctv_classifier1 = ImageClassifier(settings.cctv_model1, "A01", 0.75)
        self.cctv_classifier2 = ImageClassifier(settings.cctv_model2, "A02", 0.75)

        if not os.path.exists(settings.cctv_download):
            os.makedirs(settings.cctv_download)

        for f in os.listdir(settings.cctv_download):
            os.remove(os.path.join(settings.cctv_download, f))

        self.create_object()

    def create_object(self):
        self.outlook = EmailManager(settings.em, settings.pw, 'Security')
        print("Created CCTV Object")

    def run_code(self):
        if self.outlook.connection_err > 4:
            del self.outlook
            self.create_object()

        running = True
        sus_attachment_count: int = 0

        while running:
            running, attachment, date, file_n = self.outlook.get_next_attachment()

            if not running:
                break

            save_as = date + " " + file_n
            save_as = save_as.replace(",", "").replace(":", "-")
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(attachment)
                fp.close()

            if "A01" in file_n:
                val, sus, location = self.cctv_classifier1.classify(att_path)
                if sus:
                    self.last_detect_A01 = datetime.datetime.now()
            elif "A02" in file_n:
                val, sus, location = self.cctv_classifier2.classify(att_path)
                if sus:
                    self.last_detect_A02 = datetime.datetime.now()
            else:
                val, sus, location = 0, 0, ""

            if sus:
                if sus_attachment_count == 0:
                    communicator.send_now(date, "cctv", cctv=True)
                    sus_attachment_count = sus_attachment_count + 1
                communicator.send_now(att_path, "cctv", img=True, cctv=True)
                communicator.send_now(str(val), "cctv", cctv=True)
            print(save_as + "\t SUS: " + str("%.2f" % val) + "\t Copy to: " + location)
            logger.log('info', save_as + "\t SUS: " + str(val) + "\t Copy to: " + location)

            os.remove(att_path)

        print("-------CCTV-------")
