"""A local page for ordering clips and marking which gaps to stitch."""
import argparse
import json
import os
import subprocess
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import cli, probe

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
JOBS = {}
LOCK = threading.Lock()

PAGE = """<!doctype html>
<meta charset="utf-8"><title>seamstitch</title>
<style>
 body{font:13px/1.5 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;
      margin:0;background:#14161a;color:#dfe3e8}
 header{padding:14px 20px;border-bottom:1px solid #262a31;font-weight:600}
 main{display:grid;grid-template-columns:280px 1fr 340px;gap:0;height:calc(100vh - 49px)}
 section{padding:16px;overflow:auto}
 section+section{border-left:1px solid #262a31}
 h2{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#8b93a1;
    margin:0 0 10px;font-weight:600}
 input,select,button{font:inherit;background:#1c1f25;color:#dfe3e8;
    border:1px solid #333842;border-radius:5px;padding:5px 8px}
 button{cursor:pointer}
 button:hover{background:#252a32}
 button.go{background:#2d6cdf;border-color:#2d6cdf;color:#fff;padding:7px 14px}
 button.go:hover{background:#3d7cef}
 button:disabled{opacity:.45;cursor:default}
 .row{display:flex;gap:6px;align-items:center;margin-bottom:8px}
 .file{padding:6px 8px;border:1px solid #262a31;border-radius:5px;margin-bottom:5px;
       cursor:pointer;font-size:12px}
 .file:hover{border-color:#2d6cdf}
 .file .meta{color:#7c8492;font-size:11px}
 .clip{border:1px solid #333842;border-radius:6px;padding:8px 10px;margin-bottom:6px;
       display:flex;align-items:center;gap:8px}
 .clip .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .clip .meta{color:#7c8492;font-size:11px}
 .gap{display:flex;align-items:center;gap:10px;margin:6px 0 6px 14px;color:#8b93a1}
 .gap img{height:44px;border-radius:3px;border:1px solid #333842}
 label{display:block;margin-bottom:9px;color:#8b93a1}
 label input,label select{width:100%;margin-top:3px;box-sizing:border-box}
 pre{background:#0f1114;border:1px solid #262a31;border-radius:6px;padding:12px;
     white-space:pre-wrap;font:11px/1.45 ui-monospace,Menlo,monospace;color:#c3cad4}
 .ok{color:#4ec98a}.warn{color:#e0a458}
</style>
<header>seamstitch</header>
<main>
 <section>
  <h2>Source folder</h2>
  <div class="row"><input id="dir" style="flex:1"><button onclick="scan()">Scan</button></div>
  <div id="files"></div>
 </section>
 <section>
  <h2>Sequence</h2>
  <div id="seq"></div>
 </section>
 <section>
  <h2>Settings</h2>
  <label>Output file<input id="out" value="stitched.mp4"></label>
  <label>Correction window (seconds)<input id="win" type="number" step="0.05" value="1.25"></label>
  <label>Correction share<select id="split">
    <option value="0.5">split evenly</option>
    <option value="1">change the earlier clip only</option>
    <option value="0">change the later clip only</option>
  </select></label>
  <label>Quality (crf)<input id="crf" type="number" value="18"></label>
  <div class="row" style="margin-top:14px">
   <button onclick="run(true)">Measure only</button>
   <button class="go" onclick="run(false)">Render</button>
  </div>
  <pre id="log">Pick a folder, add clips in order, then measure or render.</pre>
 </section>
</main>
<script>
let clips=[], modes=[], busy=false;
const q=s=>document.querySelector(s);
async function scan(){
  const r=await fetch('/api/scan?dir='+encodeURIComponent(q('#dir').value));
  const d=await r.json();
  if(d.error){q('#files').textContent=d.error;return}
  q('#files').innerHTML=d.files.map(f=>
    `<div class="file" onclick='add(${JSON.stringify(JSON.stringify(f))})'>${f.name}
     <div class="meta">${f.width}x${f.height} &middot; ${f.fps.toFixed(2)}fps &middot; ${f.duration.toFixed(1)}s</div></div>`).join('');
}
function add(s){clips.push(JSON.parse(s)); if(clips.length>1) modes.push('stitch'); draw()}
function del(i){clips.splice(i,1); modes.splice(Math.max(0,i-1),1); draw()}
function move(i,d){const j=i+d; if(j<0||j>=clips.length)return;
  [clips[i],clips[j]]=[clips[j],clips[i]]; draw()}
function setMode(i,v){modes[i]=v; draw()}
function draw(){
  let h='';
  clips.forEach((c,i)=>{
    if(i>0){
      const a=clips[i-1], b=c;
      h+=`<div class="gap">
        <img src="/api/frame?path=${encodeURIComponent(a.path)}&n=${a.frames-1}">
        <img src="/api/frame?path=${encodeURIComponent(b.path)}&n=0">
        <select onchange="setMode(${i-1},this.value)">
          <option value="stitch"${modes[i-1]=='stitch'?' selected':''}>stitch this join</option>
          <option value="cut"${modes[i-1]=='cut'?' selected':''}>leave as a cut</option>
        </select></div>`;
    }
    h+=`<div class="clip"><span class="name">${c.name}
        <span class="meta">${c.width}x${c.height} &middot; ${c.frames}f</span></span>
        <button onclick="move(${i},-1)">up</button>
        <button onclick="move(${i},1)">down</button>
        <button onclick="del(${i})">remove</button></div>`;
  });
  q('#seq').innerHTML=h||'<div style="color:#7c8492">No clips yet.</div>';
}
async function run(dry){
  if(busy) return;
  if(clips.length<2){q('#log').textContent='Add at least two clips.';return}
  busy=true; q('#log').textContent='Working...';
  const body={clips:clips.map(c=>c.path), junctions:modes, dry:dry,
    output:q('#out').value, dir:q('#dir').value,
    options:{window_seconds:+q('#win').value, rate_split:+q('#split').value},
    encode:{crf:+q('#crf').value}};
  const r=await fetch('/api/run',{method:'POST',body:JSON.stringify(body)});
  const {id}=await r.json();
  const poll=setInterval(async()=>{
    const s=await (await fetch('/api/job?id='+id)).json();
    q('#log').innerHTML=s.log.replace(/\\[ok\\]/g,'<span class="ok">[ok]</span>')
                            .replace(/\\[\\?\\?\\]/g,'<span class="warn">[??]</span>');
    if(!s.running){clearInterval(poll); busy=false}
  },700);
}
q('#dir').value=DEFAULT_DIR; scan();
</script>"""


