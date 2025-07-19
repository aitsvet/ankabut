import json

import embedder

script_marker = '<script src="lib/bindings/utils.js"></script>'
body_marker = '<script type="text/javascript">'

def print(em: embedder.Index, cfg, tpl: str, cosine_distance):
    n = em.ems.ntotal
    step = max(1, n // 10)
    tickvals = list(range(0, n, step))
    if n - 1 > tickvals[-1]:
        p = em.get_paragraph(n-1)
        tickvals.append(f"{p["year"]} {p["author"]} {p["sec_id"]} {p["par_id"]}")
    tpl = tpl.replace(script_marker, f"""
        <script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
        <style type="text/css">#heatmap {{ height: {cfg["height"]}px }}</style>
        """ + script_marker)
    return tpl.replace(body_marker, f"""
    <div class="container"> <div id="graph"></div> <div id="heatmap"></div> <div id="closest"></div> </div>
    <script type="text/javascript">
        const cosine_distance = {json.dumps(cosine_distance.tolist())};
        const n = {n};
        const tickvals = {json.dumps(tickvals)};
        const ticktext = tickvals.map(v => v.toString());
        Plotly.newPlot('heatmap', [{{ z: cosine_distance,
            type: 'heatmap', colorscale: '{cfg["colorscale"]}'
        }}], {{
            title: 'Paragraph Embedding Cosine Distance Heatmap',
            position: 'sticky', width: {cfg["width"]}, height: {cfg["height"]},
            xaxis: {{ tickvals: tickvals, ticktext: ticktext }},
            yaxis: {{ tickvals: tickvals, ticktext: ticktext }}
        }});
    </script>""" + body_marker)