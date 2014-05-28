from unittest import main
from unittest import TestCase
import os
import pdf2img
import shutil


class TestPdf2img(TestCase):

    def setUp(self):
        self.converter = pdf2img.Pdf2Img()

    def tearDown(self):
        if os.path.exists(os.path.abspath(self.converter.path)):
            shutil.rmtree(self.converter.path)

    def test_converter(self):
        result = self.converter.convert(
            os.path.abspath('./tests/handbuch.pdf'))

        self.assertEquals(5, len(result), 'Expect five images')


if __name__ == "__main__":
    main()
