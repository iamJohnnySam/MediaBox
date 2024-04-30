from tools.logger import log
from PyPDF2 import PdfFileReader, PdfFileWriter


class PDFReader:
    def __init__(self, job_id: int):
        self.job_id = job_id
        log(job_id, msg="Module Created")

    def decrypt_pdf(self, input_path, output_path, password):
        with open(input_path, 'rb') as input_file, \
                open(output_path, 'wb') as output_file:
            reader = PdfFileReader(input_file)
            reader.decrypt(password)
            log(self.job_id, msg='PDF Decrypted')

            writer = PdfFileWriter()

            for i in range(reader.getNumPages()):
                writer.addPage(reader.getPage(i))

            writer.write(output_file)
