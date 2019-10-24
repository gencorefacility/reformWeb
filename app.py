from flask import Flask, render_template, request, flash, url_for
from werkzeug.utils import redirect

from forms import SubmitJob

app = Flask(__name__)
app.secret_key = 'development key'


@app.route('/', methods=['GET', 'POST'])
def submit():
    form = SubmitJob(request.form)
    if request.method == 'POST' and form.validate():
        flash('Job Submitted')
        return redirect(url_for('submit'))
    return render_template('index.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
