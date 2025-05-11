from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

class Reader:

    def __init__(self):
        self.converter = PdfConverter(artifact_dict=create_model_dict())

    def md_from(self, src):
        rendered = self.converter(src)
        source, _, _ = text_from_rendered(rendered)
        return source
    
    def convert(self, src: Path, dst: Path):
        dst.write_text(self.md_from(src.as_posix()))