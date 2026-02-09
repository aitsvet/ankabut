import re

import llm

class Reranker:

    def __init__(self, cfg, client: llm.Client, docs, ids):
        self.cfg = cfg
        self.client = client
        self.docs = docs
        self.ids = ids
        self.rerank_cfg = cfg.get('prompts', {}).get('rerank', {})
        self.window_size = self.rerank_cfg.get('window_size', 5)
        self.max_samples = self.rerank_cfg.get('max_samples', 5)
        self.min_samples = self.rerank_cfg.get('min_samples', 3)
        self.prompt = self.rerank_cfg.get('template', '')

    def _get_paragraph_text(self, result):
        doc_id, sec_id, par_id = result['path'].split(':')
        doc = next(d for d in self.docs if d['path'] == doc_id)
        paragraph = doc['sections'][int(sec_id)]['paragraphs'][int(par_id)]
        return re.sub(r'\[[, 0-9]+\]', '', paragraph['content'])

    def _format_paragraphs(self, results):
        text = ''
        for i, result in enumerate(results):
            text += f"{i+1}. ID: {result['id']}, dist: {result['dist']:.4f}\n"
            text += f"{self._get_paragraph_text(result)}\n\n"
        return text

    def _format_context(self, selected_ids):
        if not selected_ids:
            return 'No paragraphs selected yet.'
        text = 'Previously selected paragraphs:\n\n'
        for sel_id in selected_ids:
            for result in self.current_results:
                if result['id'] == sel_id:
                    text += f"- {sel_id}: {self._get_paragraph_text(result)}\n"
                    break
        return text

    def _parse_response(self, response, available_ids):
        selected_ids = []
        for item in response.split(','):
            item = item.strip()
            if not item:
                continue
            match = re.search(r'\d+:\d+:\d+', item)
            if match:
                match_str = match.group()
                if match_str in available_ids:
                    selected_ids.append(match_str)
        return selected_ids

    def rerank(self, search_results, query):
        self.current_results = sorted(search_results, key=lambda r: r['dist'], reverse=True)
        selected_ids = []
        start_idx = 0
        while start_idx < len(search_results):
            window_results = search_results[start_idx:start_idx + self.window_size]
            if not window_results:
                break
            available_ids = [r['id'] for r in window_results]
            paragraphs_text = self._format_paragraphs(window_results)
            context_text = self._format_context(selected_ids)
            values = {
                'query': query,
                'paragraphs': paragraphs_text,
                'context': context_text,
                'window_size': len(window_results) + len(selected_ids),
                'max_samples': self.max_samples,
                'min_samples': self.min_samples
            }
            response = self.client.chat('rerank', values)
            new_selected_ids = self._parse_response(response, available_ids + selected_ids)
            if len(new_selected_ids):
                selected_ids = new_selected_ids
            start_idx += self.window_size
        filtered_results = [r for r in search_results if r['id'] in selected_ids]
        return filtered_results
