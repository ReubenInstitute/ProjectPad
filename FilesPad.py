import os
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>ProjectPad</title>
	<script src="/script.js"></script>
</head>
<body>
<style>
	body {
		padding-top: 3em;
	}
	nav {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		background: #ffffff;
		padding: 0.5em;
		box-sizing: border-box;
	}
	.folder {
		border: 1px solid #cccccc;
		}
	.folder .content {
		padding-left: 1em;
	}
	.header::before {
		content: "📁 ";
	}
	.selected {
		background: #b3d4fc;
	}
</style>
<nav><button>Copy</button><span id="status"></span></nav>
<div id="app"></div>
<script>
	document.addEventListener('DOMContentLoaded', () => {
		const app = new App(document.getElementById('app'), document.getElementById('status'));
		document.querySelector('nav button').onclick = () => app.copy();
	});
</script>
</body>
</html>
"""


JS = """function basename(path) {
	return path.split('/').pop();
}

async function ls(path) {
	const res = await fetch('/api/ls', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ path }),
	});
	if (!res.ok) return [];
	return res.json();
}

async function read(paths) {
	const res = await fetch('/api/read', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ paths }),
	});
	if (!res.ok) return '';
	return res.text();
}

async function copyText(text) {
	if (navigator.clipboard && window.isSecureContext) {
		await navigator.clipboard.writeText(text);
		return;
	}
	const ta = document.createElement('textarea');
	ta.value = text;
	document.body.appendChild(ta);
	ta.select();
	document.execCommand('copy');
	document.body.removeChild(ta);
}

class Folder {
	constructor(path) {
		this.path = path;
		this.folders = [];
		this.files = [];
	}

	async ls() {
		const entries = await ls(this.path);
		this.folders = [];
		this.files = [];
		for (const entry of entries) {
			if (entry.endsWith('/')) {
				const name = entry.slice(0, -1);
				this.folders.push(new Folder(this.path ? this.path + '/' + name : name));
			} else {
				this.files.push(this.path ? this.path + '/' + entry : entry);
			}
		}
	}
}

class FolderView {
	constructor(folder, container, app) {
		this.folder = folder;
		this.container = container;
		this.app = app;
		this.container.className = "folder";
		if (folder.path) {
			this.header = document.createElement('div');
			this.header.className = "header";
			this.header.textContent = basename(folder.path);
			this.container.appendChild(this.header);
			this.header.onclick = () => {
				if (this.content.children.length) this.collapse();
				else this.expand();
			};
		}
		this.content = document.createElement('div');
		this.content.className = "content";
		this.container.appendChild(this.content);
	}

	async expand() {
		await this.folder.ls();
		this.content.replaceChildren();
		for (const folder of this.folder.folders) {
			const el = document.createElement('div');
			this.content.appendChild(el);
			new FolderView(folder, el, this.app);
		}
		for (const file of this.folder.files) {
			const el = document.createElement('div');
			el.textContent = basename(file);
			el.onclick = () => {
				el.classList.toggle('selected');
				this.app.toggle(file);
			};
			this.content.appendChild(el);
		}
	}

	collapse() {
		this.content.replaceChildren();
	}
}

class App {
	constructor(el, status) {
		this.selected = [];
		this.status = status;
		this.rootView = new FolderView(new Folder(''), el, this);
		this.rootView.expand();
	}

	toggle(path) {
		const i = this.selected.indexOf(path);
		if (i === -1) this.selected.push(path);
		else this.selected.splice(i, 1);
	}

	async copy() {
		if (!this.selected.length) return;
		const text = await read(this.selected);
		await copyText(text);
		this.status.textContent = new Blob([text]).size + ' bytes';
	}
}
"""


@app.route('/')
def index():
	return HTML


@app.route('/script.js')
def script():
	return Response(JS, mimetype='application/javascript')


@app.route('/api/ls', methods=['POST'])
def api_ls():
	path = request.json.get('path', '')
	if not path:
		path = '.'
	entries = []
	with os.scandir(path) as it:
		for e in it:
			entries.append(e.name + '/' if e.is_dir() else e.name)
	entries.sort(key=lambda s: (not s.endswith('/'), s))
	return jsonify(entries)


@app.route('/api/read', methods=['POST'])
def api_read():
	paths = request.json['paths']
	blocks = []
	for path in paths:
		with open(path, 'r', encoding='utf-8') as f:
			content = f.read()
		blocks.append(f"[FILE: {path}]\n[FILE_CONTENT_START]\n{content}\n[FILE_CONTENT_END: {path}]")
	return Response('\n\n'.join(blocks), mimetype='text/plain; charset=utf-8')


if __name__ == '__main__':
	app.run(debug=True)