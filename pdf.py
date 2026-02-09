import llm

from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser

class Reader:

    def __init__(self, cfg = {}):
        client = llm.Client(cfg)
        self.config = {
            "force_ocr": True,
            "paginate_output": True,
            "use_llm": True,
            "llm_service": "marker.services.openai.OpenAIService",
            "openai_base_url": client.cfg.get('base_url', 'http://localhost:11434/v1/'),
            "openai_api_key": client.cfg.get('api_key', 'EMPTY'),
            "openai_model": client.cfg.get('model'),
        }
    
    def render(self, output_format, src):
        config = self.config.copy()
        config["output_format"] = output_format
        config_parser = ConfigParser(config)
        render = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service()
        )
        return render(src)


    def md_from(self, src):
        rendered = self.render("markdown", src)
        source, _, _ = text_from_rendered(rendered)
        return source

    def html_from(self, src):
        rendered = self.render("chunks", src)
        result = ['<html><body>']
        for c in rendered.blocks:
            p = c.html.find(" ")
            result.append(f'{c.html[:p]} id="{c.id}" {c.html[p:]}')
        result.append('</body></html>')
        return  '\n'.join(result)
    
    def convert(self, src: Path, dst: Path):
        if dst.suffix.lower() == '.md':
            dst.write_text(self.md_from(src.as_posix()))
        if dst.suffix.lower() == '.html':
            dst.write_text(self.html_from(src.as_posix()))