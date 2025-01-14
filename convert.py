from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

import os
from pathlib import Path

def from_pdf(src, dst):
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )
    src = Path(src)
    if src.is_dir():
        for file in src.iterdir():
            rendered = converter(file.as_posix())
            text, _, _ = text_from_rendered(rendered)
            output = os.path.join(dst, file.with_suffix('.md').name)
            with open(output, 'w+') as f:
                f.write(text)
                print(f'Written {output}')
