from pdf2img.web import app
from unittest import TestCase
from unittest import main


class TestPdf2imgWebApp(TestCase):

    def setUp(self):
        self.app = app.test_client()
        pass

    def test_server_init(self):
        response = self.app.get('/')
        self.assertEquals('This is the pdf2img service... stay tuned',
                          response.data)

    def tearDown(self):
        pass

if __name__ == '__main__':
    main()
