from flask import Flask, render_template, request
from wos_service import WosService

app = Flask(__name__)
service = WosService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    identifier = request.form.get('identifier')
    if not identifier:
        return render_template('index.html', error="Please provide an identifier.")

    result = service.get_publications(identifier)

    if "error" in result:
        return render_template('results.html', identifier=identifier, error=result['error'], source="Error")

    return render_template('results.html',
                           identifier=identifier,
                           publications=result.get('publications', []),
                           source=result.get('source', 'Unknown'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
