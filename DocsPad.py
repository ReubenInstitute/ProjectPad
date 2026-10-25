import os
from flask import Flask, request, redirect, send_file, abort, render_template
from jinja2 import DictLoader
import markdown

app = Flask(__name__)

MD_EXTENSIONS = ['extra', 'toc']


BASE = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>DocsPad</title>
	<style>
	body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 1em; line-height: 1.6; }
	nav { margin-bottom: 1em; }
	pre { background: #f5f5f5; padding: 1em; overflow-x: auto; }
	code { background: #f5f5f5; padding: 0.1em 0.3em; }
	textarea { width: 100%; box-sizing: border-box; font-family: monospace; font-size: 1em; }
	</style>
</head>
<body>
	<nav><a href="/">Home</a></nav>
	<div class="content">
		{% block content %}{% endblock %}
	</div>
</body>
</html>"""


MAIN = """{% extends "BASE" %}
{% block content %}
{% if folders or files %}
<ul>
	{% for f in folders %}
	<li><a href="/{{ path }}{{ f }}/">{{ f }}/</a></li>
	{% endfor %}
	{% for f in files %}
	<li><a href="/{{ path }}{{ f }}">{{ f }}</a></li>
	{% endfor %}
</ul>
{% else %}
<p>(empty)</p>
{% endif %}
{% endblock %}"""


DOC = """{% extends "BASE" %}
{% block content %}
{{ html|safe }}
<hr>
<a href="/{{ path }}/edit">Edit</a>
{% endblock %}"""


EDIT = """{% extends "BASE" %}
{% block content %}
<form action="/{{ path }}/save" method="post">
	<textarea name="content" rows="30">{{ text }}</textarea>
	<br>
	<button type="submit">Save</button>
</form>
{% endblock %}"""


app.jinja_loader = DictLoader({
	'BASE': BASE,
	'MAIN': MAIN,
	'DOC': DOC,
	'EDIT': EDIT,
})


@app.route('/<path:path>/edit')
def edit(path):
	with open(path + '.md', 'r', encoding='utf-8') as f:
		text = f.read()
	return render_template('EDIT', path=path, text=text)


@app.route('/<path:path>/save', methods=['POST'])
def save(path):
	text = request.form.get('content', '').replace('\r\n', '\n')
	with open(path + '.md', 'w', encoding='utf-8') as f:
		f.write(text)
	return redirect('/' + path)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', strict_slashes=False)
def main(path):
	if path.endswith('.md') and os.path.isfile(path):
		path = path[:-3]
	if path == '' or path.endswith('/'):
		dir_path = path if path else '.'
		index = os.path.join(dir_path, 'index.md')
		if os.path.isfile(index):
			with open(index, 'r', encoding='utf-8') as f:
				text = f.read()
			html = markdown.markdown(text, extensions=MD_EXTENSIONS)
			return render_template('DOC', path=path + 'index', html=html)
		folders = []
		files = []
		for name in sorted(os.listdir(dir_path)):
			if name.startswith('.'):
				continue
			full = os.path.join(dir_path, name)
			if os.path.isdir(full):
				folders.append(name)
			elif name.endswith('.md'):
				files.append(name[:-3])
		return render_template('MAIN', path=path, folders=folders, files=files)
	md = path + '.md'
	if os.path.isfile(md):
		with open(md, 'r', encoding='utf-8') as f:
			text = f.read()
		html = markdown.markdown(text, extensions=MD_EXTENSIONS)
		return render_template('DOC', path=path, html=html)
	if os.path.isdir(path):
		return redirect('/' + path + '/')
	if os.path.isfile(path):
		return send_file(path)
	abort(404)


if __name__ == '__main__':
	app.run(debug=True)