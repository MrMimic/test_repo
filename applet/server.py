from flask import Flask, render_template, request
import json
import plotly
from plotly import graph_objs as go
import numpy as np
import pandas as pd

app = Flask(__name__)

def create_plot(args_1):

    try:
        N = int(args_1)
    except ValueError:
        N = 40

    x = np.random.uniform(low=0, high=10, size=(N, ))
    y = np.random.uniform(low=0, high=10, size=(N, ))

    df = pd.DataFrame({'x': x, 'y': y})


    data = [
        go.Scatter(
            x=df['x'],
            y=df['y'],
            mode='markers'
        )
    ]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route('/', methods=['POST'])
def updated_index():
    args_1 = request.form['user_input']
    bar = create_plot(args_1)
    return render_template('index.html', plot=bar)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
