from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

class Reader:

    def __init__(self):
        self.converter = PdfConverter(artifact_dict=create_model_dict())

    def extract_markdown_from(self, src):
        rendered = self.converter(src)
        source, _, _ = text_from_rendered(rendered)
        return source