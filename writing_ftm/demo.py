"""Local demo: python -m writing_ftm.demo; fixture by default, --live for MLX."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import html
import json
from pathlib import Path
import secrets
from .engine import CritiqueEngine
from .providers import MLXProvider
from .presentation import from_record, present

PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Writing-FTM · Evidence before reassurance</title><style>
body{font:16px/1.6 system-ui;max-width:1050px;margin:45px auto;padding:0 24px;background:#f5f3ee;color:#20302e}h1{font-size:38px;line-height:1.2}small{color:#52625f}textarea,select,button{font:inherit;padding:10px;border:1px solid #b8c6bf;border-radius:6px}textarea{width:95%;height:110px;background:#fff}button{background:#164c42;color:white;cursor:pointer}section{background:white;padding:24px;margin:20px 0;border-radius:12px;border:1px solid #deded4}pre{white-space:pre-wrap;overflow-wrap:anywhere}label{display:block;margin:12px 0}#status{font-weight:bold}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media(max-width:700px){.grid{display:block}}a{color:#164c42}</style>
<small>LOCAL AI ENGINEERING CASE STUDY · __MODE__</small><h1>Evidence before reassurance.</h1><p>Review a claim against its source. Adjust presentation while keeping the diagnosis, advice, and uncertainty intact.</p>
<p><strong>Research prototype.</strong> Quote validation is not proof of a correct diagnosis. Review the evidence yourself.</p>
<section><label>Passage<textarea id="passage">__PASSAGE__</textarea></label><label>Source evidence<textarea id="source">__SOURCE__</textarea></label><button id="assess" onclick="assess()">Review evidence</button><p id="status" role="status"></p></section>
<section><div class="grid"><label>Framing <select id="warmth" onchange="render()"><option value="neutral">Neutral</option><option value="warm">Warm</option></select></label><label>Order <select id="directness" onchange="render()"><option value="explanation-first">Explanation first</option><option value="action-first">Action first</option></select></label></div><div id="result">Your critique will appear here.</div><p><small>These controls use fixed framing and ordering. They do not generate new factual claims or prove that the critique is correct.</small></p></section>
<section><h2>Evidence trail</h2><details><summary>Validated record and provenance</summary><pre id="record">No assessment yet.</pre></details><p><button onclick="rate('too robotic')">Too robotic</button> <button onclick="rate('too indirect')">Too indirect</button> <button onclick="rate('this works')">This works</button></p><label>Dispute the diagnosis<input id="dispute" placeholder="What should be rechecked?" style="width:90%;padding:10px"></label><button onclick="assess(true)">Recheck evidence</button><p id="rating"></p></section>
<script>
let event=null;
const $=id=>document.getElementById(id);
async function api(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':'__TOKEN__'},body:JSON.stringify(data)});const v=await r.json();if(!r.ok)throw Error(v.error);return v;}
async function assess(recheck=false){$('assess').disabled=true;$('status').textContent='Reviewing…';try{event=await api('/assess',{passage:$('passage').value,source:$('source').value,dispute:recheck?$('dispute').value:null});$('record').textContent=JSON.stringify(event,null,2);await render();$('status').textContent='Assessment saved locally. Substantive review required.';}catch(e){$('status').textContent=e.message;}finally{$('assess').disabled=false;}}
async function render(){if(!event)return;try{const v=await api('/present',{warmth:$('warmth').value,directness:$('directness').value});$('result').replaceChildren();for(const text of [v.intro,'Verdict: '+v.verdict,v.rationale,...v.sections.map(s=>s.text+'\nSeverity: '+s.severity+' · uncertainty: '+s.uncertainty)]){let el=document.createElement('p');el.style.whiteSpace='pre-wrap';el.textContent=text;$('result').appendChild(el);}}catch(e){$('status').textContent=e.message;}}
async function rate(value){try{await api('/rate',{rating:value});$('rating').textContent='Saved locally: '+value;}catch(e){$('rating').textContent=e.message;}}
</script></html>'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    request=json.loads(Path('examples/critique-request.json').read_text())
    class Fixture:
        def generate(self,messages): return Path('examples/critique-response.json').read_text()
        def metadata(self): return {'backend':'fixture','model':None}
    engine=CritiqueEngine(MLXProvider() if args.live else Fixture())
    token=secrets.token_urlsafe(32)
    folder=Path('runs/demo')/secrets.token_hex(8);folder.mkdir(parents=True)
    state={'event':None,'input':None}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,obj):
            data=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
        def allowed_host(self):
            return self.headers.get('Host') in (f'127.0.0.1:{args.port}', f'localhost:{args.port}')
        def do_GET(self):
            if not self.allowed_host(): self.send_error(403);return
            if self.path!='/': self.send_error(404);return
            page=PAGE.replace('__TOKEN__',token).replace('__MODE__','LIVE MLX' if args.live else 'FIXTURE REPLAY — NOT A MODEL RESULT').replace('__PASSAGE__',html.escape(request['passage'])).replace('__SOURCE__',html.escape(request['sources']['demo']))
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(page.encode())
        def do_POST(self):
            if not self.allowed_host() or self.headers.get('X-Demo-Token')!=token: self.respond(403,{'error':'Invalid local session token'});return
            try:
                size=int(self.headers.get('Content-Length',0))
                if not 0<size<=32000: raise ValueError('Input exceeds demo size limit')
                data=json.loads(self.rfile.read(size))
                if self.path=='/assess':
                    inputs={'passage':data['passage'],'sources':{'demo':data['source']}}
                    if not args.live and (inputs!=request or data.get('dispute')): raise ValueError('Fixture mode only replays the supplied example. Use --live to edit or dispute.')
                    previous=None
                    if data.get('dispute'):
                        if state['event'] is None or inputs!=state['input']: raise ValueError('Recheck requires an unchanged passage/source and a previous assessment')
                        previous=from_record(state['event']['critique'])
                    event=engine.assess(**inputs,previous=previous,dispute=data.get('dispute'))
                    state.update(event=event,input=inputs)
                    result=event
                elif self.path=='/present':
                    if state['event'] is None: raise ValueError('Assess a passage first')
                    result=present(from_record(state['event']['critique']),**data)
                elif self.path=='/rate':
                    if state['event'] is None: raise ValueError('Assess a passage first')
                    if data.get('rating') not in ('too robotic','too indirect','this works'): raise ValueError('Unknown feedback')
                    result={'saved':True}
                else: self.respond(404,{'error':'Unknown action'});return
                with (folder/'events.jsonl').open('a') as f:f.write(json.dumps({'action':self.path,'request':data,'result':result})+'\n')
                self.respond(200,result)
            except (ValueError,KeyError,TypeError) as error:self.respond(400,{'error':str(error)})
    print(f'Open http://127.0.0.1:{args.port} — {"live" if args.live else "fixture"} mode. Logs: {folder}',flush=True)
    HTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

if __name__=='__main__': main()
