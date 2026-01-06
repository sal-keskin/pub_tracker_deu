from flask import Flask, render_template, request
from scopus_service import ScopusService

app = Flask(__name__)
service = ScopusService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    identifier = request.form.get('identifier')
    if not identifier:
        return render_template('index.html', error="Please provide an identifier.")

    api_key = request.form.get('api_key')

    # Collect filters
    filters = {
        "af_id": request.form.get('af_id'),
        "subj_area": request.form.get('subj_area'),
        "start_year": request.form.get('start_year'),
        "end_year": request.form.get('end_year'),
        "doctype": request.form.get('doctype')
    }

    result = service.get_publications(identifier, api_key=api_key, filters=filters)

    if "error" in result:
        return render_template('results.html', identifier=identifier, error=result['error'], source="Error")

    return render_template('results.html',
                           identifier=identifier,
                           publications=result.get('publications', []),
                           source=result.get('source', 'Unknown'),
                           query_used=result.get('query_used', ''))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