def _scan(directory):
    out = []
    for name in sorted(os.listdir(directory)):
        if os.path.splitext(name)[1].lower() not in VIDEO_EXT:
            continue
        path = os.path.join(directory, name)
        try:
            info = probe.probe(path)
        except RuntimeError:
            continue
        info["name"] = name
        out.append(info)
    return out


def _frame_jpeg(path, n, width=160):
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vf",
         "select='eq(n\\,%d)',scale=%d:-2,format=yuvj420p" % (n, width),
         "-frames:v", "1", "-f", "image2", "-c:v", "mjpeg", "-"],
        capture_output=True)
    return p.stdout


def _start(body):
    with LOCK:
        jid = str(len(JOBS) + 1)
        JOBS[jid] = {"running": True, "log": ""}

    def append(text):
        with LOCK:
            JOBS[jid]["log"] += str(text) + "\n"

    def work():
        try:
            out = body.get("output") or "stitched.mp4"
            if not os.path.isabs(out):
                out = os.path.join(body.get("dir") or ".", out)
            cli.run_job(body["clips"], body["junctions"], out,
                        body.get("options", {}), body.get("encode", {}),
                        do_verify=not body.get("dry"), dry=bool(body.get("dry")),
                        log=append)
        except Exception:
            append(traceback.format_exc())
        finally:
            with LOCK:
                JOBS[jid]["running"] = False

    threading.Thread(target=work, daemon=True).start()
    return jid


class Handler(BaseHTTPRequestHandler):
    default_dir = "."

    def log_message(self, *a):
        pass

    def _send(self, code, ctype, payload):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, obj, code=200):
        self._send(code, "application/json", json.dumps(obj).encode())

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            page = PAGE.replace("DEFAULT_DIR", json.dumps(self.default_dir))
            return self._send(200, "text/html; charset=utf-8", page.encode())
        if u.path == "/api/scan":
            d = (q.get("dir") or [self.default_dir])[0]
            if not os.path.isdir(d):
                return self._json({"error": "not a folder: %s" % d})
            return self._json({"files": _scan(d)})
        if u.path == "/api/frame":
            data = _frame_jpeg(q["path"][0], int(q.get("n", ["0"])[0]))
            return self._send(200, "image/jpeg", data)
        if u.path == "/api/job":
            with LOCK:
                return self._json(JOBS.get(q["id"][0], {"running": False, "log": "no such job"}))
        self._send(404, "text/plain", b"not found")

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            return self._send(404, "text/plain", b"not found")
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        self._json({"id": _start(body)})


def main(argv=None):
    ap = argparse.ArgumentParser(prog="seamstitch.ui")
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    Handler.default_dir = os.path.abspath(args.dir)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("seamstitch ui on http://127.0.0.1:%d  (folder: %s)"
          % (args.port, Handler.default_dir))
    srv.serve_forever()


if __name__ == "__main__":
    main()
